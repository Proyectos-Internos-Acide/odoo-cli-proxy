# Bug: Desfase de horas en Planning Slots del modulo Hotel/Rental

## Resumen

Al usar los modulos **Planning + Sale Rental** en Odoo (saas-19.1), los turnos de planificacion
generados desde ventas de alquiler (ecommerce o ventas manuales) presentan un **desfase de 10 horas**
respecto a las horas configuradas en el producto (pickup_time / return_time).

**Ejemplo**: Un producto con `pickup_time=12.0` (12:00 PM) y `return_time=11.0` (11:00 AM) genera
planning slots con horarios de 2:00 AM a 1:00 AM en vez de 12:00 PM a 11:00 AM.

---

## Causa raiz

La automatizacion `booking_engine.industry_fix_slot_times` (ID tecnico: `booking_engine.industry_fix_slot_times`)
contiene un bug de conversion de timezone en Python.

### Codigo con bug

```python
# Crea un datetime NAIVE (sin timezone) con la hora del pickup_time
start = datetime.datetime(year=start_datetime.year, month=start_datetime.month,
                          day=start_datetime.day, hour=int(pickup_time), ...)

# BUG: Llama .astimezone() en un datetime NAIVE
# Python lo interpreta como hora del servidor (UTC), no como hora local
start_datetime = start.astimezone(tz=timezone(tz))
```

### Por que falla

1. `pickup_time = 12.0` (mediodia hora local, ej: America/Lima)
2. Se crea `datetime(2026, 2, 16, 12, 0, 0)` - **naive**, sin timezone
3. Python trata el naive como hora del sistema (UTC en servidores Odoo)
4. `.astimezone(America/Lima)` convierte: 12:00 UTC -> 07:00 Lima (UTC-5)
5. Se guarda `07:00` como UTC en la BD
6. La UI muestra: 07:00 UTC - 5h = **02:00 AM** Lima

**Resultado**: doble conversion de timezone = desfase de 2x el offset (10 horas para UTC-5).

### Segundo bug: constraint violation

El codigo original escribia `start_datetime` y `end_datetime` por separado:

```python
record['start_datetime'] = start_utc.replace(tzinfo=None)  # Trigger write + flush
record['end_datetime'] = end_utc.replace(tzinfo=None)
```

Al escribir `start_datetime` primero, el ORM hace flush y valida la constraint
`planning_slot_check_start_date_lower_end_date` con el `end_datetime` viejo,
causando `CheckViolation` si el nuevo start > viejo end.

### Tercer problema: defaults incorrectos

```python
pickup_time = record.sale_line_id.product_id.pickup_time or 18.0  # 6 PM
return_time = record.sale_line_id.product_id.return_time or 9.0   # 9 AM
```

Los defaults `18.0` y `9.0` no son apropiados para la mayoria de hoteles.
Ademas, sin la condicion `if not record.sale_line_id: continue`, la automatizacion
modificaba asignaciones manuales (sin orden de venta) usando estos defaults.

---

## Solucion

### Codigo corregido

```python
tz = env.ref('website.default_website').tz
tz_info = dateutil.tz.gettz(tz)
for record in records:
    if not record.sale_line_id: continue
    if not record.role_id.x_is_a_room_offer: continue
    pickup_time = record.sale_line_id.product_id.pickup_time or 12.0
    return_time = record.sale_line_id.product_id.return_time or 11.0
    # Convert to local timezone to get the correct local date
    start_local = record.start_datetime.astimezone(tz=dateutil.tz.UTC).astimezone(tz=tz_info)
    end_local = record.end_datetime.astimezone(tz=dateutil.tz.UTC).astimezone(tz=tz_info)
    expected_start_time = f"{int(pickup_time):02d}:{int(pickup_time % 1 * 60):02d}:00"
    if record.start_datetime and start_local.strftime('%H:%M:%S') != expected_start_time:
        start_local = start_local.replace(hour=int(pickup_time), minute=int(pickup_time % 1 * 60), second=0)
    expected_end_time = f"{int(return_time):02d}:{int(return_time % 1 * 60):02d}:00"
    if record.end_datetime and end_local.strftime('%H:%M:%S') != expected_end_time:
        end_local = end_local.replace(hour=int(return_time), minute=int(return_time % 1 * 60), second=0)
    if start_local >= end_local:
        end_local = end_local + datetime.timedelta(days=1)
    # Convert back to UTC for storage
    start_utc = start_local.astimezone(dateutil.tz.UTC)
    end_utc = end_local.astimezone(dateutil.tz.UTC)
    # Write both fields at once to avoid constraint violation
    record.write({
        'start_datetime': start_utc.replace(tzinfo=None),
        'end_datetime': end_utc.replace(tzinfo=None),
    })
for record in records:
    if not record.sale_line_id: continue
    nights = 0
    if record.sale_line_id.planning_slot_ids:
        nights = sum(record.sale_line_id.planning_slot_ids.mapped('x_nights'))
    record.sale_line_id.update({
        'start_date': record.start_datetime,
        'return_date': record.end_datetime,
        'x_nights': nights,
    })
    record.sale_line_id._reset_price_unit()
```

### Cambios clave

| Problema | Solucion |
|---|---|
| Datetime naive tratado como UTC | Convertir a timezone local primero con `dateutil.tz.gettz()`, luego ajustar hora y reconvertir a UTC |
| Constraint violation al escribir campos | Usar `record.write({...})` para escribir ambos campos en un solo UPDATE |
| Defaults inapropiados (18.0/9.0) | Cambiados a 12.0/11.0 (check-in mediodia, check-out 11 AM) |
| Modifica asignaciones manuales | Agregar `if not record.sale_line_id: continue` al inicio |

### Aplicar el fix via XML-RPC

```python
from odoo_cli import OdooClient
client = OdooClient()
client.connect()

# El codigo corregido (ver arriba)
fixed_code = '''...'''

# Buscar la automatizacion por xml_id
automation = client.search_read('base.automation',
    domain=[['name', 'like', 'Fix Slot Times']],
    fields=['action_server_ids'])
server_action_id = automation[0]['action_server_ids'][0]

# Actualizar el codigo
client.execute('ir.actions.server', 'write', [server_action_id], {'code': fixed_code})
```

### Corregir slots existentes

```bash
uv run python business_units/hotel-trip-agency/hotel/debug_planning.py sale-vs-planning S00020
```

Para forzar la re-ejecucion de la automatizacion en slots existentes, escribir un valor
diferente en `start_datetime`:

```python
client.execute('planning.slot', 'write', [slot_id], {
    'start_datetime': '2026-02-16 08:00:00',  # Valor diferente al actual
})
# La automatizacion se ejecuta y corrige ambas horas
```

---

## Condiciones de la automatizacion

La automatizacion **solo se ejecuta** cuando:

1. El slot tiene una **orden de venta vinculada** (`sale_line_id` existe)
2. El rol del slot es una **habitacion** (`role_id.x_is_a_room_offer = True`)

**No afecta**: turnos manuales, asignaciones de empleados, roles sin `x_is_a_room_offer`.
