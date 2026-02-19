# Guia de Setup - Modulo Agencia de Viajes

Setup completo para la operacion de agencia de viajes en Odoo 19 SaaS.
Todos los scripts son **idempotentes** (se pueden ejecutar multiples veces sin duplicar datos).

## Pre-requisitos

- Instancia Odoo 19 SaaS con modulos: `sale_management`, `project`, `purchase`, `fleet`, `sale_purchase`
- Booking engine instalado (provee `x_guests`, `x_guest_line_ids`, `x_nationality`, `x_document_type`, `x_document_number`, `x_identity_check` en res.partner)
- Python 3.13+ con `uv` instalado
- Archivo `.env` configurado con credenciales de la instancia

## Orden de Ejecucion

```bash
export PATH="$HOME/.local/bin:$PATH"

# 1. CRITICO: Parchar bug de planning slots (DEBE ejecutarse primero)
uv run python business_units/hotel-trip-agency/hotel/fix_slot_times_automation.py

# 2. Campos custom en contactos y ordenes de venta (sin datos de test)
uv run python business_units/hotel-trip-agency/agency/setup_custom_fields.py
# Para instancia de test, agregar --test-data para poblar pasajeros de prueba:
# uv run python business_units/hotel-trip-agency/agency/setup_custom_fields.py --test-data

# 3. Plantilla de proyecto "Tour Estandar" con tareas y etapas
uv run python business_units/hotel-trip-agency/agency/setup_projects.py

# 4. Automatizaciones de flota y campos en tareas
uv run python business_units/hotel-trip-agency/agency/setup_fleet_automations.py

# 5. Biblia Operativa (modelos, campos, vistas, automatizacion)
uv run python business_units/hotel-trip-agency/agency/setup_biblia_operativa.py

# 6. Formulario de contacto con campos de pasajero
uv run python business_units/hotel-trip-agency/agency/setup_partner_form.py

# 7. Ecommerce: boton "Solicitar Cotizacion" para tours
uv run python business_units/hotel-trip-agency/agency/setup_ecommerce.py

# 8. Grupos de Tour (modelo, vistas, menu)
uv run python business_units/hotel-trip-agency/agency/setup_tour_groups.py
```

## Automatizaciones Nativas del Booking Engine

El modulo `booking_engine` (pre-instalado en instancias con hotel) incluye 14 automatizaciones nativas. **No requieren setup** — vienen con el modulo. Se documentan aqui como referencia operativa.

### POS / Contabilidad
- **Account POS Settle Due** (1): Modulo `account_pos_settle_due`. Al confirmar una factura (`account.move.state=posted`), resetea `customer_due_total=0` en los pedidos POS vinculados y guarda la referencia al asiento contable.

### Planning Slots (Habitaciones)
- **Fix Slot Times** (2): Al crear/modificar un planning slot vinculado a una linea de venta con rol de habitacion (`x_is_a_room_offer`), ajusta `start_datetime`/`end_datetime` segun `pickup_time`/`return_time` del producto, convirtiendo correctamente entre UTC y zona horaria local. Tambien actualiza fechas y noches en la linea de venta. **PARCHEADA** por `fix_slot_times_automation.py` (ver seccion siguiente).
- **Set Rental Start/Return Hours on Create** (3): Al crear/modificar una SO con fechas de alquiler, ajusta las horas de `rental_start_date` y `rental_return_date` segun `pickup_time`/`return_time` del primer producto con periodicidad de alquiler. Recalcula precios con `action_update_rental_prices()`.

### Room Offer → Planning Role (sincronizacion)
- **Create role on stay offer creation** (4): Al crear un producto con `x_is_a_room_offer=True` sin `planning_role_id`, crea automaticamente un `planning.role` con `sync_shift_rental=True`.
- **Edit role name on stay offer modification** (5): Al editar un producto de habitacion, sincroniza el nombre al `planning.role` vinculado.
- **Delete role on stay offer deletion** (6): Al eliminar un producto de habitacion, elimina el `planning.role` vinculado.

### HouseKeeping (Limpieza de habitaciones)
- **On check in** (7): Al cambiar `rental_status` a `return` (check-in), marca los resources (habitaciones) de los planning slots como `x_occupancy=occupied`.
- **On check out** (8): Al cambiar `rental_status` a `returned` (check-out), marca los resources como `x_occupancy=vacant`.
- **On task stage reaching Clean** (9): Cuando una tarea de limpieza llega al stage "Clean" (id=17), si no hay aprobadores configurados, la pasa automaticamente a "Ready" (stage 18) con `state=1_done`.
- **On task stage set to Ready** (10): Trigger `on_change`. Valida que el usuario tenga permisos de aprobador antes de permitir marcar una tarea como "Ready". Si no es aprobador, lanza `UserError`.
- **On stage change** (11): Al cambiar el stage de una tarea de housekeeping (`x_is_house_keeping_project`), ejecuta un `object_write` (no code — actualiza estado directamente).
- **Activate House Keeping** (12): Al activar `x_module_house_keeping` en configuracion, aplica el grupo `booking_engine.group_house_keeping` a todos los usuarios y desarchiva las automatizaciones y cron de housekeeping.
- **Deactivate House Keeping** (13): Al desactivar `x_module_house_keeping`, remueve el grupo y archiva las automatizaciones y cron.
- **On approvers setting set** (14): Al cambiar `x_setting_approvers` en configuracion, guarda el parametro `booking_engine.x_approvers_setting` como booleano.

## Que crea cada script

### 1. fix_slot_times_automation.py
- Parcha la automatizacion "Fix Slot Times" (base.automation id=2) que crashea cuando planning slots tienen `start_datetime=False`
- **CRITICO**: sin este parche, confirmar una cotizacion puede fallar

