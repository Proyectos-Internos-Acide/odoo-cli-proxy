# Lista de Capturas de Pantalla para las Guías de Usuario

Instrucciones: Tomar cada captura de pantalla en la instancia de producción de Odoo, guardarla con el nombre de archivo indicado en la carpeta `screenshots/` junto a las guías.

**Resolución recomendada:** 1920x1080, navegador en modo normal (no incógnito), zoom al 100%.

---

## Guía 1: Ventas de Tours con Biblia Operativa

| # | Archivo | Descripción | Navegación paso a paso | Qué debe ser visible |
|---|---------|-------------|----------------------|---------------------|
| 1 | `01_lista_cotizaciones.png` | Lista de cotizaciones | Menú > Ventas > Pedidos > Cotizaciones | Lista con al menos 3-4 cotizaciones visibles, columnas: Número, Cliente, Fecha, Total, Estado |
| 2 | `02_nueva_cotizacion_plantilla.png` | Formulario de nueva cotización con plantilla seleccionada | Cotizaciones > botón "Nuevo" > seleccionar plantilla en campo "Plantilla de cotización" | Formulario con cliente, plantilla seleccionada, y líneas de pedido auto-rellenadas |
| 3 | `03_campos_tour.png` | Campos específicos del tour | Misma cotización del paso 2, sección superior | Campos visibles: "Es un tour" (marcado), Fecha inicio, Fecha fin, Nro. pasajeros, Tipo de servicio, Ciudad de salida |
| 4 | `04_biblia_itinerario.png` | Tabla de itinerario en Biblia Operativa | Misma cotización > clic en pestaña "Biblia Operativa" | Tabla con al menos 3 filas de itinerario: Día, Título, Descripción, Alojamiento, Comidas |
| 5 | `05_biblia_operadores.png` | Tabla de operadores en Biblia Operativa | Misma pestaña "Biblia Operativa" > scroll abajo | Tabla de operadores con: Proveedor, Tipo servicio, Costo, Moneda, Costo PEN. Al menos 2-3 operadores |
| 6 | `06_biblia_inclusiones.png` | Campo de inclusiones HTML | Misma pestaña "Biblia Operativa" > sección Inclusiones | Editor HTML con lista de servicios incluidos (transporte, alojamiento, guía, etc.) |
| 7 | `07_pasajeros_semaforo.png` | Pestaña de pasajeros con semáforo de identidad | Misma cotización > clic en pestaña "Pasajeros" | Lista de pasajeros con columnas: Nombre, Nacionalidad, Documento, Semáforo (al menos un verde, un rojo y un amarillo idealmente) |
| 8 | `08_costos_margen.png` | Campos de costos y margen calculados | Misma cotización > buscar sección de costos (puede estar en la parte superior o lateral) | Campos: Costo total estimado, Margen estimado, % de margen, todos con valores numéricos |
| 9 | `09_enviar_correo.png` | Botón y diálogo de enviar por correo | Misma cotización > clic en "Enviar por correo" | Diálogo de composición de email con: destinatario, asunto, cuerpo del mensaje, PDF adjunto |
| 10 | `10_confirmar_pedido.png` | Botón de confirmar pedido | Abrir una cotización en estado "Cotización enviada" | Barra de acciones con botón "Confirmar" visible y resaltado |
| 11 | `11_proyecto_tareas.png` | Proyecto auto-creado con tareas en kanban | Menú > Proyecto > abrir el proyecto del tour recién confirmado | Vista kanban con columnas de etapas y tareas: Confirmar Reservas, Coordinar Transporte, etc. |
| 12 | `12_boton_crear_oc.png` | Botón "Crear OC desde Operadores" | Pedido confirmado > pestaña "Biblia Operativa" > scroll al final de operadores | Botón claramente visible al final de la tabla de operadores |
| 13 | `13_operadores_estado_oc.png` | Tabla de operadores con columnas de OC y Estado | Después de haber generado OCs > pestaña "Biblia Operativa" > operadores | Columnas OC y Estado OC visibles con datos (ej: "PO00001", "Borrador") |
| 14 | `14_boton_compras.png` | Botón inteligente "Compras" | Pedido con OCs generadas > barra superior de smart buttons | Botón "Compras" con número de OCs (ej: "2 Compras") |
| 15 | `15_tarea_flota.png` | Tarea con campos de flota | Proyecto > abrir tarea "Coordinar Transporte" > marcar "Requiere vehículo propio" | Campos: casilla "Requiere vehículo propio" marcada, Vehículo, Conductor, Asientos necesarios, Asientos disponibles |
| 16 | `16_alerta_vehiculo.png` | Alerta de conflicto de vehículo | Tarea > asignar un vehículo que ya esté asignado en las mismas fechas | Mensaje de advertencia/alerta en el chatter de la tarea indicando el conflicto |
| 17 | `17_grupos_tour_lista.png` | Lista de Grupos de Tour | Menú > Ventas > Pedidos > Grupos de Tour | Lista con al menos 1-2 grupos con: Nombre, Fecha inicio, Fecha fin, Capacidad |
| 18 | `18_grupo_tour_form.png` | Formulario de un Grupo de Tour | Grupos de Tour > abrir un grupo existente | Formulario completo: Nombre, Fechas, Capacidad, lista de Pasajeros, Notas |
| 19 | `19_registro_trabajo.png` | Registro de trabajo en una tarea | Proyecto > Tarea > pestaña "Registro de Trabajo" | Tabla con al menos 2 entradas: Operador, Tipo servicio, Fecha, Horas. Totales visibles arriba |
| 20 | `20_pdf_biblia.png` | Preview del PDF Biblia Operativa | Pedido > Imprimir > Biblia Operativa > captura del PDF | Primera página del PDF mostrando el itinerario y datos del tour |
| 21 | `21_pdf_voucher.png` | Preview del PDF Voucher Pasajero | Pedido > Imprimir > Voucher Pasajero > captura del PDF | Una página del voucher con datos del pasajero e itinerario |
| 22 | `22_plantillas_lista.png` | Lista de plantillas de cotización | Menú > Ventas > Configuración > Plantillas de cotización | Lista con al menos 3-4 plantillas con nombre y estado |
| 23 | `23_plantilla_biblia.png` | Formulario de plantilla con Biblia | Plantillas > abrir una plantilla > pestaña "Biblia Operativa" | Itinerario pre-configurado y operadores por defecto |

