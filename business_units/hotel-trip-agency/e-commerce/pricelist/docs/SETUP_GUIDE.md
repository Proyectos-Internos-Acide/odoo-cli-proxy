# Pricelist Currency Setup — Precios por Idioma

## Resumen

El ecommerce muestra precios en la moneda correspondiente al idioma del visitante:

| Idioma   | Moneda | Pricelist        |
|----------|--------|------------------|
| Español  | PEN (S/) | Predeterminado (id=1) |
| English  | USD ($)  | USD minorista (id=2)  |

## Arquitectura

```
Visitante abre /en/shop
        │
        ▼
QWeb view (website.layout)
  ├── <script> lee document.documentElement.lang
  ├── Compara con sessionStorage('pl_last_lang')
  ├── Si cambió idioma → redirect a /shop/change_pricelist/<id>
  └── Si mismo idioma → no hace nada (sin recarga extra)
        │
        ▼
Odoo cambia session pricelist → precios en USD
```

### Componentes

1. **Pricelists** (`product.pricelist`)
   - PEN (id=1): moneda empresa, `selectable=True`
   - USD (id=2): `selectable=True`, con regla global de conversion

2. **Regla global de conversion** (`product.pricelist.item`)
   - `applied_on=3_global`, `compute_price=formula`, `base=list_price`
   - Odoo convierte automaticamente PEN→USD usando `res.currency.rate`
   - Precios manuales por producto (fixed_price) tienen prioridad sobre la regla global

3. **Country groups** (`res.country.group`) — fallback GeoIP
   - LATAM (20 paises) → PEN pricelist
   - International (todos los paises) → USD pricelist
   - **Critico**: ambas pricelists DEBEN tener country groups. Si alguna no tiene, Odoo la excluye del GeoIP matching

4. **QWeb view** (`agency_ecommerce.pricelist_lang_switch`)
   - Hereda `website.layout`, inyecta `<script>` en `<head>`
   - JavaScript sincroniza idioma → pricelist al cargar la pagina
   - Arch definido en `agency/defaults/views.py` → `ECOM_PRICELIST_LANG_SWITCH_ARCH`

## Como funciona la conversion de precios

### Producto CON precio manual en USD
Se configura un `product.pricelist.item` con `applied_on=1_product` (o `0_product_variant`),
`compute_price=fixed`, y `fixed_price=XX`. Odoo usa este precio directamente.

Ejemplo: City Tour Cusco → $25 USD (manual)

### Producto SIN precio manual
La regla global (`3_global`, `formula`, `base=list_price`) toma el `list_price` del producto
(en PEN, moneda de la empresa) y lo convierte usando el tipo de cambio del dia (`res.currency.rate`).

Ejemplo: Tour con list_price=3700 PEN → 3700 * 0.2974 ≈ $1,100 USD (automatico)

### Tipo de cambio
- `res.currency.rate` para USD: ~0.2974 (1 PEN = 0.2974 USD)
- Se actualiza manualmente en Contabilidad > Configuracion > Monedas, o automaticamente si esta habilitado el servicio de tipo de cambio

## Ejecucion

```bash
# Test instance
uv run python business_units/hotel-trip-agency/e-commerce/pricelist/setup_pricelist_currency.py

# Production
uv run python business_units/hotel-trip-agency/e-commerce/pricelist/setup_pricelist_currency.py --target prod

# Ambas
uv run python business_units/hotel-trip-agency/e-commerce/pricelist/setup_pricelist_currency.py --target both
```

El script es idempotente — puede ejecutarse multiples veces sin duplicar datos.

## Verificacion

1. Abrir `/es/shop` → precios en S/ (PEN)
2. Cambiar idioma a English → redirect automatico → precios en $ (USD)
3. Navegar paginas en el mismo idioma → sin redirects adicionales
4. Producto con precio USD manual → muestra el precio fijo
5. Producto sin precio manual → muestra conversion automatica PEN→USD
6. Ventana incognito desde IP internacional → USD por GeoIP

## Agregar precios manuales en USD

Desde Odoo UI:
1. Ir a Ventas > Configuracion > Listas de Precios > USD minorista
2. Agregar regla: Producto especifico > Precio fijo > $XX

O via XML-RPC:
```python
client.execute('product.pricelist.item', 'create', [{
    'pricelist_id': 2,                    # USD pricelist
    'applied_on': '1_product',            # Producto especifico
    'product_tmpl_id': PRODUCT_TMPL_ID,   # ID del product.template
    'compute_price': 'fixed',
    'fixed_price': 25.0,                  # Precio en USD
}])
```

## Notas tecnicas (Odoo 19 SaaS)

- `product.pricelist.item` NO tiene campo `sequence` — la prioridad se determina por `applied_on` (producto especifico > template > categoria > global)
- `res.currency.rate` NO tiene campo `inverse_rate`
- Odoo auto-crea una regla `fixed_price=0.0` global al crear pricelists nuevas — el script la elimina
- El `change_pricelist` route requiere `selectable=True` en la pricelist
- GeoIP: si ALGUNA pricelist tiene `country_group_ids`, Odoo ignora las que no tienen grupos — por eso ambas necesitan country groups asignados
- Odoo 19 usa URLs slug-based: `/shop/change_pricelist/2` → 301 → `/en/shop/change_pricelist/usd-minorista-usd-2`

## Archivos relacionados

| Archivo | Descripcion |
|---------|-------------|
| `e-commerce/pricelist/setup_pricelist_currency.py` | Script de configuracion |
| `agency/defaults/views.py` → `ECOM_PRICELIST_LANG_SWITCH_ARCH` | Arch XML del QWeb view (JS) |
| `agency/setup_ecommerce.py` | Setup de botones "Cotizar" y prefijos de precio |