### 2. setup_custom_fields.py
- Campos en `res.partner`: x_birthdate, x_medical_restrictions, x_emergency_contact_name, x_emergency_contact_phone
- Campos en `sale.order`: x_travel_date, x_departure_city, x_service_type (shared/private), x_train_category
- Categorias de proveedores (Transporte, Tren, Guia, Hotel, Restaurante, Otros)
- Producto "Alojamiento Externo (Tercerizado)"
- Producto "Alojamiento Propio" (servicio generico para cotizaciones de agencia)
- Producto "Servicio de Tour" (SRV-TOUR) — placeholder para lineas de PO generadas desde Biblia Operativa
- Con `--test-data`: pobla datos de pasajeros de prueba y los vincula a cotizaciones (NO usar en produccion)

### 3. setup_projects.py
- Plantilla de proyecto "Tour Estandar" con `is_template=True`
- Etapas kanban: Pendientes, En progreso, Listo, Cancelado
- Tareas estandar: Confirmar Reservas, Coordinar Transporte, Asignar Guia, Verificar Documentacion, Seguimiento Post-Tour
- Vincula productos de tour a la plantilla de proyecto

### 4. setup_fleet_automations.py
**Campos en sale.order:**
- x_is_tour, x_tour_start_date, x_tour_end_date, x_num_passengers

**Campos en project.task:**
- x_tour_start_date, x_tour_end_date (readonly, propagados desde SO)
- x_is_fleet_task (checkbox "Requiere vehiculo propio")
- x_vehicle_id (many2one a fleet.vehicle), x_driver_id (many2one a res.partner)
- x_seats_needed, x_available_seats (calculado por automatizacion)
- x_assigned_operator_id (many2one a res.partner) — operador principal de la tarea
- x_operator_ids (many2many a res.partner) — operadores asignados (visible solo en subtareas)
- x_use_internal_users (boolean) — checkbox para mostrar columna de usuarios internos en subtareas
- x_total_hours_logged (float) — horas registradas (calculado por automatizacion)
- x_remaining_hours (float) — horas restantes (calculado por automatizacion)

**Modelo x_task_work_log:**
- x_task_id (many2one a project.task, cascade), x_partner_id (many2one a res.partner)
- x_service_type (selection: transporte/tren/guia/hotel/restaurante/coordinacion/otros)
- x_description (text), x_date (date), x_hours_spent (float)
- ACL: CRUD para Role/User (group_id=1)
- x_work_log_ids (one2many) en project.task

**Vista de tareas:**
- Hereda de project.task.form (detecta vista padre dinamicamente)
- Agrega campos de flota con visibilidad condicional (solo si x_is_fleet_task)
- Agrega x_assigned_operator_id (operador principal, excluye clientes)
- Agrega x_operator_ids (many2many_tags, visible solo en subtareas via `invisible="not parent_id"`)
- Agrega x_use_internal_users (checkbox, visible solo en tareas padre via `invisible="parent_id"`)
- Tab "Registro de Trabajo" con resumen de horas (Asignadas, Registradas, Restantes) + lista de work logs
- En lista de subtareas (child_ids): columna "Operadores Asignados" (siempre visible) + "Usuarios Internos" (condicional via `column_invisible="not parent.x_use_internal_users"`)

**Automatizaciones:**
- **Validate Tour Dates** (15): Bloquea si fecha fin < fecha inicio
- **Propagate Tour Data to Tasks** (16): Al crear una tarea vinculada a un SO con `x_is_tour=True`, copia fechas y asientos desde el SO. Corre en `project.task` con trigger `on_create`.
- **Warn Vehicle Date Conflict** (17): Al asignar vehiculo en tarea, verifica conflictos **solo contra SOs confirmados** (`state='sale'`):
  - **Servicios en proceso**: bloquea si vehiculo tiene servicio de Fleet en estado "En proceso" (en taller)
  - Tours privados: bloquea si vehiculo tiene otros tours en mismas fechas
  - Tours compartidos: bloquea si excede capacidad, advierte si hay superposicion
  - Calcula x_available_seats automaticamente
  - Tareas de SOs cancelados o en borrador NO participan en la validacion
- **Sync Tour Data Changes** (18): Si se editan datos del tour en SO confirmada, propaga cambios a tareas. Advierte si cambio a privado tiene conflictos (solo contra SOs confirmados).
- **Work Log: Post to Task Chatter** (20): Al crear registro de trabajo, publica en chatter + recalcula horas
- **Work Log: Recalc Hours on Edit** (21): Al editar horas/operador/tipo/descripcion, publica en chatter + recalcula
- **Work Log: Recalc Hours on Delete** (22): Al eliminar registro, publica en chatter + recalcula (excluye registro eliminado)
- **Task: Recalc Remaining on Allocated Change** (23): Al cambiar horas asignadas, recalcula restantes + publica en chatter
- **Warn Tour on Fleet Service State** (24): Al cambiar el estado de un servicio de Fleet a "En proceso", advierte en chatter del servicio si el vehiculo tiene tours activos asignados (SOs confirmados con fecha fin futura). NO bloquea (permite reparaciones de emergencia).
- **Warn Tour on Fleet Service Create** (25): Al crear un nuevo servicio de Fleet con estado "En proceso", ejecuta la misma validacion que la automatizacion 24. Separada porque `on_create` y `on_write` requieren automatizaciones distintas en Odoo.

**Tipos de servicio de Fleet:**
- Servicios (puntuales): Cambio de aceite, Revision tecnica, Lavado, Reparacion general, Cambio de llantas
- Contratos (recurrentes): SOAT, Seguro vehicular

### 5. setup_biblia_operativa.py (depende de #2 y #4)
**Modelos custom:**
- `x_itinerary_line`: tabla de itinerario dia a dia (campos traducibles)
- `x_operator_line`: operadores asignados con tipo de servicio, costo estimado y vinculo a PO

