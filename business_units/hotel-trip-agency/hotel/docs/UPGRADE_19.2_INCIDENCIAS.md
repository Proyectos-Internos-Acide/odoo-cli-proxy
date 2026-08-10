# Incidencias tras el upgrade a Odoo saas~19.2

Instancia: `machupicchu-afdestiny-production`
Fecha del upgrade: **2026-07-29 04:36**
Fecha de este analisis: **2026-08-10**

---

## Resumen

Tras la actualizacion automatica de Odoo Online a `saas~19.2`, el modulo Hotel
(paquete de industria `booking_engine`) empezo a fallar en varios puntos.
Todos los fallos comparten la misma raiz.

### Estado de versiones

| Modulo | Version | Nota |
|---|---|---|
| `base` | `saas~19.2.1.3` | actualizado |
| `planning` | `saas~19.2.1.0` | actualizado |
| `web` | `saas~19.2.1.0` | actualizado |
| `booking_engine` | `saas~19.1.1.5` | **rezagado** |
| `base_industry_data` | `saas~19.1.1.1` | **rezagado** |

De 393 modulos instalados, solo esos dos quedaron en 19.1.

---

## Causa raiz comun

En `saas~19.2` el modelo `planning.slot` sustituyo el campo:

```
resource_id   many2one  -> resource.resource      (ELIMINADO)
resource_ids  many2many -> resource.resource      (NUEVO)
```

Un turno pasa de tener **un** recurso a tener **varios**.

`booking_engine` no se actualizo, asi que todo su codigo y sus vistas siguen
apuntando a `resource_id`. Los scripts de migracion de Odoo reescribieron
**algunas** referencias pero no todas:

| Lo que la migracion SI corrigio | Lo que NO corrigio |
|---|---|
| Nodos `<field name="resource_id">` en vistas | Atributos como `default_group_by="resource_id"` |
| Rutas `related` de campos manuales | El `ttype` de esos campos manuales |
| (reescribio 17 acciones de servidor) | El codigo Python que usa `slot.resource_id` |

Como comprobacion: los 248 registros `ir.model.data` de `booking_engine`
conservan `write_date = 2026-01-21`, es decir el modulo **nunca se recargo**.
Lo que cambio el 29-jul lo cambiaron los scripts de migracion, no un upgrade
del paquete.

---

## Incidencia 1 - Gantt de Hotel no carga (RESUELTO)

**Sintoma**: al entrar a Hotel -> Schedule, pantalla en blanco con

```
OwlError: An error occured in the owl lifecycle
Caused by: TypeError: Cannot read properties of undefined (reading 'type')
    at PlanningGanttModel._fetchData
```

**Causa**: la vista `booking_engine.booking_engine_planning_gantt_view` (id 3716)
declara `default_group_by="resource_id"`. El modelo JS del gantt hace:

```js
const fields = this._getFields(metaData);   // incluye groupedBy
for (const fieldName of fields) {
    if (metaData.fields[fieldName.split(".")[0]].type === "many2one") { ... }
    //  ^^^ undefined cuando el campo no existe -> .type revienta
}
```

**Arreglo aplicado** (2026-08-10 15:04:46):

```diff
- <attribute name="default_group_by">resource_id</attribute>
+ <attribute name="default_group_by">resource_ids</attribute>
- <attribute name="form_view_id">3715</attribute>
```

El `form_view_id="3715"` apuntaba ademas a una vista **inexistente**; al quitarlo
cae al formulario por defecto de planning (vista 5108, que si existe).

---

## Incidencia 2 - Kanban de planning no carga (RESUELTO)

**Sintoma**: al cambiar a vista kanban en Hotel -> Schedule

```
TypeError: Cannot read properties of undefined (reading 'raw_value')
    at KanbanRecord.template
```

**Causa**: `sale_planning` reescribio su kanban el 29-jul (vista 3583) y ahora
declara el campo y lo usa en el template por separado:

```xml
<xpath expr="//field[@name='employee_ids']" position="after">
    <field name="sale_line_id" .../>              <!-- declaracion -->
</xpath>
<xpath expr="//div[@name='description']" position="before">
    <div t-if="record.sale_line_id.raw_value">    <!-- uso -->
```

Y `booking_engine` (vista 3707, de enero) **borra la declaracion**:

```xml
<xpath expr="//field[@name='sale_line_id']" position="replace">
    <field name="sale_order_id" .../>
</xpath>
```

