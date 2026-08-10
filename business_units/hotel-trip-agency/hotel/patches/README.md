# Parches del modulo Hotel (upgrade a saas~19.2)

Nueve parches aplicados en produccion el 2026-08-10 para arreglar el modulo
Hotel tras la actualizacion automatica a Odoo `saas~19.2`.

El diagnostico completo de cada uno esta en
[`../docs/UPGRADE_19.2_INCIDENCIAS.md`](../docs/UPGRADE_19.2_INCIDENCIAS.md).

## Uso

```bash
uv run python hotel_patches.py                    # comprobar produccion
uv run python hotel_patches.py --apply            # reaplicar lo que falte
uv run python hotel_patches.py --target           # comprobar TARGET_MIGRATION_*
uv run python hotel_patches.py --target --apply
```

Es idempotente: cada parche sabe comprobarse antes de tocar nada, y ejecutarlo
dos veces no hace dano. Identifica los objetos por xmlid o por nombre, no por
id, asi que funciona igual en produccion que en un clon.

Salida de ejemplo:

```
  [OK ] gantt         Vista gantt del hotel: default_group_by=resource_ids  id=3716 ...
  [FALTA] kanban      Vista kanban de planning: xpath position=after        id=3707 xpath=replace
```

## Cuando ejecutarlo

- **Siempre despues de actualizar el modulo `booking_engine`.** Es el unico
  evento que revierte parte de los parches (ver la tabla de abajo).
- Como comprobacion rutinaria despues de cualquier upgrade de plataforma,
  aunque no deberia hacer falta.
- Sobre una base de test recien clonada, antes de dar por buena una prueba.

## Que sobrevive a que

| # | Parche | Objeto | Lo revierte un upgrade de `booking_engine` |
|---|---|---|---|
| 1 | `gantt` | vista 3716, `booking_engine` `noupdate=False` | **si** |
| 2 | `kanban` | vista 3707, `booking_engine` `noupdate=False` | **si** |
| 3 | `huespedes` | campo 23078, `booking_engine` `noupdate=False` | **si** |
| 4 | `muertos` | campos borrados de `booking_engine` | **si** (los recrea, y rotos) |
| 5 | `housekeeping` | acciones 901/902/906, `__cloc_exclude__` | **si** |
| 6 | `leads` | `website.crm_default_user_id`, `noupdate=True` | no |
| 7 | `confirmar` | accion y vista nuestras, sin `ir.model.data` | no |
| 8 | `calendarios` | dato en `resource.resource` | no |
| 9 | `duplicado` | dato en `resource.resource` | no |

**Un upgrade de plataforma no los pierde.** Comprobado: una base clonada con el
parche 1 ya puesto se actualizo a `saas~19.3` y la vista 3716 conservo su
`write_date`, intacta. La actualizacion de plataforma **no recarga los datos de
`booking_engine`**, solo ejecuta scripts de migracion sobre la base.

Lo que si los revierte es pulsar *Actualizar* sobre el modulo `booking_engine`
en Aplicaciones. Si eso ocurre, ejecutar `--apply` y listo.

## Los parches, uno a uno

1. **`gantt`** — La vista gantt del hotel agrupaba por `resource_id`, campo que
   19.2 elimino. El modelo JS reventaba con `Cannot read properties of
   undefined (reading 'type')`. Ademas apuntaba a un `form_view_id` inexistente.
2. **`kanban`** — La vista de booking_engine borraba la declaracion
   `<field name="sale_line_id"/>` que `sale_planning` necesita para su plantilla,
   provocando `Cannot read properties of undefined (reading 'raw_value')`. Se
   cambia el xpath de `replace` a `after`.
3. **`huespedes`** — El compute de `x_sol_resource_ids` pasaba por
   `order_line.x_resource_id`, un campo roto. Ahora llega a los recursos por
   campos del core.
4. **`muertos`** — `sale.order.line.x_resource_id` y
   `rental.order.wizard.line.x_resource_id` eran many2one con `related` a un
   many2many: Odoo no los podia instanciar y los descartaba en silencio. Se
   borran; nada los referencia.
5. **`housekeeping`** — Las tres acciones de servidor usaban `slot.resource_id`.
   Reescritas iterando `slot.resource_ids`.
6. **`leads`** — `website.crm_default_user_id` quedo vacio tras el upgrade, asi
   que los leads del formulario web se creaban sin comercial y nadie recibia la
   notificacion.
7. **`confirmar`** — Rodeo a un bug del core: al confirmar un pedido de
   alquiler cuyo turno ya tiene recurso asignado, Odoo falla con *"Shift not
   rescheduled due to conflicts"* porque la comprobacion de disponibilidad no
   excluye el propio turno. La accion comprueba solapes reales, quita el
   recurso, confirma y lo devuelve. **Borrar este parche cuando Odoo arregle el
   bug** (ver [`../docs/TICKET_ODOO_planning_reschedule.md`](../docs/TICKET_ODOO_planning_reschedule.md)).
8. **`calendarios`** — Las habitaciones estaban en `Standard 40 hours/week`, asi
   que una noche de sabado contaba 0 horas y el gantt pintaba noches y fines de
   semana como no disponibles. No afecta a `x_nights` ni a `x_city_tax`.
9. **`duplicado`** — Habia dos recursos `601`; se archiva el que no tiene rol.