**Campos:**
- `sale.order`: x_itinerary_line_ids, x_operator_line_ids, x_inclusions, x_key_times, x_special_observations
- `sale.order.template`: x_is_tour, x_itinerary_line_ids, x_operator_line_ids, x_inclusions, x_key_times, x_special_observations
- `x_operator_line`: x_cost (costo estimado), x_purchase_order_id (PO generado, readonly), x_po_state (estado PO, related)

**Related fields en x_guests_line (10 campos):**
- Nacionalidad, tipo doc, nro doc, fecha nacimiento, telefono, email, idioma, restricciones medicas, contacto emergencia (nombre + telefono)
- Todos readonly, jalan datos de res.partner automaticamente

**ACLs:**
- x_itinerary_line: CRUD para Role/User (group_id=1)
- x_operator_line: CRUD para Role/User (group_id=1)

**Vistas:**
- sale.order form: tab "Biblia Operativa" con itinerario, pasajeros (lista+popup), operadores (con costo, PO, estado), boton "Generar Pedidos de Compra", servicios incluidos, horarios, observaciones
- sale.order.template form: tab "Biblia Operativa" con itinerario, operadores, servicios incluidos
- sale.order PDF: tipo de cambio (1 USD = X.XXXX PEN) debajo de los totales

**Automatizacion:**
- "Copy Biblia Operativa from Template" (trigger: on_create_or_write)
- Copia itinerario, operadores, inclusions, key_times, observations de la plantilla a la cotizacion
- Guard: no sobreescribe si la cotizacion ya tiene datos de biblia

**Server action "Create POs from Biblia Operators":**
- Boton `type=action` en tab Biblia Operativa con dialogo de confirmacion
- Agrupa operadores sin PO por proveedor (partner)
- Crea un PO por proveedor con lineas usando producto "Servicio de Tour" (SRV-TOUR)
- Precio de cada linea = `x_cost` del operador
- Vincula PO lines a SO via `sale_order_id` (campo nativo de `sale_purchase`) — habilita smart button "Compras"
- Escribe `x_purchase_order_id` en cada operador para traceabilidad
- Publica mensaje en chatter de la SO con nombres de POs creados
- Idempotente: no duplica POs (solo procesa operadores sin `x_purchase_order_id`)

### 6. setup_partner_form.py
- Vista heredada en res.partner form (busca automaticamente la vista del booking engine)
- Agrega: Fecha de Nacimiento, Restricciones Medicas, Contacto Emergencia, Tel. Emergencia
- Renombra labels: "Tipo Doc. de Viaje", "Nro. Doc. de Viaje" (para diferenciar del ID fiscal)

### 7. setup_ecommerce.py
- 9 vistas QWeb heredadas para la tienda web
- **Deteccion de tours**: categoria interna "Tours y Paquetes turisticos" O categoria publica "Tours" (incluyendo subcategorias)

**Vistas QWeb:**
- `agency_ecommerce.cta_tour_quote`: hereda de `website_sale.cta_wrapper` — oculta "Anadir al carrito" y muestra "Solicitar Cotizacion" en la pagina de producto
- `agency_ecommerce.product_tour_modal`: hereda de `website_sale.product` — modal con formulario que crea un `crm.lead` via `/website/form/`
- `agency_ecommerce.listing_tour_quote`: hereda de `website_sale.shop_product_buttons` — reemplaza boton del listado con "Cotizar" que lleva a la pagina del producto
- `agency_ecommerce.wishlist_tour_quote`: hereda de `website_sale_wishlist.product_wishlist` — oculta add-to-cart en lista de deseos, muestra "Cotizar"
- `agency_ecommerce.dynamic_snippet_tour_quote`: hereda de `website_sale.dynamic_filter_template_product_product_products_item` — oculta add-to-cart en bloques dinamicos de catalogo
- `agency_ecommerce.price_prefix_tour`: hereda de `website_sale.product_price` — prefijo "aprox." (es) / "estimated" (en) en pagina de producto
- `agency_ecommerce.price_prefix_listing`: hereda de `website_sale.products_item` — prefijo "aprox." en cards del listado /shop
- `agency_ecommerce.price_prefix_wishlist`: hereda de `website_sale_wishlist.product_wishlist` — prefijo "aprox." en cards de wishlist
- `agency_ecommerce.price_prefix_dynamic`: hereda de `website_sale.price_dynamic_filter_template_product_product` — prefijo "aprox." en bloques dinamicos

**Lead creado en CRM:**
- `name`: "Cotizacion Web: [Nombre del Tour]"
- `contact_name`: nombre del visitante
- `email_from`: email del visitante
- `phone`: telefono (opcional)
- `description`: texto libre (fechas, pasajeros, preferencias)

**Prerequisitos**: `website_sale` + `website_crm` instalados

### 8. setup_tour_groups.py
- Modelo `x_tour_group`: grupos operativos de pasajeros para tours
- Campos: x_name, x_start_date, x_end_date, x_max_capacity, x_passenger_ids (m2m res.partner), x_notes, x_color
- ACL: CRUD para Role/User (group_id=1)
- Campo `x_tour_group_ids` (many2many) en sale.order
- Campo `x_tour_group_id` (many2one) en project.task (creado por setup_fleet_automations.py)
- Vistas form + list para x_tour_group
- Window action + menu item bajo Ventas > Orders > "Grupos de Tour"

## Flujo Operativo

### Cotizacion → Proyecto

