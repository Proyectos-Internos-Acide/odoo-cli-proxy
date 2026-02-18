# Guia de Replicacion — Agencia de Viajes en Odoo 19 SaaS

Documento de referencia con hallazgos tecnicos, configuraciones genericas y patrones
reutilizables para implementar agencias de viajes diferentes sobre Odoo 19 SaaS via XML-RPC.

> **Prerequisito**: leer `AGENCY_SETUP_GUIDE.md` para el detalle de scripts y campos custom.
> Este documento cubre los **patrones genericos** y **hallazgos criticos** descubiertos
> durante la implementacion de A&F Destiny.

---

## 1. Arquitectura General

```
WordPress/Web ──scrape──▶ tours.json ──translate──▶ tours.json (bilingue)
                                           │
                                           ▼
                               upload_tours_to_odoo.py
                                           │
                            ┌──────────────┼──────────────┐
                            ▼              ▼              ▼
                     product.template   QWeb views    Traducciones
                    (description_ecommerce,  (website)   (update_field_
                     x_extended_description)              translations)
```

### Modulos Odoo requeridos

| Modulo | Uso |
|--------|-----|
| `sale_management` | Cotizaciones y plantillas |
| `sale_project` | Crea proyectos/tareas al confirmar SO |
| `purchase` | Ordenes de compra a proveedores |
| `fleet` | Vehiculos propios |
| `crm` | Pipeline de leads (formulario web) |
| `website_sale` | Tienda web / ecommerce |
| `website_crm` | Formularios web que crean leads |
| `project` | Gestion de proyectos operativos |
| `planning` | Planificacion de recursos |

---

## 2. Hallazgos Criticos — Odoo 19 SaaS

### 2.1 Traducciones en campos `html_translate`

**Problema**: `write()` con `context={'lang': 'es_419'}` en campos `html_translate`
**NO crea traducciones** correctamente cuando el HTML en ingles y espanol tienen
contenido diferente. Odoo intenta matchear segmentos del HTML nuevo contra el HTML base
y, al no encontrar coincidencias, **sobreescribe el contenido base**.

**Solucion**: Usar el patron de 3 pasos:

```python
# Paso 1: Escribir contenido EN como base
client.execute('product.template', 'write', [pid], {
    'description_ecommerce': short_en,
    'x_extended_description': extended_en,
}, context={'lang': 'en_US'})

# Paso 2: Obtener los terminos fuente que Odoo extrajo del HTML
result = client.execute('product.template', 'get_field_translations',
                        [pid], 'description_ecommerce', ['es_419'])
source_terms = [t['source'] for t in result[0] if isinstance(t, dict)]
# Ejemplo de source_terms:
# ['Discover the itinerary we have for you.',
#  '<strong>Departures:</strong> Monday to Sunday, 06:30 am',
#  '<strong>Difficulty:</strong> Moderate']

# Paso 3: Construir mapeo {en_term: es_term} y aplicar
mapping = {
    'Discover the itinerary...': 'Conoce el itinerario...',
    '<strong>Departures:</strong> Monday to Sunday, 06:30 am': '<strong>Salidas:</strong> Lunes a Domingo 06:30 am',
    '<strong>Difficulty:</strong> Moderate': '<strong>Dificultad:</strong> Moderado',
}
client.execute('product.template', 'update_field_translations',
               [pid], 'description_ecommerce', {'es_419': mapping})
```

**Notas clave**:
- `get_field_translations` recibe `langs` como **lista**: `['es_419']`, no string
- Los terminos fuente incluyen tags inline: `<strong>Salidas:</strong> texto`
- Los tags de bloque (`<p>`, `<h3>`, `<ul>`, `<li>`) NO forman parte del termino
- Ambos HTML (EN y ES) deben tener la **misma estructura** (mismo numero de `<p>`, `<li>`, etc.)
  para que el mapeo posicional funcione

### 2.2 Traducciones en vistas QWeb (`translate=xml`)