Resultado: el template lee `record.sale_line_id.raw_value` sobre `undefined`.
Afecta a las kanban 1149 y 1159.

**Arreglo aplicado** (2026-08-10 15:33:27): cambiar `position="replace"` por
`position="after"` en la vista 3707, para que la declaracion sobreviva.

Se eligio esa opcion en vez de borrar el bloque huerfano del template porque
debilita un xpath existente en lugar de anadir uno nuevo: no introduce puntos
de fallo ante futuros upgrades. Efecto visible: la tarjeta kanban vuelve a
mostrar la linea de pedido de venta (comportamiento estandar de Odoo).

**Barrido**: se revisaron las 186 vistas kanban primarias activas comparando
referencias `record.X.raw_value` contra los `<field>` del arch combinado.
Solo 1149 y 1159 tenian un campo sin declarar. No quedan mas casos.

---

## Incidencia 3 - Formulario de huespedes (RESUELTO)

**Sintoma**: `RPC_ERROR` al abrir el formulario del modelo `x_guests_line`

```
ValueError: KeyError('x_resource_id') while evaluating
"for record in self: record['x_sol_resource_ids'] = record.x_sale_order_id.mapped('order_line.x_resource_id.id')"
```

**Causa**: el campo manual `sale.order.line.x_resource_id` (id 23052) era

```
ttype   = many2one -> resource.resource
related = "planning_slot_ids.resource_ids"
```

Un `many2one` cuyo `related` termina en un **many2many** no se puede instanciar.
Odoo lo descarta al construir el registro, en silencio, y `_fields['x_resource_id']`
deja de existir. La migracion reescribio la ruta `related` de `resource_id` a
`resource_ids` pero no podia cambiar el tipo del campo.

Arrastraba a `rental.order.wizard.line.x_resource_id` (id 23086), que era
`related` al anterior.

**Intentos fallidos** (documentados para no repetirlos):

1. Convertir el campo de `related` a `compute` -> el campo siguio sin cargar.
2. Poner `store=True` -> igual.
3. Se detecto que `fields_get` devolvia `True` o `False` **segun la peticion**:
   hay varios workers de Odoo con registros distintos y persistentemente
   inconsistentes (medido: 5/12 y 6/12 lecturas correctas). Esa inestabilidad
   no se puede resolver desde XML-RPC.

**Arreglo aplicado**: eliminar la dependencia en vez de reparar el campo.

```python
# antes
record['x_sol_resource_ids'] = record.x_sale_order_id.mapped('order_line.x_resource_id.id')
# ahora
record['x_sol_resource_ids'] = record.x_sale_order_id.order_line.planning_slot_ids.resource_ids
```

`depends` paso de `x_sale_order_id.order_line` a
`x_sale_order_id.order_line.planning_slot_ids.resource_ids`.
Misma semantica, pero solo con campos del core que existen siempre.
Medido: **12/12 lecturas correctas**.

Despues se **borraron** los dos campos manuales muertos (23052 y 23086), previa
auditoria de referencias en vistas, campos `related`/`compute`/`depends`,
acciones de servidor, filtros guardados y lineas de exportacion. Barrido final:
190 campos manuales, **0 sin cargar**.

> Nota: la unica coincidencia en el barrido fue la accion de servidor 906, pero
> ahi `x_resource_id` es una clave del `create` de `project.task` (campo 23108,
> que sigue intacto), no el de `sale.order.line`.

---

## Incidencia 4 - Leads de tours desde la web sin notificacion (RESUELTO)

**Sintoma**: los leads del formulario "Request Quote" de las paginas de tour
dejaron de generar el aviso de "nuevo lead".

**Diagnostico**: los leads **si se creaban**. Lo que faltaba era la asignacion:

| | Leads mar/abr | Leads jul/ago |
|---|---|---|
| `user_id` | `ayfdestinyeirl` | `False` |
| Seguidores | 1 | 0 |
| Mensaje `user_notification` | si, inbox/sent | no existe |

Sin `user_id` no hay seguidor, y sin seguidor Odoo no tiene a quien notificar.
El aviso que llegaba era el mensaje "se te ha asignado" que Odoo publica al
asignar comercial.