1. **Crear cotizacion**: Seleccionar plantilla de cotizacion marcada como "Es un Tour"
2. **Automatizacion**: Al guardar, se copian datos de la Biblia Operativa de la plantilla (itinerario, operadores, inclusions, etc.). Requiere F5 para ver cambios.
3. **Agregar pasajeros**: En la tab Biblia Operativa, agregar contactos como pasajeros. Sus datos (nacionalidad, documentos, restricciones) se muestran automaticamente desde el formulario de contacto.
4. **Confirmar cotizacion**: Los productos con `service_tracking=task_in_project` crean automaticamente un proyecto con tareas usando la plantilla "Tour Estandar"
5. **Gestionar proyecto**: Las tareas aparecen en el kanban del proyecto (Pendientes → En progreso → Listo)

### Validacion de Identidad (automatica)

El badge de verificacion en la tabla de pasajeros se calcula automaticamente:
- **OK** (verde): contacto tiene nacionalidad + tipo doc + nro doc completos
- **No valido** (rojo): datos incompletos
- **NA** (amarillo): sin datos de identificacion

### Asignacion de Operadores en Subtareas

Las subtareas usan **contactos** (res.partner) como asignacion principal en lugar de usuarios del sistema:

1. **Operadores Asignados** (x_operator_ids): campo many2many_tags que solo aparece en subtareas. Permite asignar multiples contactos/operadores excluyendo clientes (`customer_rank = 0`).
2. **Usuarios Internos** (user_ids): columna oculta por defecto en la lista de subtareas. Para mostrarla, marcar el checkbox **"Mostrar Usuarios Internos"** en la tarea padre.
3. **Operador Principal** (x_assigned_operator_id): campo many2one en todas las tareas para asignacion rapida de un solo operador.

Esto permite que agencias con pocos usuarios de Odoo (1-2 licencias) gestionen la asignacion operativa via contactos, mientras que agencias con mas usuarios pueden habilitar la columna de usuarios con el checkbox.

### Registro de Trabajo

El tab "Registro de Trabajo" permite registrar horas por contacto/operador sin requerir empleados formales en Odoo:

1. **Agregar registro**: fecha, operador/contacto, tipo de servicio, descripcion, horas
2. **Horas calculadas**: se muestran Asignadas, Registradas y Restantes (widget float_time HH:MM)
3. **Auditoria**: cada creacion, edicion o eliminacion publica en el chatter de la tarea con totales actualizados
4. **Solo contactos no-clientes**: el dropdown filtra con `customer_rank = 0`

### Vinculacion SO → PO (Compras desde Biblia Operativa)

La agencia compra servicios a proveedores (transporte, guias, hoteles externos). Los pedidos de compra se generan directamente desde los operadores de la Biblia Operativa:

1. **Llenar operadores**: En la tab Biblia Operativa, agregar operadores con tipo de servicio y **costo estimado** (columna "Costo Est.")
2. **Generar POs**: Click en boton "Generar Pedidos de Compra" debajo de la tabla de operadores
3. **Confirmacion**: El sistema pide confirmacion antes de crear los POs
4. **Resultado**: Se crea un PO por proveedor (agrupando si un mismo proveedor tiene multiples servicios)
5. **Vinculacion**:
   - Columna "Pedido Compra" muestra el PO generado (clickeable para abrirlo)
   - Columna "Estado PO" muestra badge de estado (borrador/enviado/confirmado)
   - Smart button "Compras" en la SO muestra todos los POs vinculados
   - Se publica mensaje en chatter de la SO con los POs creados

**Producto placeholder**: Las lineas de PO usan el producto "Servicio de Tour" (SRV-TOUR). La descripcion de la linea incluye el tipo de servicio y el codigo de la SO.

**Idempotente**: Si se agregan nuevos operadores despues, el boton solo genera POs para los que no tienen uno asignado. Los operadores con PO existente se saltan.

**Nota**: Los POs se crean en estado "borrador". El usuario debe confirmarlos manualmente en el modulo de Compras.

### Ecommerce: Solicitar Cotizacion

Los productos de tour NO muestran "Anadir al carrito" en la tienda web. En su lugar:

1. **Listado de productos** (`/shop`): tours muestran boton "Cotizar" que redirige a la pagina del producto
2. **Pagina del producto**: muestra boton "Solicitar Cotizacion" en vez de "Anadir al carrito"
3. **Click en "Solicitar Cotizacion"**: abre un modal con formulario (nombre, email, telefono, descripcion del viaje)
4. **Enviar formulario**: crea un lead en CRM (`crm.lead`) con nombre "Cotizacion Web: [Tour]"
5. **Modal de exito**: tras enviar, se muestra un modal con mensaje de confirmacion ("Se envio tu solicitud, nos comunicaremos en breve por correo o WhatsApp")
6. **Resultado**: el lead aparece en CRM > Pipeline para seguimiento comercial. El contacto (res.partner) NO se crea automaticamente — se vincula al convertir el lead en oportunidad.

**Nota sobre el lead**: El formulario crea un `crm.lead` con `contact_name`, `email_from` y `phone` directamente en el lead, sin crear un `res.partner`. El flujo estandar de Odoo es: el agente revisa el lead → lo convierte en oportunidad → ahi se crea/vincula el contacto.

**Nota**: productos que NO son tours (restaurante, hotel, etc.) siguen mostrando "Anadir al carrito" normal.

### Grupos de Tour

Los grupos permiten organizar pasajeros operativamente. Un grupo puede contener pasajeros de multiples ventas (tours compartidos) y una venta puede tener pasajeros en multiples grupos.

1. **Crear grupo**: Ventas > Orders > Grupos de Tour > Nuevo. Asignar nombre, fechas, capacidad maxima.
2. **Agregar pasajeros**: En el formulario del grupo, agregar contactos al campo "Pasajeros" (many2many tags).
3. **Vincular a ventas**: En la cotizacion de tour (seccion "Tour"), asignar el grupo en el campo "Grupos" (many2many tags).
4. **Vincular a tareas**: En las tareas de flota (con vehiculo), asignar el grupo en el campo "Grupo de Tour".