`write()` con `context={'lang': ...}` **NO funciona** para campos `arch_db` de `ir.ui.view`.

```python
# INCORRECTO — no crea traducciones
client.execute('ir.ui.view', 'write', [view_id],
               {'arch': arch_es}, context={'lang': 'es_419'})

# CORRECTO
client.execute('ir.ui.view', 'update_field_translations',
               [view_id], 'arch_db',
               {'es_419': {'Request a Quote': 'Solicitar Cotizacion'}})
```

Para descubrir los terminos fuente exactos (incluyendo HTML inline):
```python
result = client.execute('ir.ui.view', 'get_field_translations',
                        [view_id], 'arch_db', ['es_419'])
for term in result[0]:
    print(term['source'], '→', term['value'])
```

### 2.3 Idioma base y contexto XML-RPC

- **Idioma base**: siempre `en_US` en Odoo 19 SaaS
- XML-RPC sin contexto opera en **ingles** (base), no en el idioma del usuario
- `es_ES` NO esta instalado — usar solo `es_419` (Spanish Latin America)
- `write` con `context={'lang': 'en_US'}` = write sin contexto = escribe en columna base
- `create` en Odoo 19 retorna **lista** — extraer con `result[0] if isinstance(result, list) else result`

### 2.4 Restricciones de `safe_eval` en SaaS

- `import` = opcode prohibido → no se puede importar nada en codigo de automatizaciones
- `Markup` NO esta disponible → usar texto plano en `message_post` (Odoo lo envuelve via `plaintext2html`)
- `datetime`, `time`, `json` SI estan disponibles via entorno safe_eval

### 2.5 Bug critico: Fix Slot Times

La automatizacion "Fix Slot Times" (base.automation id=2) crashea al confirmar SO cuando
planning slots tienen `start_datetime=False`. **Debe parchearse en cada instancia nueva.**

```python
# hotel/fix_slot_times_automation.py — agregar al inicio del codigo:
# if not record.start_datetime or not record.end_datetime: continue
```

---

## 3. Patron: Campo Descripcion Extendida (Ecommerce)

### Problema
El campo `description_ecommerce` nativo de Odoo aparece junto a la imagen del producto.
Para tours, se necesita informacion detallada (itinerario, incluye, no incluye, precios)
que no cabe en ese espacio.

### Solucion: campo custom + QWeb view

#### 3.1 Crear campo `x_extended_description`

```python
# Buscar id del modelo
model = client.search_read('ir.model',
    domain=[['model', '=', 'product.template']],
    fields=['id'], limit=1)

# Crear campo html traducible
client.execute('ir.model.fields', 'create', [{
    'model_id': model[0]['id'],
    'name': 'x_extended_description',
    'field_description': 'Extended Description',
    'ttype': 'html',
    'copied': True,
}])

# Hacer traducible
field = client.search_read('ir.model.fields',
    domain=[['model', '=', 'product.template'],
            ['name', '=', 'x_extended_description']],
    fields=['id', 'translate'])
if not field[0]['translate']:
    client.execute('ir.model.fields', 'write', [field[0]['id']],
                    {'translate': True})
# translate=True en html → Odoo lo convierte a html_translate automaticamente
```

#### 3.2 QWeb view (sitio web)

Renderiza el campo debajo de la seccion del producto, arriba de especificaciones:

```xml
<data>
    <xpath expr="//section[@id='product_detail']" position="after">
        <section t-if="(CONDICION_TOUR) and product.x_extended_description"
                 class="container py-4" id="tour_extended_description">
            <div t-field="product.x_extended_description"
                 class="o_wsale_extended_description"/>
        </section>
    </xpath>
</data>
```

Creacion via XML-RPC:
```python
parent_id = client.search_read('ir.ui.view',
    domain=[['key', '=', 'website_sale.product']],
    fields=['id'], limit=1)[0]['id']

client.execute('ir.ui.view', 'create', [{
    'name': 'agency_ecommerce.extended_description_tour',
    'key': 'agency_ecommerce.extended_description_tour',
    'inherit_id': parent_id,
    'type': 'qweb',
    'arch': ARCH_XML,
    'priority': 99,
}], context={'lang': 'en_US'})
```

