# Configuracion Fiscal - Agencia de Viajes

## Configuracion actual (por defecto)

Se implemento la **Opcion C: Mixto** como configuracion por defecto.

### Impuestos

| Impuesto | ID | Uso | Mapeado por FOREIGN-EXPORT |
|---|---|---|---|
| **VAT 18%** | 5 | Tours, transporte, alojamiento, servicios turisticos | Si -> 0% Exp |
| **IGV 18% Local** | 24 | Restaurante, productos de consumo local | **No** (siempre 18%) |
| **0% Exp** | 18 | (Destino del mapeo para exportacion) | - |

### Posiciones fiscales

| Posicion | ID | auto_apply | Efecto |
|---|---|---|---|
| **LOCAL PERU** | 3 | Si (Peru) | Mantiene IGV 18% en todo |
| **FOREIGN - EXPORT** | 4 | Si (otros paises) | VAT 18% -> 0% Exp, IGV 18% Local no se toca |

### Asignacion de impuestos por tipo de producto

| Tipo de producto | Impuesto | Cliente peruano | Cliente extranjero |
|---|---|---|---|
| Tours (City Tour, Palcoyo, etc.) | VAT 18% | 18% IGV | 0% Exp |
| Transporte (Shuttle, Traslado) | VAT 18% | 18% IGV | 0% Exp |
| Alojamiento propio | VAT 18% | 18% IGV | 0% Exp |
| Alojamiento externo | VAT 18% | 18% IGV | 0% Exp |
| **Restaurante** (todas cat. id=4) | **IGV 18% Local** | 18% IGV | **18% IGV** |

### Efecto en cotizaciones

- **Cliente peruano**: Todos los productos con 18% IGV (ambos impuestos son 18%)
- **Cliente extranjero**: Tours/transporte/alojamiento a 0% Exp, restaurante a 18% IGV
- Ambos tipos de linea pueden coexistir en una misma cotizacion

### Nota sobre precios incluidos (price_include=True)

Ambos impuestos tienen `price_include=True` (estandar peruano). Cuando la posicion fiscal
mapea VAT 18% -> Exp 0%, Odoo recalcula el precio unitario dividiendo entre 1.18.
Esto genera precios con decimales (ej: S/70 -> S/59.32). Es comportamiento normal de Odoo.

## Preguntas pendientes para el contador

### 1. Beneficio de exportacion de servicios (Apendice V, Ley del IGV)
- La empresa esta registrada en el **Directorio MINCETUR** de prestadores turisticos?
- Si es asi, aplica 0% IGV para servicios a personas no domiciliadas con pago del exterior
- Si NO califica, cambiar a Opcion A (ver abajo)

### 2. Boletos aereos
- Vuelos internacionales: generalmente **exentos** de IGV
- Vuelos domesticos: con **IGV 18%**
- Comision/markup de la agencia: depende de la modalidad
- Puede requerir un tercer impuesto o posicion fiscal especial

### 3. Servicios tercerizados (hoteles externos, transporte)
- Las compras a proveedores llevan IGV en la factura del proveedor
- La reventa al cliente: depende de si es intermediacion o servicio propio

## Como cambiar la configuracion

### Cambiar a Opcion A: Todo con IGV (desactivar exportacion)
```python
# Desactivar auto_apply en FOREIGN-EXPORT
client.execute('account.fiscal.position', 'write', [4], {'auto_apply': False})
```
Resultado: Todas las ventas (nacionales y extranjeras) llevan 18% IGV.

### Cambiar a Opcion B: Exportacion total (sin distinguir restaurante)
```python
# Cambiar restaurante de vuelta a VAT 18% (que si se mapea)
rest_prods = client.search_read('product.template',
    domain=[['categ_id', '=', 4]], fields=['id', 'taxes_id'])
for p in rest_prods:
    if 24 in p['taxes_id']:  # 24 = IGV 18% Local
        new_taxes = [t for t in p['taxes_id'] if t != 24] + [5]  # 5 = VAT 18%
        client.execute('product.template', 'write', [p['id']],
            {'taxes_id': [(6, 0, new_taxes)]})
```
Resultado: TODO se exporta a 0% para extranjeros (incluido restaurante).

### Agregar mas productos a "siempre con IGV"
```python
# Asignar IGV 18% Local (id=24) en vez de VAT 18% (id=5)
client.execute('product.template', 'write', [PRODUCT_ID],
    {'taxes_id': [(6, 0, [24])]})
```

## Accion requerida

**ANTES de facturar en produccion**: Confirmar con el contador cual opcion aplica
y si la empresa califica para el beneficio del Apendice V.

---

Ultima actualizacion: 2026-02-11