**Casos de uso:**
- **Tour compartido**: Crear grupo "Cusco Cultural Feb 15-20". Multiples ventas (S00050, S00051) asignan sus pasajeros al mismo grupo.
- **Tour privado**: El grupo = los pasajeros de una sola venta. Se crea un grupo exclusivo para esa reserva.
- **Grupos grandes**: Una venta con 40 pasajeros puede dividirse en Grupo A y Grupo B, cada uno con su vehiculo.

**Nota**: El vinculo grupo-venta y grupo-pasajeros es manual. No hay automatizacion que auto-asigne pasajeros a grupos.

### Datos del pasajero

Los datos personales (restricciones medicas, fecha nacimiento, emergencia) se editan en el **formulario de contacto** (res.partner), NO en la Biblia Operativa. La Biblia los muestra como solo lectura.

## Archivos de Defaults

| Archivo | Contenido |
|---------|-----------|
| `agency/defaults/views.py` | Arquitecturas XML de todas las vistas (SO, template, partner, PDF, ecommerce, tour groups) |
| `agency/defaults/automations.py` | Codigo Python de 9 automatizaciones (flota + work log) + 1 server action (POs) |
| `agency/defaults/projects.py` | Plantilla de proyecto, etapas, tareas estandar |
| `agency/defaults/products.py` | Productos de tour |
| `agency/defaults/kits.py` | (Deprecado) Configuracion de kits BoM |
| `defaults/categories.py` | IDs de categorias de producto |
| `defaults/i18n.py` | Helpers de traduccion |

## Reportes PDF (ya creados por setup_biblia_operativa.py)

Los reportes se crean automaticamente al ejecutar el script. Aparecen en el menu Imprimir de las ordenes de venta. Las especificaciones a continuacion documentan los campos disponibles para futuras modificaciones.

### Reporte: Biblia Operativa (PDF)

**Objetivo**: Generar un PDF imprimible con toda la informacion operativa del tour para entregar al equipo operativo.

**Modelo**: `sale.order` (solo cuando `x_is_tour=True`)

**Datos disponibles** (campos en sale.order):
- `name`: codigo de reserva (ej: S00028)
- `partner_id`: contacto principal
- `x_tour_start_date`, `x_tour_end_date`: fechas del tour
- `x_service_type`: compartido/privado
- `x_departure_city`: lugar de partida
- `x_num_passengers`: cantidad de pasajeros
- `x_itinerary_line_ids` (o2m a `x_itinerary_line`):
  - `x_day_number`: dia (integer)
  - `x_title`: titulo del dia
  - `x_description`: descripcion detallada
  - `x_accommodation`: alojamiento del dia
  - `x_meals`: comidas incluidas
- `x_guest_line_ids` (o2m a `x_guests_line`, del booking engine):
  - `x_guest_partner_id`: contacto del pasajero
  - `x_nationality_id`: nacionalidad (related)
  - `x_document_type_rel`, `x_document_number_rel`: documento de viaje
  - `x_phone_rel`, `x_email_rel`: contacto
  - `x_medical_rel`: restricciones medicas
  - `x_emergency_name_rel`, `x_emergency_phone_rel`: emergencia
  - `x_guest_identity_check`: verificacion (ok/invalid/na)
- `x_operator_line_ids` (o2m a `x_operator_line`):
  - `x_partner_id`: operador/proveedor
  - `x_service_type`: tipo (transporte/tren/guia/hotel/restaurante/otros)
  - `x_phone_rel`, `x_email_rel`: contacto del operador
- `x_inclusions` (html): servicios incluidos
- `x_key_times` (text): horarios clave
- `x_special_observations` (text): observaciones especiales

**Layout sugerido**:
1. Encabezado con logo empresa + "BIBLIA OPERATIVA" + codigo reserva
2. Seccion "Datos Generales": contacto, fechas, tipo servicio, partida, num pasajeros
3. Tabla "Itinerario": dia | titulo | descripcion | alojamiento | comidas
4. Tabla "Pasajeros": nombre | nacionalidad | documento | telefono | restricciones medicas | emergencia
5. Tabla "Operadores": operador | tipo servicio | telefono | email
6. Seccion "Servicios Incluidos" (render HTML de x_inclusions)
7. Seccion "Horarios Clave" + "Observaciones Especiales"

**Creacion via XML-RPC** (2 pasos):
1. Crear `ir.ui.view` con type='qweb' conteniendo el template QWeb
2. Crear `ir.actions.report` con `model='sale.order'`, `report_type='qweb-pdf'`, `report_name` apuntando al template

### Reporte: Voucher Pasajero (PDF)

**Objetivo**: Documento individual por pasajero para entregarle con su informacion del tour.

**Modelo**: `sale.order` (itera sobre `x_guest_line_ids` generando una pagina por pasajero)

**Datos por pasajero**:
- Nombre completo, nacionalidad, documento
- Itinerario completo del tour (misma tabla que Biblia)
- Servicios incluidos
- Horarios clave
- Nombre y telefono del contacto de emergencia del pasajero
- Operadores asignados al tour (guia, transporte)

**Layout sugerido**:
1. Encabezado con logo + "VOUCHER DE VIAJE" + codigo reserva
2. Datos del pasajero: nombre, nacionalidad, documento, emergencia
3. Datos del tour: fechas, tipo servicio, lugar partida
4. Tabla itinerario dia a dia
5. Servicios incluidos
6. Horarios clave
7. Contactos de operadores (guia, transporte)

**Nota**: Usa `t-foreach="doc.x_guest_line_ids" t-as="guest"` con un page break entre cada pasajero.