#### 3.3 Backend form view (pestaña ecommerce)

```xml
<data>
    <xpath expr="//group[@name='ecom_description']" position="after">
        <group string="Extended Description" name="ecom_extended_description">
            <field colspan="2" name="x_extended_description" nolabel="1"
                   placeholder="Detailed content (itinerary, includes, conditions...)"/>
        </group>
    </xpath>
</data>
```

**CUIDADO**: El form view `product.template.product.website.form` (id=3525) tiene DOS
campos `description_ecommerce` — uno oculto en el grupo `upsell`. Usar siempre
`//group[@name='ecom_description']` como xpath selector, no `//field[@name='description_ecommerce']`.

---

## 4. Patron: Deteccion de Tours en QWeb

Para que las vistas QWeb apliquen solo a productos de tour, usar una condicion compuesta:

```python
# Deteccion por categoria interna O por categoria publica (incluyendo padres)
_IS_TOUR = (
    "product.categ_id.name == 'Tours y Paquetes turísticos'"
    " or product.public_categ_ids.filtered("
    "lambda c: c.name == 'Tours' or c.parent_id.name == 'Tours')"
)
_NOT_TOUR = "not (" + _IS_TOUR + ")"
```

Uso en QWeb:
```xml
<section t-if="product.categ_id.name == 'Tours y Paquetes turísticos'
               or product.public_categ_ids.filtered(
                   lambda c: c.name == 'Tours' or c.parent_id.name == 'Tours')"
         ...>
```

**Nota**: Cada contexto de ecommerce (pagina de producto, listado, wishlist, snippet dinamico)
usa un template QWeb **diferente**. No se puede depender de una sola vista heredada
para cambiar precios o botones en todos los contextos.

---

## 5. Patron: Pipeline de Contenido Bilingue

### 5.1 Estructura del JSON

Cada tour tiene campos base (espanol) y campos `_en` (ingles):

```json
{
    "slug": "city-tour-cusco",
    "title": "City Tour Cusco",
    "description": "Conoce la magica ciudad...",
    "description_en": "Discover the magical city...",
    "itinerary": "9:00 a 9:30 am recojo en su hotel...",
    "itinerary_en": "9:00 to 9:30 am pickup at your hotel...",
    "includes": ["Guia profesional", "Recojo en el hotel"],
    "includes_en": ["Professional guide", "Hotel pickup"],
    "excludes": [...],
    "excludes_en": [...],
    "recommendations": [...],
    "recommendations_en": [...],
    "schedule": "Lunes a Domingo 09:00 hrs",
    "schedule_en": "Monday to Sunday, 09:00 hrs",
    "conditions": "...",
    "conditions_en": "...",
    "booking": "...",
    "booking_en": "...",
    "prices": "...",
    "prices_en": "...",
    "difficulty": "Moderado",
    "difficulty_en": "Moderate"
}
```

### 5.2 Builders HTML (espanol + ingles)

Cada builder produce HTML con headers en el idioma correspondiente:

```python
def build_short_description_html(tour: dict) -> str:
    """ES: intro corta (~350 chars) + Salidas + Dificultad"""
    parts = []
    desc = tour.get("description", "").strip()
    if desc:
        intro = _extract_intro(desc)  # max 350 chars, corta en oracion
        parts.append(f"<p>{escape(intro)}</p>")
    schedule = tour.get("schedule", "").strip()
    if schedule:
        parts.append(f"<p><strong>Salidas:</strong> {escape(schedule)}</p>")
    difficulty = tour.get("difficulty", "").strip()
    if difficulty:
        parts.append(f"<p><strong>Dificultad:</strong> {escape(difficulty)}</p>")
    return "\n".join(parts)

def build_short_description_html_en(tour: dict) -> str:
    """EN: usa *_en keys con fallback a espanol"""
    parts = []
    desc = tour.get("description_en", tour.get("description", "")).strip()
    # ... same structure but English headers
    parts.append(f"<p><strong>Departures:</strong> {escape(schedule)}</p>")
    parts.append(f"<p><strong>Difficulty:</strong> {escape(difficulty)}</p>")
```