---

## Guía 2: Gestión de Hospedaje

| # | Archivo | Descripción | Navegación paso a paso | Qué debe ser visible |
|---|---------|-------------|----------------------|---------------------|
| 1 | `h01_productos_habitacion.png` | Lista de productos de habitación | Menú > Ventas > Productos > filtrar por categoría "Apart./Hotel" | Lista de habitaciones con: Nombre, Precio, Categoría |
| 2 | `h02_producto_atributos.png` | Formulario de producto habitación con atributos | Abrir una habitación > pestaña "Atributos y Variantes" | Atributos visibles: Camas, Baños, WiFi, TV, etc. con sus valores |
| 3 | `h03_cotizacion_habitacion.png` | Cotización con habitación y fechas de alquiler | Cotizaciones > Nuevo > agregar una habitación como línea | Formulario con cliente, línea de habitación, fechas de alquiler visibles |
| 4 | `h04_fechas_alquiler.png` | Detalle de fechas de alquiler en la línea de pedido | Misma cotización > expandir la línea de la habitación | Campos: Fecha de alquiler (inicio), Fecha de devolución, Duración (noches), Precio calculado |
| 5 | `h05_pedido_confirmado.png` | Pedido confirmado con botón de planificación | Confirmar la cotización anterior | Estado "Pedido de venta", botón inteligente "Planificación" visible en la barra superior |
| 6 | `h06_gantt_planificacion.png` | Vista Gantt de planificación de habitaciones | Menú > Planificación > vista "Por Recurso" | Diagrama Gantt con habitaciones en el eje Y, tiempo en el eje X, bloques de color para reservas |
| 7 | `h07_detalle_slot.png` | Detalle de un slot de planificación | Clic en un bloque de color en el Gantt | Popup con: Habitación, Fecha/hora inicio (check-in), Fecha/hora fin (check-out), Pedido vinculado |
| 8 | `h08_nuevo_producto_habitacion.png` | Formulario de crear nueva habitación | Ventas > Productos > Nuevo > llenar datos básicos | Formulario con: Nombre, Tipo "Servicio", Categoría "Apart./Hotel", Precio, "Es oferta de habitación" marcado |

---

## Guía 3: E-commerce