## Notas Tecnicas

- Todas las vistas se buscan **por nombre** (no por ID), y se crean dinamicamente si no existen. Esto permite ejecutar los scripts en cualquier instancia Odoo 19 SaaS.
- Las vistas padre se detectan automaticamente (buscan el form view base del modelo).
- La vista de partner busca automaticamente la vista del booking engine que contiene `x_document_type`.
- Los campos `x_name` en modelos custom (`x_itinerary_line`, `x_operator_line`) son auto-creados por Odoo al crear modelos con `state=manual`.

## Referencia: Campos custom por modelo

### res.partner
| Campo | Tipo | Descripcion | Creado por |
|-------|------|-------------|------------|
| x_nationality | many2one (res.country) | Nacionalidad | Booking engine |
| x_document_type | selection | Tipo doc. de viaje | Booking engine |
| x_document_number | char | Nro. doc. de viaje | Booking engine |
| x_identity_check | selection (computed) | Verificacion identidad (ok/invalid/na) | Booking engine |
| x_birthdate | date | Fecha de nacimiento | setup_custom_fields.py |
| x_medical_restrictions | text | Restricciones medicas/alimentarias | setup_custom_fields.py |
| x_emergency_contact_name | char | Nombre contacto emergencia | setup_custom_fields.py |
| x_emergency_contact_phone | char | Telefono contacto emergencia | setup_custom_fields.py |

### sale.order
| Campo | Tipo | Descripcion | Creado por |
|-------|------|-------------|------------|
| x_guests | many2many (res.partner) | Pasajeros | Booking engine |
| x_guest_line_ids | one2many (x_guests_line) | Lineas de pasajeros | Booking engine |
| x_travel_date | date | Fecha de viaje | setup_custom_fields.py |
| x_departure_city | char | Lugar de partida | setup_custom_fields.py |
| x_service_type | selection (shared/private) | Tipo servicio | setup_custom_fields.py |
| x_train_category | char | Categoria de tren | setup_custom_fields.py |
| x_is_tour | boolean | Es un Tour | setup_fleet_automations.py |
| x_tour_start_date | date | Fecha inicio del tour | setup_fleet_automations.py |
| x_tour_end_date | date | Fecha fin del tour | setup_fleet_automations.py |
| x_num_passengers | integer | Numero de pasajeros | setup_fleet_automations.py |
| x_itinerary_line_ids | one2many (x_itinerary_line) | Itinerario | setup_biblia_operativa.py |
| x_operator_line_ids | one2many (x_operator_line) | Operadores | setup_biblia_operativa.py |
| x_inclusions | html | Servicios incluidos | setup_biblia_operativa.py |
| x_key_times | text | Horarios clave | setup_biblia_operativa.py |
| x_special_observations | text | Observaciones especiales | setup_biblia_operativa.py |
| x_tour_group_ids | many2many (x_tour_group) | Grupos de tour | setup_tour_groups.py |

### sale.order.template
| Campo | Tipo | Descripcion | Creado por |
|-------|------|-------------|------------|
| x_is_tour | boolean | Es un Tour | setup_biblia_operativa.py |
| x_itinerary_line_ids | one2many (x_itinerary_line) | Itinerario plantilla | setup_biblia_operativa.py |
| x_operator_line_ids | one2many (x_operator_line) | Operadores por defecto | setup_biblia_operativa.py |
| x_inclusions | html | Servicios incluidos | setup_biblia_operativa.py |
| x_key_times | text | Horarios clave | setup_biblia_operativa.py |
| x_special_observations | text | Observaciones especiales | setup_biblia_operativa.py |

### project.task
| Campo | Tipo | Descripcion | Creado por |
|-------|------|-------------|------------|
| x_tour_start_date | date | Fecha inicio tour (readonly) | setup_fleet_automations.py |
| x_tour_end_date | date | Fecha fin tour (readonly) | setup_fleet_automations.py |
| x_is_fleet_task | boolean | Requiere vehiculo propio | setup_fleet_automations.py |
| x_vehicle_id | many2one (fleet.vehicle) | Vehiculo asignado | setup_fleet_automations.py |
| x_driver_id | many2one (res.partner) | Chofer asignado | setup_fleet_automations.py |
| x_seats_needed | integer | Asientos necesarios | setup_fleet_automations.py |
| x_available_seats | integer | Asientos disponibles (automation) | setup_fleet_automations.py |
| x_assigned_operator_id | many2one (res.partner) | Operador principal | setup_fleet_automations.py |
| x_operator_ids | many2many (res.partner) | Operadores asignados (subtareas) | setup_fleet_automations.py |
| x_use_internal_users | boolean | Mostrar Usuarios Internos en subtareas | setup_fleet_automations.py |
| x_total_hours_logged | float | Horas registradas (auto-calculado) | setup_fleet_automations.py |
| x_remaining_hours | float | Horas restantes (auto-calculado) | setup_fleet_automations.py |
| x_work_log_ids | one2many (x_task_work_log) | Registro de trabajo | setup_fleet_automations.py |
| x_tour_group_id | many2one (x_tour_group) | Grupo de tour (flota) | setup_fleet_automations.py |

### x_tour_group (modelo custom)
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| x_name | char | Nombre del grupo |
| x_start_date | date | Fecha inicio |
| x_end_date | date | Fecha fin |
| x_max_capacity | integer | Capacidad maxima de pasajeros |
| x_passenger_ids | many2many (res.partner) | Pasajeros del grupo |
| x_notes | text | Notas operativas |
| x_color | integer | Color para tags/kanban |

