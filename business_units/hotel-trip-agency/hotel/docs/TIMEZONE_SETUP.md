# Configuracion de Timezone para Hotel en Odoo

Guia para configurar correctamente todos los componentes de timezone en una instancia
de Odoo que opera como hotel con los modulos Planning + Sale Rental.

Odoo almacena **todas las fechas en UTC** en la base de datos. La conversion a hora local
ocurre en la UI segun el timezone configurado. Si algun componente tiene un timezone
incorrecto, se producen desfases.

---

## Componentes que requieren configuracion

### 1. Usuario administrador

**Modelo**: `res.users`
**Campo**: `tz`
**Donde**: Ajustes > Usuarios > [usuario] > Preferencias > Zona horaria

```python
client.execute('res.users', 'write', [uid], {'tz': 'America/Lima'})
```

> Si el usuario tiene `tz=UTC` o vacio, todas las fechas en la UI se muestran en UTC.

### 2. Todos los usuarios del sistema

Verificar que **todos** los usuarios tengan timezone correcto:

```python
users = client.search_read('res.users', domain=[], fields=['name', 'login', 'tz'])
for u in users:
    print(f'{u["name"]} ({u["login"]}): tz={u.get("tz") or "NOT SET"}')

# Fix masivo
users_to_fix = client.search_read('res.users',
    domain=['|', ['tz', '=', False], ['tz', '=', 'UTC']],
    fields=['id'])
if users_to_fix:
    ids = [u['id'] for u in users_to_fix]
    client.execute('res.users', 'write', ids, {'tz': 'America/Lima'})
```

### 3. Website

**Modelo**: `website`
**Campo**: `tz`
**Donde**: No accesible directamente desde UI, solo via codigo/debug

```python
websites = client.search_read('website', domain=[], fields=['name', 'tz'])
# Verificar que tz coincida con la ubicacion del hotel
```

> El website.tz se usa en la automatizacion `Fix Slot Times` como referencia de timezone.

### 4. Empresa (Company)

**Modelo**: `res.company`
**Campo**: `resource_calendar_id` (calendario de recursos asociado)
**Donde**: Ajustes > Empresas > [empresa]

La empresa no tiene campo `tz` directo, pero su calendario de recursos si.

### 5. Calendarios de recursos

**Modelo**: `resource.calendar`
**Campo**: `tz`
**Donde**: Ajustes > Tecnico > Recursos > Horarios laborales

```python
calendars = client.search_read('resource.calendar', domain=[], fields=['name', 'tz'])
for cal in calendars:
    print(f'{cal["name"]}: tz={cal.get("tz")}')

# Fix masivo
cals_to_fix = client.search_read('resource.calendar',
    domain=[['tz', '=', 'UTC']], fields=['id'])
if cals_to_fix:
    ids = [c['id'] for c in cals_to_fix]
    client.execute('resource.calendar', 'write', ids, {'tz': 'America/Lima'})
```

Calendarios tipicos en un hotel:

| Calendario | Proposito | tz recomendado |
|---|---|---|
| Standard 40 hours/week | Empleados | America/Lima |
| Rental 24/7 | Habitaciones (recursos materiales) | America/Lima |
| Opening time | Restaurante/servicios | America/Lima |

### 6. Recursos (habitaciones, mesas, equipos)

**Modelo**: `resource.resource`
**Campo**: `tz`
**Donde**: No accesible directamente, solo via codigo/debug

```python
resources = client.search_read('resource.resource', domain=[], fields=['name', 'tz', 'resource_type'])
for r in resources:
    print(f'{r["name"]}: tz={r.get("tz")}, type={r.get("resource_type")}')

# Fix masivo
res_to_fix = client.search_read('resource.resource',
    domain=[['tz', '=', 'UTC']], fields=['id'])
if res_to_fix:
    ids = [r['id'] for r in res_to_fix]
    client.execute('resource.resource', 'write', ids, {'tz': 'America/Lima'})
```

> Cada habitacion es un `resource.resource` de tipo `material`. Si su `tz` es UTC
> mientras el usuario/calendario es America/Lima, puede causar conversiones incorrectas.

---

## Script de configuracion rapida

Usar con `debug_planning.py` o directamente:

```python
#!/usr/bin/env python3
"""Configura timezone para todos los componentes de un hotel en Odoo."""
import sys, os
# Adjust path to point to project root where odoo_cli package lives
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
from odoo_cli import OdooClient

TIMEZONE = 'America/Lima'  # Cambiar segun ubicacion del hotel

client = OdooClient()
uid = client.connect()

# 1. Usuario actual
client.execute('res.users', 'write', [uid], {'tz': TIMEZONE})
print(f'[OK] Usuario actual: tz={TIMEZONE}')

# 2. Todos los usuarios sin timezone o con UTC
users = client.search_read('res.users',
    domain=['|', ['tz', '=', False], ['tz', '=', 'UTC']],
    fields=['id', 'name'])
if users:
    ids = [u['id'] for u in users]
    client.execute('res.users', 'write', ids, {'tz': TIMEZONE})
    for u in users:
        print(f'[OK] Usuario {u["name"]}: tz={TIMEZONE}')

# 3. Calendarios de recursos
cals = client.search_read('resource.calendar',
    domain=[['tz', '!=', TIMEZONE]],
    fields=['id', 'name'])
if cals:
    ids = [c['id'] for c in cals]
    client.execute('resource.calendar', 'write', ids, {'tz': TIMEZONE})
    for c in cals:
        print(f'[OK] Calendario "{c["name"]}": tz={TIMEZONE}')

# 4. Recursos (habitaciones, mesas, etc)
resources = client.search_read('resource.resource',
    domain=[['tz', '!=', TIMEZONE]],
    fields=['id', 'name'])
if resources:
    ids = [r['id'] for r in resources]
    client.execute('resource.resource', 'write', ids, {'tz': TIMEZONE})
    for r in resources:
        print(f'[OK] Recurso "{r["name"]}": tz={TIMEZONE}')

print(f'\nConfiguracion completa. Timezone: {TIMEZONE}')
```

---

## Verificacion

Despues de configurar, usar el comando de debug para verificar:

```bash
uv run python business_units/hotel-trip-agency/hotel/debug_planning.py timezone
```

Salida esperada (todo en America/Lima):

```
=== User Timezone ===
  User: admin (admin@hotel.com)
  Timezone: America/Lima

=== Companies ===
  Company: Mi Hotel
  Resource Calendar: Standard 40 hours/week

=== Resource Calendars ===
  Standard 40 hours/week: tz=America/Lima
  Rental 24/7: tz=America/Lima
  Opening time: tz=America/Lima

=== Resources ===
  101: tz=America/Lima
  201: tz=America/Lima
  ...
```

---

## Timezones comunes para Peru y Latinoamerica

| Pais | Timezone |
|---|---|
| Peru | America/Lima |
| Colombia | America/Bogota |
| Chile | America/Santiago |
| Argentina | America/Argentina/Buenos_Aires |
| Mexico (Centro) | America/Mexico_City |
| Ecuador | America/Guayaquil |
| Bolivia | America/La_Paz |
| Brasil (Sao Paulo) | America/Sao_Paulo |