**Regla critica**: Ambos builders deben producir HTML con **la misma estructura**
(mismo numero de `<p>`, `<h3>`, `<ul>`, `<li>`) para que el mapeo de traducciones funcione.

### 5.3 Itinerarios multi-dia vs dia unico

```python
# Deteccion de multi-dia
_DAY_RE = re.compile(
    r'^(?:D[ií]a|DIA|Day)\s*0?(\d+)\s*[:.\-–—]\s*(.*)',
    re.IGNORECASE,
)
is_multiday = bool(_DAY_RE.search(itinerary))

# Multi-dia: <h4>Day N: Title</h4> + <ul><li>steps</li></ul>
# Dia unico: <ul><li>steps</li></ul> (split por tiempo/transicion)
```

Patrones de split para itinerarios de un dia:
```python
_SPLIT_RE = re.compile(
    r'(?<=[.!])\s*(?='
    r'(?:\d{1,2}[:.]\d{2})'          # marcadores de tiempo (9:00, 08.30)
    r'|(?:[Ll]uego\b)'               # "luego"
    r'|(?:[Dd]espu[eé]s\b)'          # "después"
    r'|(?:[Pp]osteriormente\b)'       # "posteriormente"
    r'|(?:[Ff]inalmente\b)'          # "finalmente"
    r'|(?:[Aa]l\s+(?:llegar|terminar)\b)'  # "al llegar/terminar"
    r')',
)
```

### 5.4 Flujo de migracion completo

```
1. scrape_wordpress_tours.py    → generated/wordpress_tours.json (28 tours, ES)
2. translate_tours_json.py      → agrega *_en fields al JSON
3. upload_tours_to_odoo.py      → crea/actualiza product.template en Odoo
4. setup_extended_description.py:
   a. Crea campo x_extended_description (html, traducible)
   b. Crea QWeb view (sitio web) + backend form view
   c. Migra datos: EN base → get_field_translations → update_field_translations(es_419)
```

---

## 6. Patron: Traducciones de Items Comunes

Para listas (incluye, no incluye, recomendaciones), usar diccionarios de traduccion
compartidos. Muchos items se repiten entre tours:

```python
INCLUDES_EN = {
    "Guía español / inglés": "Spanish / English guide",
    "Recojo en el hotel": "Hotel pickup",
    "Transporte turístico": "Tourist transportation",
    "Almuerzo Buffet": "Buffet lunch",
    "Boleto de ingreso a Machu Picchu.": "Machu Picchu entrance ticket.",
    # ... 100+ items
}

def translate_item(item: str, dictionary: dict) -> str:
    return dictionary.get(item, item)  # fallback al original

tour['includes_en'] = [translate_item(i, INCLUDES_EN) for i in tour['includes']]
```

**Tip**: Las comillas tipograficas (`"..."` vs `"..."`) causan fallos de match.
Agregar ambas variantes al diccionario.

---

## 7. Patron: Ecommerce — Boton "Solicitar Cotizacion"

### Problema
Los tours no se venden directamente. El boton "Agregar al carrito" debe reemplazarse
por un formulario que crea un lead en CRM.

### Solucion: 5 vistas QWeb + 4 price prefix