### x_task_work_log (modelo custom)
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| x_sequence | integer | Secuencia |
| x_task_id | many2one (project.task) | Tarea (cascade) |
| x_partner_id | many2one (res.partner) | Operador/Contacto |
| x_service_type | selection | Tipo servicio (transporte/tren/guia/hotel/restaurante/coordinacion/otros) |
| x_description | text | Descripcion del trabajo |
| x_date | date | Fecha |
| x_hours_spent | float | Horas dedicadas |

### x_itinerary_line (modelo custom)
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| x_name | char | Nombre (auto-creado, rec_name) |
| x_sequence | integer | Secuencia (drag & drop) |
| x_day_number | integer | Numero de dia |
| x_title | char (traducible) | Titulo del dia |
| x_description | text (traducible) | Descripcion detallada |
| x_accommodation | char (traducible) | Alojamiento |
| x_meals | char (traducible) | Comidas incluidas |
| x_sale_order_id | many2one (sale.order) | Venta (cascade) |
| x_template_id | many2one (sale.order.template) | Plantilla (cascade) |

### x_operator_line (modelo custom)
| Campo | Tipo | Descripcion |
|-------|------|-------------|
| x_name | char | Nombre (auto-creado, rec_name) |
| x_sequence | integer | Secuencia |
| x_partner_id | many2one (res.partner) | Operador/proveedor |
| x_service_type | selection | Tipo servicio (transporte/tren/guia/hotel/restaurante/otros) |
| x_phone_rel | char (related) | Telefono del operador (readonly) |
| x_email_rel | char (related) | Email del operador (readonly) |
| x_cost | float | Costo estimado del servicio |
| x_purchase_order_id | many2one (purchase.order) | PO generado (readonly) |
| x_po_state | selection (related) | Estado del PO (readonly) |
| x_sale_order_id | many2one (sale.order) | Venta (cascade) |
| x_template_id | many2one (sale.order.template) | Plantilla (cascade) |

### x_guests_line - related fields (readonly)
| Campo | Tipo | Related path |
|-------|------|-------------|
| x_nationality_id | many2one | x_guest_partner_id.x_nationality |
| x_document_type_rel | selection | x_guest_partner_id.x_document_type |
| x_document_number_rel | char | x_guest_partner_id.x_document_number |
| x_birthdate_rel | date | x_guest_partner_id.x_birthdate |
| x_phone_rel | char | x_guest_partner_id.phone |
| x_email_rel | char | x_guest_partner_id.email |
| x_lang_rel | selection | x_guest_partner_id.lang |
| x_medical_rel | text | x_guest_partner_id.x_medical_restrictions |
| x_emergency_name_rel | char | x_guest_partner_id.x_emergency_contact_name |
| x_emergency_phone_rel | char | x_guest_partner_id.x_emergency_contact_phone |

## Referencia: Vistas creadas

| Vista | Modelo | Hereda de | Creado por |
|-------|--------|-----------|------------|
| sale.order.form.inherit.agency_biblia | sale.order | (auto-detectado) | setup_biblia_operativa.py |
| sale.order.template.form.inherit.agency_biblia | sale.order.template | (auto-detectado) | setup_biblia_operativa.py |
| sale.report_saleorder_document.exchange_rate | sale.order | report template (qweb) | setup_biblia_operativa.py |
| project.task.form.inherit.agency_fields | project.task | (auto-detectado) | setup_fleet_automations.py |
| res.partner.form.inherit.agency_guest_fields | res.partner | booking engine view | setup_partner_form.py |
| x_tour_group.form.agency | x_tour_group | (base) | setup_tour_groups.py |
| x_tour_group.list.agency | x_tour_group | (base) | setup_tour_groups.py |
| agency_ecommerce.cta_tour_quote | (qweb) | website_sale.cta_wrapper | setup_ecommerce.py |
| agency_ecommerce.product_tour_modal | (qweb) | website_sale.product | setup_ecommerce.py |
| agency_ecommerce.listing_tour_quote | (qweb) | website_sale.shop_product_buttons | setup_ecommerce.py |
| agency_ecommerce.wishlist_tour_quote | (qweb) | website_sale_wishlist.product_wishlist | setup_ecommerce.py |
| agency_ecommerce.dynamic_snippet_tour_quote | (qweb) | website_sale.dynamic_filter_template_product_product_products_item | setup_ecommerce.py |
| agency_ecommerce.price_prefix_tour | (qweb) | website_sale.product_price | setup_ecommerce.py |
| agency_ecommerce.price_prefix_listing | (qweb) | website_sale.products_item | setup_ecommerce.py |
| agency_ecommerce.price_prefix_wishlist | (qweb) | website_sale_wishlist.product_wishlist | setup_ecommerce.py |
| agency_ecommerce.price_prefix_dynamic | (qweb) | website_sale.price_dynamic_filter_template_product_product | setup_ecommerce.py |

## Referencia: Automatizaciones

### Booking Engine (nativas, IDs 1-14)

| ID | Nombre | Modelo | Trigger | Origen |
|----|--------|--------|---------|--------|
| 1 | Account POS Settle Due | account.move | on_create_or_write (state) | account_pos_settle_due |
| 2 | Fix Slot Times | planning.slot | on_create_or_write (end_datetime, sale_line_id, start_datetime) | booking_engine (parcheada) |
| 3 | Set Rental Start/Return Hours | sale.order | on_create_or_write (rental_return_date, rental_start_date) | booking_engine |
| 4 | Create role on stay offer creation | product.template | on_create_or_write | booking_engine |
| 5 | Edit role name on stay offer modification | product.template | on_write | booking_engine |
| 6 | Delete role on stay offer deletion | product.template | on_unlink | booking_engine |
| 7 | HouseKeeping: On check in | sale.order | on_create_or_write (rental_status) | booking_engine |
| 8 | HouseKeeping: On check out | sale.order | on_create_or_write (rental_status) | booking_engine |
| 9 | HouseKeeping: On task stage reaching Clean | project.task | on_create_or_write (stage_id) | booking_engine |
| 10 | HouseKeeping: On task stage set to Ready | project.task | on_change | booking_engine |
| 11 | HouseKeeping: On stage change | project.task | on_create_or_write (stage_id) | booking_engine |
| 12 | Activate House Keeping | res.config.settings | on_create_or_write | booking_engine |
| 13 | Deactivate House Keeping | res.config.settings | on_create_or_write | booking_engine |
| 14 | HouseKeeping: On approvers setting set | res.config.settings | on_create_or_write (x_setting_approvers) | booking_engine |