| # | Archivo | Descripción | Navegación paso a paso | Qué debe ser visible |
|---|---------|-------------|----------------------|---------------------|
| 1 | `e01_producto_web.png` | Página de producto tour en el sitio web | Abrir el sitio web > navegar a /shop > clic en un tour | Página del producto con: foto, nombre, precio con prefijo "desde"/"aprox.", botón "Solicitar Cotización" (NO "Agregar al carrito") |
| 2 | `e02_modal_cotizacion.png` | Modal de solicitud de cotización | Misma página > clic en "Solicitar Cotización" | Formulario modal con campos: Nombre completo, Email, Teléfono, Descripción del viaje |
| 3 | `e03_listado_tienda.png` | Listado de productos en la tienda | Sitio web > /shop | Grid de productos con: fotos, nombres, precios, botones "Cotizar" en los tours |
| 4 | `e04_listas_precios.png` | Lista de precios en el backend | Menú > Ventas > Configuración > Listas de precios | Lista mostrando al menos: PEN (por defecto) y USD, con columnas Nombre, Moneda, Sitio web |
| 5 | `e05_regla_conversion.png` | Regla de conversión en la lista USD | Listas de precios > abrir "USD" > sección de reglas | Regla global visible: Aplicar en "Todos los productos", Calcular precio "Fórmula", Base "Precio de venta" |
| 6 | `e06_tipo_cambio.png` | Tipo de cambio USD | Menú > Contabilidad > Configuración > Monedas > clic en USD | Detalle de la moneda USD con: tasa actual, fecha de la última tasa |
| 7 | `e07_precio_manual.png` | Regla de precio manual para un producto | Listas de precios > USD > agregar línea con precio fijo | Nueva regla visible: Aplicar en "1 Producto", Producto seleccionado, Calcular precio "Precio fijo", valor ingresado |
| 8 | `e08_conciliacion_comision.png` | Conciliación bancaria mostrando comisión | Menú > Contabilidad > Banco > Conciliación | Vista de conciliación con: línea del extracto bancario (monto depositado), pago registrado (monto completo), diferencia marcada como "Gasto bancario/Comisión" |
| 9 | `e09_canal_livechat.png` | Configuración del canal de Livechat | Menú > Sitio Web > Livechat > Canales > abrir canal | Formulario del canal: nombre, texto del botón, colores, regla de aparición |
| 10 | `e10_conversacion_livechat.png` | Conversación del Livechat con IA | Menú > Conversaciones > buscar un canal de livechat con conversación | Historial de chat mostrando: mensajes del visitante y respuestas del bot con recomendaciones de tours |
| 11 | `e11_plantillas_whatsapp.png` | Lista de plantillas WhatsApp filtrada | Menú > Marketing > WhatsApp > Plantillas > buscar "Auto:" | Lista filtrada mostrando: Auto: Bienvenida, Auto: Info Tours, Auto: Cotización, etc. |
| 12 | `e12_plantilla_whatsapp_form.png` | Formulario de una plantilla WhatsApp | Abrir una plantilla (ej: "Auto: Info Tours") | Formulario con: Nombre, Cuerpo (texto), Cuerpo en inglés, Condición de disparo, Keywords |
| 13 | `e13_editor_web.png` | Editor web en modo edición | Menú > Sitio Web > navegar a página principal > clic "Editar" | Sitio web en modo edición con: barra de herramientas visible, panel de snippets, contenido editable |
| 14 | `e14_productos_relacionados.png` | Productos opcionales/relacionados en el backend | Ventas > Productos > abrir un tour > pestaña "Ventas" | Campo "Productos opcionales" con 3-4 productos seleccionados |

---

## Resumen de capturas

| Guía | Cantidad | Archivos |
|------|----------|----------|
| Guía 1: Tours y Biblia Operativa | 23 | `01_*.png` a `23_*.png` |
| Guía 2: Hospedaje | 8 | `h01_*.png` a `h08_*.png` |
| Guía 3: E-commerce | 14 | `e01_*.png` a `e14_*.png` |
| **Total** | **45** | — |

---

## Tips para tomar las capturas

1. **Usar datos de ejemplo reales o realistas** — No dejes formularios vacíos. Usa datos de prueba como "Juan García", "City Tour Cusco", etc.
2. **Resaltar lo importante** — Si es posible, usa una herramienta de anotación para poner flechas o recuadros en los elementos clave
3. **Consistencia** — Usa el mismo tour/cotización para las capturas 2-14 de la Guía 1 (así el usuario ve el mismo ejemplo de principio a fin)
4. **Idioma** — Tomar las capturas con el sistema en español (es_419)
5. **Limpieza** — Cerrar menús y paneles que no son relevantes. No dejar notificaciones/banners visibles
6. **Formato** — PNG, resolución mínima 1920x1080, no comprimir excesivamente