| Vista | Hereda de | Efecto |
|-------|-----------|--------|
| `cta_tour_quote` | `website_sale.cta_wrapper` | Reemplaza add-to-cart → "Solicitar Cotizacion" |
| `product_tour_modal` | `website_sale.product` | Modal con `s_website_form` → `crm.lead` |
| `listing_tour_quote` | `website_sale.shop_product_buttons` | Card del listado: "Cotizar" → link a producto |
| `wishlist_tour_quote` | `website_sale_wishlist.product_wishlist` | Wishlist: oculta cart, muestra "Cotizar" |
| `dynamic_snippet_tour_quote` | dynamic filter template | Snippet dinamico: oculta cart |
| `price_prefix_tour` | `website_sale.product_price` | Prefijo "aprox." en pagina de producto |
| `price_prefix_listing` | `website_sale.products_item` | Prefijo "aprox." en cards del listado |
| `price_prefix_wishlist` | wishlist template | Prefijo "aprox." en wishlist |
| `price_prefix_dynamic` | dynamic price template | Prefijo "aprox." en snippets |

**IMPORTANTE**: `data-success-mode="message"` rompe `s_website_form` en Odoo 19 SaaS
(el formulario no renderiza). Usar `data-success-mode="redirect"` y detectar el parametro
en la URL para mostrar un overlay de exito via CSS.

### Lead creado en CRM

El formulario web crea un `crm.lead` con:
- `name`: "Cotizacion Web: [Nombre del Tour]"
- `contact_name`: nombre del visitante
- `email_from`: email del visitante
- `phone`: telefono (opcional)
- `description`: texto libre del visitante

---

## 8. Patron: Biblia Operativa

Documento operativo interno con toda la informacion del tour. Se adjunta como tab
en la orden de venta y se puede imprimir como PDF.

### Modelos custom

| Modelo | Campos clave | Uso |
|--------|-------------|-----|
| `x_itinerary_line` | day_number, title, description, accommodation, meals | Itinerario dia a dia |
| `x_operator_line` | partner_id, service_type, cost, purchase_order_id | Proveedores asignados |

### Flujo

```
Plantilla SO (x_is_tour=True)
    ├── Itinerario predefinido
    ├── Operadores por defecto
    └── Inclusions, key_times, observations
         │
         │ Automatizacion: on_create_or_write
         ▼
Cotizacion (sale.order)
    ├── Itinerario copiado (editable)
    ├── Operadores (editables + boton "Generar POs")
    ├── Pasajeros (x_guest_line_ids, datos readonly desde res.partner)
    └── Boton Imprimir → PDF Biblia Operativa / Voucher Pasajero
```

### Generacion de POs desde operadores

```python
# Server action: agrupa operadores sin PO por proveedor
# Crea un PO por proveedor con producto "Servicio de Tour" (SRV-TOUR)
# Precio = x_cost del operador
# Vincula via sale_order_id (campo nativo de sale_purchase)
```

---

## 9. Patron: Creacion de Campos Custom via XML-RPC

Odoo 19 SaaS permite crear campos `x_` via `ir.model.fields`, equivalente a Odoo Studio.

```python
# Buscar model_id
model = client.search_read('ir.model',
    domain=[['model', '=', 'sale.order']],
    fields=['id'], limit=1)

# Crear campo
result = client.execute('ir.model.fields', 'create', [{
    'model_id': model[0]['id'],
    'name': 'x_my_field',
    'field_description': 'My Field',
    'ttype': 'char',  # char, text, html, boolean, integer, float, date, datetime
                       # many2one, one2many, many2many, selection
    'copied': True,    # se copia al duplicar registro
}])

# Para selection fields:
'selection_ids': [
    (0, 0, {'value': 'option1', 'name': 'Option 1', 'sequence': 1}),
    (0, 0, {'value': 'option2', 'name': 'Option 2', 'sequence': 2}),
]

# Para many2one:
'relation': 'res.partner'

# Para one2many:
'relation': 'x_my_child_model'
'relation_field': 'x_parent_id'

# Para related fields con selection source, usar ttype='selection' (NO char)
```

### Modelos custom completos

```python
# Crear modelo
model_result = client.execute('ir.model', 'create', [{
    'name': 'My Custom Model',
    'model': 'x_my_model',
    'state': 'manual',  # OBLIGATORIO para custom models
}])

# ACL — CRUD para todos los usuarios
client.execute('ir.model.access', 'create', [{
    'name': 'x_my_model access',
    'model_id': model_result[0],
    'group_id': 1,  # base.group_user (todos los empleados)
    'perm_read': True,
    'perm_write': True,
    'perm_create': True,
    'perm_unlink': True,
}])
```