### Agencia / Tours (custom, IDs 15-25)

| ID | Nombre | Modelo | Trigger | Creado por |
|----|--------|--------|---------|------------|
| 15 | Validate Tour Dates | sale.order | on_write (x_tour_start_date, x_tour_end_date) | setup_fleet_automations.py |
| 16 | Propagate Tour Data to Tasks | project.task | on_create | setup_fleet_automations.py |
| 17 | Warn Vehicle Date Conflict | project.task | on_write (x_vehicle_id, x_seats_needed, x_tour_start_date, x_tour_end_date) | setup_fleet_automations.py |
| 18 | Sync Tour Data Changes to Tasks | sale.order | on_write (x_service_type, x_num_passengers, x_departure_city, x_tour_start_date, x_tour_end_date) | setup_fleet_automations.py |
| 19 | Copy Biblia Operativa from Template | sale.order | on_create_or_write | setup_biblia_operativa.py |
| 20 | Work Log: Post to Task Chatter | x_task_work_log | on_create | setup_fleet_automations.py |
| 21 | Work Log: Recalc Hours on Edit | x_task_work_log | on_write (x_hours_spent, x_partner_id, x_service_type, x_description) | setup_fleet_automations.py |
| 22 | Work Log: Recalc Hours on Delete | x_task_work_log | on_unlink | setup_fleet_automations.py |
| 23 | Task: Recalc Remaining on Allocated | project.task | on_write (allocated_hours) | setup_fleet_automations.py |
| 24 | Warn Tour on Fleet Service State | fleet.vehicle.log.services | on_write (state) | setup_fleet_automations.py |
| 25 | Warn Tour on Fleet Service Create | fleet.vehicle.log.services | on_create | setup_fleet_automations.py |

### Server Actions (botones en vista)

| Nombre | Modelo | Trigger | Creado por |
|--------|--------|---------|------------|
| Create POs from Biblia Operators (1181) | sale.order | Boton en Biblia Operativa | setup_biblia_operativa.py |

## Comparador de Instancias (Migracion)

Para replicar la configuracion en una nueva instancia Odoo, se puede usar el comparador que detecta que configuraciones custom existen en la instancia source pero faltan en la target.

### Configuracion

Agregar credenciales de la instancia destino en `.env` (dejar vacio para deshabilitar):

```
TARGET_MIGRATION_URL=https://nueva-instancia.odoo.com/
TARGET_MIGRATION_DB=nueva-instancia
TARGET_MIGRATION_USERNAME=admin@empresa.com
TARGET_MIGRATION_PASSWORD=api-key-aqui
```

### Uso

```bash
# Comparacion completa (9 categorias)
uv run python business_units/hotel-trip-agency/compare_instances.py

# Solo una categoria
uv run python business_units/hotel-trip-agency/compare_instances.py --category automations

# Modo verbose (muestra tambien los OK y EXTRA)
uv run python business_units/hotel-trip-agency/compare_instances.py --verbose
```

### Categorias de comparacion

| Categoria | Modelo | Que compara |
|-----------|--------|-------------|
| models | ir.model | Modelos custom (state=manual, ej: x_itinerary_line) |
| fields | ir.model.fields | Campos custom (x_*, state=manual) |
| automations | base.automation | Automatizaciones sin ir.model.data (creadas por scripts) |
| server_actions | ir.actions.server | Server actions de codigo custom |
| views | ir.ui.view | Vistas heredadas custom (sin ir.model.data) |
| acls | ir.model.access | ACLs para modelos custom (x_*) |
| products | product.template | Productos de servicio con sale_ok=True |
| templates | sale.order.template | Plantillas de cotizacion |
| reports | ir.actions.report | Reportes PDF custom |

### Como funciona

1. Conecta a ambas instancias (source via `ODOO_*`, target via `TARGET_MIGRATION_*`)
2. Para cada categoria, consulta `ir.model.data` para distinguir registros nativos (de modulos) vs custom (creados por scripts XML-RPC)
3. Compara por match key (nombre, modelo+campo, etc.) y reporta: `[FALTA]`, `[OK]`, `[EXTRA]`
4. **Read-only**: nunca escribe en ninguna instancia

### Archivos

| Archivo | Proposito |
|---------|-----------|
| `odoo_cli/client.py` | `OdooClient` acepta kwargs opcionales (url, db, username, password) |
| `odoo_cli/target.py` | Factory `get_target_client()` — retorna None si vars vacias |
| `compare_instances.py` | Script principal de comparacion |

## Notas Importantes

- Los campos `x_document_type` / `x_document_number` son para **documentos de viaje** (pasaporte, etc.), NO para identificacion fiscal (eso usa `l10n_latam_identification_type_id` + `vat`)
- La automatizacion de copia de Biblia ejecuta en el servidor, NO actualiza el browser automaticamente. El usuario debe presionar F5 despues de guardar.
- Los campos de itinerario (titulo, descripcion, alojamiento, comidas) son traducibles (es_419/en_US)
- `ir.translation` NO existe en Odoo 19 — para cambiar labels usar `string` en vistas o actualizar `field_description`