**Causa**: `website(1).crm_default_user_id` quedo vacio tras el upgrade.
Es el campo que Odoo usa para asignar comercial a los leads que entran por
formulario web. `crm_default_team_id` si seguia puesto (Sales), por eso los
leads nuevos tenian equipo pero no comercial.

El formulario en si (`agency_ecommerce.product_tour_modal`, vista 4850) esta
intacto desde el 28-feb y nunca ha enviado `user_id`; solo manda `name`,
`contact_name`, `email_from`, `phone` y `description`.

**Arreglo aplicado**:

```
website(1).crm_default_user_id: False -> ayfdestinyeirl@gmail.com (uid 2)
```

Y se asignaron los 3 leads huerfanos (ids 10, 11, 12) al mismo comercial.
Esos 3 no generaron notificacion porque la asignacion se hizo desde el propio
usuario y Odoo no se notifica a si mismo; los leads que entren por la web los
crea OdooBot, asi que ahi si se disparara.

**Este arreglo no lo revierte ningun upgrade**: es configuracion propia, no un
registro de `booking_engine`.

---

## Incidencia 5 - No se puede confirmar una venta de hotel (DIAGNOSTICADO)

**Sintoma**: al confirmar un pedido de alquiler

```
Error de validacion
No fue posible reprogramar el turno debido a los conflictos
```

**Lo establecido**:

- **No hay conflicto real**. Los dos pedidos que fallan (`AYF-VT-2026-08-0039` y
  `AYF-VT-2026-08-0040`, ambos del Apartamento 501 / recurso 23) tienen como
  unico turno solapado **el suyo propio** (slots 150 y 151). Odoo calcula
  `overlap_slot_count = 0` y `conflicting_slot_ids = []` en ambos.
- **Es una regresion del upgrade**. El ultimo alquiler confirmado con exito es
  del **2026-07-02**; cero confirmaciones desde el 29-jul.
- **Configuracion divergente**: las 6 habitaciones estan en el calendario
  `Standard 40 hours/week` (8h/dia, lunes a viernes). El calendario
  `Rental 24/7` (24h, 7 dias) existe y esta **vacio**, pese a que
  `TIMEZONE_SETUP.md` documenta que las habitaciones van ahi. Se nota en que el
  slot 151 cubre 4 dias de estancia pero tiene `allocated_hours = 27`.
  Aun asi, esa divergencia es anterior al upgrade y no impedia confirmar.
- La sincronizacion turno<->alquiler esta activa: la accion 898 crea cada rol de
  habitacion con `sync_shift_rental: True`.

### Causa raiz (reproducida)

Experimento controlado en el clon 19.3, una sola variable: que la linea tenga
o no un `planning.slot` ya enlazado antes de confirmar.

| Caso | Turno previo enlazado | Resultado |
|---|---|---|
| A | no | **CONFIRMA OK** (y la confirmacion crea el turno) |
| B | si | **ERROR: `Shift not rescheduled due to conflicts`** |

Ese es el original ingles del mensaje que sale en produccion.

**Cuando la linea ya tiene turno, al confirmar Odoo intenta reprogramarlo al
periodo del alquiler; la comprobacion de disponibilidad cuenta como ocupado el
recurso que esta ocupando ese mismo turno, y se autobloquea.**

En produccion los turnos llegan pre-enlazados por la automatizacion **34
"Rental: Auto-link Planning Slot"** (accion 1292), que engancha turnos huerfanos
(`sale_line_id = False`) del mismo rol que solapen con la reserva. Es el flujo
de "bloquear la habitacion en el gantt y luego crear el pedido".

### Es una regresion, no un cambio de flujo

Los cuatro pedidos que se confirmaron con exito el 2026-07-02 **tambien traian
turno pre-enlazado**:

```
0033: confirmado 14:06 | slot 144 creado 14:06  -> antes
0034: confirmado 14:07 | slot 145 creado 14:07  -> antes
0035: confirmado 14:09 | slot 146 creado 14:09  -> antes
0036: confirmado 14:16 | slot 149 creado 14:15  -> antes
```

Mismo patron, funcionaba. Se rompio con 19.2 y **sigue roto en 19.3**.

### Descartado

- **No es el calendario**. La divergencia de calendarios existe desde antes y no
  interviene: el caso A confirma sin problema con las habitaciones en
  `Standard 40 hours/week`.
