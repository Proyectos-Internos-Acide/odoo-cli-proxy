# Configuracion del Restaurante - Guia Completa

## Resumen

El restaurante opera como un POS con modo restaurante habilitado en Odoo 19 (saas-19.1).
Soporta Dine In, Takeout y Delivery con self-ordering mobile (ES/EN).

## Configuracion Automatizada (Scripts)

### 1. POS Categories + Preparation Display

```bash
uv run python business_units/hotel-trip-agency/restaurant/setup_pos.py
```

Crea/verifica:
- Categorias POS: Bebidas, Desayuno, Platos de fondo, Hamburguesas, Sandwiches, Salchipapas
- Display de preparacion "Despacho restaurante" con 3 etapas (To prepare, Ready, Completed)
- Traducciones EN de categorias (para self-ordering)

### 2. Productos Default

```bash
uv run python business_units/hotel-trip-agency/restaurant/setup_products.py
```

Crea/verifica:
- Productos default (bebidas: Agua, Gaseosa) con i18n ES/EN
- Asignacion de `pos_categ_ids` y `available_in_pos`
- Lista todos los productos disponibles en POS

## Configuracion Manual (UI)

### 1. Crear POS Config "Restaurante"

1. Ir a **Punto de Venta > Configuracion > Punto de Venta**
2. Crear nuevo con nombre "Restaurante"
3. Habilitar:
   - **Es un Bar/Restaurante** (module_pos_restaurant)
   - **Dividir Cuenta** (iface_splitbill)
   - **Imprimir Cuenta** (iface_printbill)
   - **Control de Caja** (cash_control)
   - **Impuestos incluidos** en el precio (iface_tax_included = total)

### 2. Configurar Presets (Modalidades de Servicio)

En la config del POS Restaurante:
1. Habilitar **Usar Presets** (use_presets)
2. Crear 3 presets:
   - **Dine In** — color: 4, identificacion: ninguna (default)
   - **Takeout** — color: 3, identificacion: nombre del cliente
   - **Delivery** — color: 2, identificacion: direccion

### 3. Configurar Pisos y Mesas

En la config del POS Restaurante, seccion **Pisos y Mesas**:

#### Primer Piso (12 mesas, 48 asientos)

| Mesa | Asientos | Color | Uso |
|------|----------|-------|-----|
| 1-2 | 4 c/u | Verde | Mesas regulares |
| 3 | 4 | Verde | Mesa grande (165x100) |
| 4-5 | 4 c/u | Verde | Mesas regulares |
| 6 | 4 | Verde | Mesa grande (165x100) |
| 7-8 | 4 c/u | Rojo | Mesas regulares |
| 9 | 6 | Rojo | Mesa grande (165x100) |
| 10 | 6 | Rojo | Mesa regular |
| 11 | 2 | Morado | Mesa pequena |
| 12 | 2 | Morado | Mesa grande (165x100) |

#### Patio (12 mesas, 32 asientos)

| Mesa | Asientos | Color | Uso |
|------|----------|-------|-----|
| 101-108 | 2 c/u | Verde | Mesas exteriores (130x85) |
| 109-112 | 4 c/u | Amarillo | Mesas exteriores grandes (130x120) |

**Nota Odoo 19**: Las mesas usan `table_number` (entero) en vez de `name`. La forma, color y posicion se almacenan en el campo JSON `floor_plan_layout`.

### 4. Metodos de Pago

Configurar en el POS Restaurante:
- **Efectivo del restaurante** — tipo: cash, journal dedicado, cash count activo
- **Tarjeta** — tipo: bank, journal bancario
- **Cuenta de cliente** — tipo: pay_later (para fiados/cuentas abiertas)

### 5. Self-Ordering Mobile

En la config del POS Restaurante:
1. **Modo**: Mobile
2. **Pagar despues de**: Cada orden (each)
3. **Modo de servicio**: Counter
4. **Idioma por defecto**: Espanol (Latin America)
5. **Idiomas disponibles**: Espanol, Ingles
6. URL generada automaticamente: `https://<instance>.odoo.com/pos-self/<config_id>?access_token=<token>`

### 6. Preparation Display

1. Ir a **Punto de Venta > Ordenes > Pantalla de Preparacion**
2. El script crea "Despacho restaurante" con 3 etapas:
   - **To prepare** (gris, alerta 10 min)
   - **Ready** (azul, alerta 5 min)
   - **Completed** (verde, sin alerta)
3. Vincular el display al POS Restaurante manualmente desde la UI

## Categorias de Producto

| Categoria | Tipo | ID |
|-----------|------|----|
| Restaurante | product.category | 4 |
| Bebidas | pos.category | (auto) |
| Desayuno | pos.category | (auto) |
| Platos de fondo | pos.category | (auto) |
| Hamburguesas | pos.category | (auto) |
| Sandwiches | pos.category | (auto) |
| Salchipapas | pos.category | (auto) |

## Modulos Requeridos

Modulos POS/Restaurant que deben estar instalados:
- `point_of_sale` — POS base
- `pos_restaurant` — Modo restaurante (pisos, mesas, split bill)
- `pos_self_order` — Self-ordering mobile
- `pos_restaurant_preparation_display` — Display de preparacion
- `l10n_pe_edi_pos` — Localizacion Peru para POS

## Notas Tecnicas - Odoo 19

### Modelos renombrados
- `restaurant.printer` → **`pos.printer`**
- `pos.preparation.display` → **`pos.prep.display`**
- Stages: `pos.prep.stage`, Lines: `pos.prep.line`

### Campos especificos
- `restaurant.table`: sin campo `name`, usa `table_number` (integer)
- `restaurant.table.floor_plan_layout`: JSON con `{top, left, color, shape, width, height, uuid}`
- `restaurant.floor.floor_plan_layout`: JSON con `{bgColor}` (ej: "texture-wood-v")
- `pos.order`: sin `floor_id`, solo `table_id` (many2one a restaurant.table)
- `pos.config.available_preset_ids`: many2many a `pos.preset`

### Impuestos
- IGV 18% (id=5) aplicado a productos de venta
- City Tax: S/2.10 fijo por unidad
- Posiciones fiscales: LOCAL PERU (auto), FOREIGN-EXPORT (auto)