---

## 10. Patron: Vistas Heredadas via XML-RPC

### QWeb (website)

```python
parent = client.search_read('ir.ui.view',
    domain=[['key', '=', 'website_sale.product']],
    fields=['id'], limit=1)

client.execute('ir.ui.view', 'create', [{
    'name': 'my_view_name',
    'key': 'my_view_name',        # OBLIGATORIO para QWeb
    'inherit_id': parent[0]['id'],
    'type': 'qweb',
    'arch': '<data>...</data>',
    'priority': 99,
}], context={'lang': 'en_US'})
```

### Backend form

```python
# Buscar vista padre dinamicamente (no hardcodear IDs)
parents = client.search_read('ir.ui.view',
    domain=[
        ['model', '=', 'sale.order'],
        ['type', '=', 'form'],
        ['arch_db', 'ilike', 'campo_unico_de_la_vista'],
    ],
    fields=['id', 'name'],
    order='priority asc',
    limit=1)

client.execute('ir.ui.view', 'create', [{
    'name': 'my.form.inherit',
    'model': 'sale.order',
    'inherit_id': parents[0]['id'],
    'type': 'form',
    'arch': '<data><xpath expr="..." position="after">...</xpath></data>',
    'priority': 99,
}])
```

### XPath: errores comunes

| Problema | Solucion |
|----------|----------|
| `aria-label` como selector | No permitido. Usar `hasclass()`, `@name`, `@id` |
| Match en campo oculto (invisible="1") | Usar `//group[@name='...']` en vez de `//field[@name='...']` |
| Multiples matches | Agregar mas contexto al xpath: `//page[@name='x']//field[@name='y']` |

---

## 11. Checklist: Nueva Agencia de Viajes

### Pre-requisitos

- [ ] Instancia Odoo 19 SaaS configurada
- [ ] Modulos instalados (seccion 1)
- [ ] Booking engine con campos `x_guests`, `x_guest_line_ids`, `x_nationality`, `x_document_type`, `x_document_number`
- [ ] Archivo `.env` con credenciales
- [ ] Python 3.13+ con `uv`

### Setup base (1 vez por instancia)

- [ ] Parchar bug Fix Slot Times (`hotel/fix_slot_times_automation.py`)
- [ ] Campos custom en contactos y SO (`setup_custom_fields.py`)
- [ ] Plantilla de proyecto con etapas kanban (`setup_projects.py`)
- [ ] Automatizaciones de flota (`setup_fleet_automations.py`)
- [ ] Biblia Operativa con modelos y PDF (`setup_biblia_operativa.py`)
- [ ] Formulario de contacto extendido (`setup_partner_form.py`)
- [ ] Vistas ecommerce (`setup_ecommerce.py`)
- [ ] Grupos de tour (`setup_tour_groups.py`)

### Contenido de tours (por agencia)

- [ ] Scrapear/recopilar tours del sitio web actual → `tours.json`
- [ ] Traducir JSON: agregar campos `*_en` → `translate_tours_json.py`
- [ ] Subir productos a Odoo → `upload_tours_to_odoo.py`
- [ ] Crear campo extendido + vistas + migrar traducciones → `setup_extended_description.py`
- [ ] Crear plantillas de cotizacion → `create_tour_templates.py`

### Verificacion

- [ ] Sitio web: tours muestran "Solicitar Cotizacion" (no "Agregar al carrito")
- [ ] Sitio web: precio con prefijo "aprox." / "estimated"
- [ ] Sitio web: formulario crea lead en CRM
- [ ] Sitio web: descripcion corta al lado de imagen, extendida debajo
- [ ] Sitio web: cambiar idioma muestra contenido EN/ES correctamente
- [ ] Backend: pestaña ecommerce muestra ambos campos (Descripcion Larga + Extended)
- [ ] Backend: Biblia Operativa funciona en cotizaciones
- [ ] Backend: confirmar SO crea proyecto con tareas