- **No es el mensaje de capacidad**. Existe otro error distinto,
  `No enough resources are available for the shifts in: X`, que aparece cuando
  la cantidad de la linea supera el numero de recursos del rol (caso real:
  `AYF-VT-2026-07-0038` pide `product_uom_qty = 2` de "Apartment 701 (1 ppl)"
  y el rol tiene 1 recurso). **Ese error es correcto**, se comporta igual en
  19.2 y 19.3, y no tiene relacion con esta incidencia.
- **Desactivar `sync_shift_rental` no sirve**: deja confirmar, pero genera un
  turno duplicado en la linea.

### El disparador exacto: el recurso asignado al turno

Segundo experimento, aislando una variable mas:

| Caso | Turno previo | Con habitacion asignada | Resultado |
|---|---|---|---|
| D | si | **no** (solo rol) | **CONFIRMA OK**, mismo turno, sin duplicar |
| E | si | si | **ERROR** `Shift not rescheduled due to conflicts` |

La comprobacion de disponibilidad **no excluye el propio turno que esta
moviendo**: ve la habitacion ocupada por el mismo y aborta. El movimiento ni
siquiera cambia nada, porque el turno ya esta en el periodo del alquiler.

### Parche desplegado en produccion

No se puede tocar el core, pero si rodearlo desde datos.

| Objeto | Id en produccion |
|---|---|
| `ir.actions.server` "Confirmar pedido de hotel" | **1322** |
| `ir.ui.view` `sale.order.form.hotel.confirm` (heredada de 3121) | **5183** |

La accion, en una sola transaccion:

1. Busca conflictos **reales**: cualquier otro turno que ocupe la misma
   habitacion en el periodo. Si lo hay, lanza `UserError` con el detalle y no
   confirma nada.
2. Si esta limpio: quita el recurso de los turnos, llama a `action_confirm()`,
   y lo devuelve.

La vista anade un boton "Confirmar" en la cabecera, visible solo cuando
`is_rental_order` y el pedido esta en `draft` o `sent`, y oculta los dos
botones Confirmar estandar en esa misma condicion. Los pedidos que no son de
alquiler conservan el boton normal. La accion tambien queda en el menu
*Acciones* como respaldo.

Pruebas realizadas en el clon antes de desplegar:

| Caso | Resultado |
|---|---|
| Pedido con turno y habitacion asignada | CONFIRMA OK, conserva `resource_ids` |
| Pedido con doble booking real | **RECHAZA**, sigue en borrador |
| Pedido mixto (alquiler + producto normal) | CONFIRMA OK, 2 lineas, turno intacto |

**Limitaciones**:

- Reimplementa la comprobacion de solape que hace el core. Cubre solape de
  recurso en el periodo; no cubre ausencias de calendario ni otras
  validaciones. Para el caso de uso (una habitacion por rol, reservas por
  fechas) es suficiente, pero no es equivalente palabra por palabra.
- Es un parche. Cuando Odoo arregle el bug, se borran la accion 1322 y la
  vista 5183 y no queda rastro.
- **Este si sobrevive a un upgrade de `booking_engine`**: son registros nuevos
  nuestros, no del paquete. La vista 5183 ademas no tiene `ir.model.data`, asi
  que ningun upgrade la toca.

### Salida operativa alternativa (sin el parche)

Confirmar el pedido **antes** de que exista el turno: Odoo lo crea solo, con el
recurso y el periodo correctos (verificado en el caso A). Es decir, invertir el
flujo actual de "bloquear en el gantt y luego vender".

Si la habitacion ya estaba bloqueada en el gantt, hay que desenlazar ese turno
de la linea antes de confirmar y borrar el duplicado despues, lo que no es
practico como rutina.

### Accion recomendada

Reportar a Odoo como regresion, con la reproduccion de arriba: funcionaba en
19.1, se rompio en 19.2 y persiste en 19.3. Es codigo del core (`sale_planning`
/ `planning`), no de `booking_engine`, asi que aqui no hay parche posible por
nuestra parte.

---

## Incidencia 6 - House Keeping (ROTO, DORMIDO)

Tres acciones de servidor siguen usando `slot.resource_id`:

| ID | Nombre | Modelo | Ocurrencias |
|---|---|---|---|
| 901 | HouseKeeping: Set resources as occupied | Sales Order | 3 |
| 902 | HouseKeeping: Set resources as vacant | Sales Order | 3 |
| 906 | HouseKeeping: Daily room update | Resource | 4 |

**No se estan ejecutando**: las 5 automatizaciones que las invocan
(`automation_on_check_in`, `automation_on_check_out`,
`automation_on_task_stage_clean`, `automation_on_task_stage_ready`,
`automation_on_task_stage_modified`) estan **archivadas**, y el cron
`ir_cron_room_update` (id 58) tambien. Ultima actividad en el proyecto
"House Keeping": 2026-02-19.

**Riesgo**: la automatizacion 12 "Activate House Keeping" (activa, sobre Config
Settings) llama a la accion 916, que desarchiva las 5 automatizaciones y el
cron. Si alguien toca ese ajuste, el codigo roto empieza a correr.

**No es un renombrado simple**: `resource_ids` es many2many, hay que iterar el
recordset en vez de sustituir el nombre.

---

## Hallazgos secundarios

| Hallazgo | Detalle |
|---|---|
| Recurso 601 duplicado | Existen dos `resource.resource` llamados `601`: id 26 (sin rol, sin uso) e id 27 (el bueno). El 26 sobra. |
| Slot huerfano 142 | 24/06 13:00 -> 27/06 17:00, apartamento 601, sin linea ni pedido, creado a mano el 30/06. Es el **unico conflicto real** de toda la base: solapa con el slot 141 del pedido 0032. |
| Habitaciones sin calendario 24/7 | Las 6 habitaciones estan en `Standard 40 hours/week`. `Rental 24/7` (id 4) esta vacio. |
| `TIMEZONE_SETUP.md` desactualizado | En 19.2 `resource.calendar` ya **no tiene campo `tz`**. La seccion 5 de ese documento ya no aplica. |
| `OdooClient.write()` roto | `odoo_cli/client.py:82` pasa `[ids, vals]` como un unico argumento posicional; Odoo responde `write() missing 1 required positional argument: 'vals'`. No afecta a nada hoy: **0** llamadas en el repo, los 97 sitios usan `execute(..., 'write', ...)`. `create` y `unlink` no tienen el problema. |

---

## Cambios aplicados en produccion

Todos revertibles. Los tres primeros son registros con `noupdate=False`:
**un upgrade de `booking_engine` los sobrescribe**.

| Fecha | Objeto | Cambio |
|---|---|---|
| 15:04:46 | `ir.ui.view` 3716 | `default_group_by` -> `resource_ids`; quitado `form_view_id=3715` |
| 15:33:27 | `ir.ui.view` 3707 | xpath `position="replace"` -> `position="after"` |
| ~16:05 | `ir.model.fields` 23078 | compute y depends de `x_sol_resource_ids` reescritos |
| ~16:10 | `ir.model.fields` 23052, 23086 | **borrados** (campos muertos) |
| ~16:45 | `website` 1 | `crm_default_user_id` -> uid 2 |
| ~16:45 | `crm.lead` 10, 11, 12 | `user_id` -> uid 2 |

---

## Pendiente de decidir: el upgrade de `booking_engine`

Los parches de vistas son un puente. La solucion de fondo es actualizar el
paquete, pero hay que verificarlo antes en una base de prueba:

**Que sobrescribe un upgrade**: 200 de los 248 registros de `booking_engine`
tienen `noupdate=False`. De ellos, lo editado a mano son 3 etiquetas de campo:

| Campo | Modelo | Etiqueta actual |
|---|---|---|
| `x_document_type` | res.partner | Tipo Doc. de Viaje (Driving license / ID card / Passport) |
| `x_document_number` | res.partner | Nro. Doc. de Viaje |
| `x_resource_ids` | product.template | Resources |

**Que NO corre riesgo**: las 8 vistas propias de agencia (no tienen
`ir.model.data`, ningun upgrade las toca), los 39 campos manuales sin
`ir.model.data`, los modelos propios (`x_tour_group`, `x_task_work_log`,
`x_tour_*_line`) y los 48 registros con `noupdate=True` (atributos Bed y
Bathroom, calendario Rental 24/7, etapas, impuestos). No hay nada de Studio:
`studio_customization` tiene 0 registros.

**Riesgo abierto**: si el XML del paquete nuevo ya no declara alguno de los 58
campos `x_*` propiedad de `booking_engine`, Odoo borraria el xmlid huerfano y
con el el campo y su columna. Los `x_*` registrados bajo modulos core
(`planning`, `product`, `project`, `sale`) ya sobrevivieron el upgrade completo
a 19.2, asi que esos estan probados; los 58 de `booking_engine` no.