---

## 12. Adaptacion para Otra Agencia

Para replicar en una agencia diferente (distinto destino, idiomas, estructura):

### Cambios necesarios

1. **`defaults/categories.py`**: Ajustar IDs de categorias (varian por instancia)
2. **`defaults/views.py`**: Ajustar `_IS_TOUR` / `_NOT_TOUR` si la categoria de tours se llama diferente
3. **`translate_tours_json.py`**: Nuevos diccionarios de traduccion (items especificos del destino)
4. **Builders HTML**: Ajustar headers si se usan otros idiomas (ej: portugues, frances)
5. **`setup_custom_fields.py`**: Agregar/quitar campos segun necesidad operativa
6. **Automatizaciones**: Ajustar logica de conflictos de flota si la operacion es diferente

### Lo que NO cambia (reutilizable tal cual)

- Patron de campo `x_extended_description` + QWeb + form view
- Patron de `update_field_translations` para html_translate
- Patron de Biblia Operativa (itinerario + operadores + POs)
- Patron de ecommerce (CTA → CRM lead)
- Pipeline JSON → builders → upload → migrate
- Helpers de i18n (`write_translations`, `search_translatable`)
- Deteccion dinamica de vistas padre (sin IDs hardcodeados)

---

## 13. Referencia Rapida: APIs XML-RPC

### Traducciones

```python
# Leer terminos fuente de un campo traducible
client.execute(model, 'get_field_translations', [ids], field_name, ['es_419'])
# → [[{'lang': 'es_419', 'source': '...', 'value': '...'}, ...], {metadata}]

# Aplicar traducciones
client.execute(model, 'update_field_translations', [ids], field_name,
               {'es_419': {'source_en': 'traduccion_es', ...}})
```

### Campos

```python
# Verificar si campo existe
client.search_read('ir.model.fields',
    domain=[['model', '=', 'product.template'],
            ['name', '=', 'x_my_field']],
    fields=['id', 'ttype', 'translate'])

# Hacer campo traducible
client.execute('ir.model.fields', 'write', [field_id], {'translate': True})
```

### Vistas

```python
# Buscar vista por key (QWeb)
client.search_read('ir.ui.view',
    domain=[['key', '=', 'website_sale.product']],
    fields=['id', 'name'])

# Buscar vista por contenido (backend)
client.search_read('ir.ui.view',
    domain=[['model', '=', 'product.template'],
            ['type', '=', 'form'],
            ['arch_db', 'ilike', 'texto_unico']],
    fields=['id', 'name'],
    order='priority asc', limit=1)
```

---

## 14. Errores Comunes y Soluciones

| Error | Causa | Solucion |
|-------|-------|----------|
| `Invalid language code: e` | `get_field_translations` recibe string en vez de lista | Pasar `['es_419']` no `'es_419'` |
| Campo no aparece en form | xpath matcheo campo invisible | Usar `//group[@name='...']` |
| Traduccion no se guarda | `write` con lang context en html_translate | Usar `update_field_translations` |
| `data-success-mode="message"` rompe form | Bug Odoo 19 SaaS | Usar `"redirect"` + CSS overlay |
| `import` en automatizacion | safe_eval bloquea imports | Usar solo builtins disponibles |
| `Markup` no existe | No disponible en safe_eval | Usar texto plano en `message_post` |
| `on_state_set` no tiene tareas | Tasks se crean DESPUES del trigger | Usar `on_create` en `project.task` |
| Conflicto flota con SO cancelado | Domain no filtra por estado | Agregar `("sale_order_id.state", "=", "sale")` |
| `column_invisible` no funciona | Sintaxis incorrecta | Usar `column_invisible="not parent.x_field"` |
| Related field selection como char | ttype incorrecto | Usar `ttype='selection'` para related de selection |
| `complete_name` en menu search | Campo no stored en Odoo 19 | Buscar por `name` + `parent_id` chain |