---

## Verificacion en una base de test actualizada a saas~19.3

Base: `afdestiny-test-10-ago-2026-test-saas19-0810` (clon de produccion tomado
entre las 15:04 y las 15:33 del 2026-08-10, y despues actualizado).

> Ojo al interpretar: ese clon **si contiene** el parche del gantt (vista 3716,
> 15:04:46), pero **no** los otros tres. Por eso el gantt no sirve de prueba
> alli, y el kanban, el campo manual y los leads si.

### Lo que el upgrade a 19.3 NO arregla

| Problema | Estado en 19.3 |
|---|---|
| `booking_engine` | sigue en **`saas~19.1.1.5`** |
| `base_industry_data` | sigue en **`saas~19.1.1.1`** |
| Kanban 1149 y 1159 | `sale_line_id` sigue sin declarar |
| `sale.order.line.x_resource_id` | sigue `related="planning_slot_ids.resource_ids"` y fuera del registro ORM |
| Acciones House Keeping 901/902/906 | siguen con `slot.resource_id` |
| Menu "Steering" de las notas de 19.3 | **no aparece** (es parte del paquete Hotel, que no se actualizo) |
| `website.crm_default_user_id` | sigue vacio (es dato, no lo restaura ningun upgrade) |

**Conclusion principal**: la actualizacion de plataforma **no actualiza el
paquete de industria**. La causa raiz de todo sobrevive intacta a 19.3.
Esperar a la siguiente version no resuelve nada; los parches tienen que
quedarse y la solucion de fondo pasa por un ticket a Odoo sobre
`booking_engine`.

### Lo que 19.3 si hace bien

Los scripts de migracion reescribieron **4510 vistas**, de las cuales **123 no
tienen `ir.model.data`** (vistas de sitio web con copy-on-write). Caso concreto
nuestro, la vista 3882 `website_sale_renting.rental_product`:

```diff
- request.cart.has_rented_products and ...
+ request.cart.has_rentable_lines and ...
```

Es decir: el tipo de fallo en que una personalizacion de web apunta a un campo
renombrado **si esta cubierto**. Lo que la migracion no puede hacer es cambiar
el `ttype` de un campo, reescribir la semantica de codigo Python, ni arreglar
la logica de un paquete de terceros que no se publica actualizado.

### Cambios de campos 19.2 -> 19.3 en los modelos del hotel

| Modelo | Nuevos | Eliminados |
|---|---|---|
| `planning.slot` | `resources_without_correct_role`, `resources_without_correct_role_count` | ninguno |
| `sale.order` | `has_rentable_lines`, `is_pickup_required`, `is_rating_email_sent` | `amount_undiscounted`, `has_rented_products`, `pickup_location_data` |
| `product.template` | 9 (`free_qty`, `reinvoice_policy`, ...) | `expense_policy`, `service_to_purchase`, `visible_expense_policy` |
| `sale.order.line` | `qty_delivered_percent` | ninguno |
| `resource.resource` | `assigned_employee_id` | ninguno |
| `crm.lead` | `whatsapp_channel_count` | ninguno |
| `project.task` | `document_count` | ninguno |

`planning.slot` no pierde ningun campo: **no hay una cuarta ola** del problema
de `resource_id`.

Se revisaron en produccion todas las referencias a los 6 campos eliminados
(vistas, campos `related`/`compute`/`depends` y acciones de servidor). Todas
pertenecen a modulos core que se actualizan con la plataforma, salvo la vista
3882, que la migracion ya corrige sola. **No hace falta accion preventiva.**

---

## Verificacion

Los scripts de diagnostico usados viven en el scratchpad de la sesion. Los
reutilizables:

- `check_193.py` - snapshot comparable de una instancia (versiones, vista gantt,
  acciones de House Keeping, etiquetas personalizadas, menus). Modos:
  `prod`, `target`, `compare`. Usa `TARGET_MIGRATION_*` del `.env`.
- `sweep_kanban.py` - busca vistas kanban cuyo template lea `record.X.raw_value`
  sin que `X` este declarado en el arch combinado.
- `sweep_manual_fields.py` - compara los campos manuales de `ir.model.fields`
  contra el registro real del ORM; detecta los que Odoo descarto en silencio.
