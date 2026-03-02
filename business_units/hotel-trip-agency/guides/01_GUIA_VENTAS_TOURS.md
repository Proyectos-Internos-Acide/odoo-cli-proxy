# Guía de Venta de Paquetes Turísticos con Biblia Operativa

## Tabla de Contenidos

1. [Introducción: Flujo General](#1-introducción-flujo-general)
2. [Crear una Cotización de Tour](#2-crear-una-cotización-de-tour)
3. [Biblia Operativa: Itinerario](#3-biblia-operativa-itinerario)
4. [Biblia Operativa: Operadores](#4-biblia-operativa-operadores)
5. [Biblia Operativa: Inclusiones y Observaciones](#5-biblia-operativa-inclusiones-y-observaciones)
6. [Gestión de Pasajeros](#6-gestión-de-pasajeros)
7. [Costos y Margen](#7-costos-y-margen)
8. [Enviar Cotización al Cliente](#8-enviar-cotización-al-cliente)
9. [Confirmar el Pedido](#9-confirmar-el-pedido)
10. [Crear Órdenes de Compra desde Operadores](#10-crear-órdenes-de-compra-desde-operadores)
11. [Gestión de Flota (Vehículos)](#11-gestión-de-flota-vehículos)
12. [Grupos de Tour](#12-grupos-de-tour)
13. [Registro de Trabajo en Tareas](#13-registro-de-trabajo-en-tareas)
14. [Reportes PDF](#14-reportes-pdf)
15. [Plantillas de Cotización](#15-plantillas-de-cotización)
16. [Hoja de Referencia Rápida](#16-hoja-de-referencia-rápida)

---

## 1. Introducción: Flujo General

La venta de un paquete turístico en A y F Destiny sigue este flujo de trabajo:

```
PASO 1: Llega una consulta (web, WhatsApp, teléfono, email)
    ↓
PASO 2: Se crea una COTIZACIÓN usando una plantilla de tour
    ↓
PASO 3: Se llena la BIBLIA OPERATIVA (itinerario, operadores, inclusiones)
    ↓
PASO 4: Se registran los PASAJEROS con sus documentos
    ↓
PASO 5: Se ENVÍA la cotización al cliente por email
    ↓
PASO 6: El cliente APRUEBA → se CONFIRMA el pedido
    ↓
PASO 7: Se crean automáticamente el PROYECTO y las TAREAS
    ↓
PASO 8: Se generan las ÓRDENES DE COMPRA a los proveedores
    ↓
PASO 9: Se asignan VEHÍCULOS y GUÍAS en las tareas
    ↓
PASO 10: Se ejecuta el tour y se registra el TRABAJO realizado
```

**La Biblia Operativa** es el documento central que consolida toda la información del tour en un solo lugar: el itinerario día por día, los operadores/proveedores asignados, qué servicios están incluidos, los horarios clave y las observaciones especiales. Es una pestaña dentro de cada cotización/pedido de venta.

![Captura 1: Lista de cotizaciones](screenshots/01_lista_cotizaciones.png)

---

## 2. Crear una Cotización de Tour

### 2.1 Abrir el formulario de nueva cotización

1. En el menú principal, ir a **Ventas > Pedidos > Cotizaciones**
2. Hacer clic en el botón **"Nuevo"** (esquina superior izquierda)
3. Se abre un formulario en blanco

### 2.2 Llenar los datos del cliente

1. En el campo **"Cliente"**, escribir el nombre del cliente
2. Si el cliente ya existe, seleccionarlo de la lista desplegable
3. Si es un cliente nuevo, hacer clic en **"Nuevo y editar"** para crear su ficha de contacto

### 2.3 Seleccionar la plantilla de tour

1. En el campo **"Plantilla de cotización"**, buscar el nombre del tour
   - Ejemplo: "City Tour Cusco", "Valle Sagrado Completo", "Machu Picchu 2D/1N"
2. Al seleccionar la plantilla:
   - Las **líneas de pedido** se llenan automáticamente con los productos del tour
   - La **Biblia Operativa** se pre-carga con el itinerario, operadores e inclusiones por defecto

> **Nota importante:** Después de seleccionar la plantilla, la Biblia Operativa se llena en el servidor. Si no ves los datos inmediatamente, presiona **F5** para recargar la página.

![Captura 2: Formulario nueva cotización con plantilla seleccionada](screenshots/02_nueva_cotizacion_plantilla.png)

### 2.4 Llenar los campos del tour

En la sección superior del formulario, completar los siguientes campos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Es un tour** | Marcar esta casilla para activar los campos de tour | ✓ |
| **Fecha de inicio** | Primer día del tour | 15/03/2026 |
| **Fecha de fin** | Último día del tour | 18/03/2026 |
| **Nro. de pasajeros** | Cantidad total de viajeros | 4 |
| **Tipo de servicio** | "Compartido" o "Privado" | Privado |
| **Ciudad de salida** | Desde dónde parten los clientes | Cusco |

![Captura 3: Campos de tour (es_tour, fechas, pasajeros, servicio)](screenshots/03_campos_tour.png)

> **Tip:** Si el tour es "Compartido", los pasajeros pueden agruparse con otros pedidos en un Grupo de Tour (ver sección 12).

---

## 3. Biblia Operativa: Itinerario

El itinerario es la tabla día por día que describe las actividades del tour.

### 3.1 Acceder al itinerario

1. En el formulario de la cotización, hacer clic en la pestaña **"Biblia Operativa"**
2. La primera sección es la tabla de **Itinerario**

### 3.2 Editar el itinerario

Si seleccionaste una plantilla, el itinerario ya viene pre-llenado. Puedes editarlo:

1. Hacer clic en cualquier celda para modificarla
2. Cada fila representa un día del tour con estos campos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Día** | Número del día | 1 |
| **Título** | Nombre de la actividad del día | "Llegada a Cusco - City Tour" |
| **Descripción** | Detalle de actividades | "Recojo del aeropuerto, aclimatación, visita a la Plaza de Armas..." |
| **Alojamiento** | Dónde duerme el pasajero | "Hotel Sonesta Cusco" |
| **Comidas** | Qué comidas están incluidas | "Desayuno, Almuerzo" |

### 3.3 Agregar un nuevo día

1. Hacer clic en **"Agregar línea"** al final de la tabla
2. Llenar los campos del nuevo día
3. El número de día se asigna automáticamente

### 3.4 Eliminar un día

1. Seleccionar la fila haciendo clic en la casilla de la izquierda
2. Hacer clic en el ícono de **eliminar** (papelera) o presionar la tecla **Suprimir**

![Captura 4: Pestaña Biblia Operativa - Itinerario](screenshots/04_biblia_itinerario.png)

> **Tip:** El itinerario se traduce automáticamente al inglés para clientes extranjeros. Si necesitas ajustar la traducción, contacta al administrador del sistema.

---

## 4. Biblia Operativa: Operadores

Los operadores son los proveedores/prestadores de servicio que participan en el tour (transportistas, guías, hoteles, restaurantes, etc.).

### 4.1 Acceder a la tabla de operadores

1. En la pestaña **"Biblia Operativa"**, desplazarse hacia abajo después del itinerario
2. La tabla de **Operadores** muestra todos los proveedores asignados

### 4.2 Agregar un operador

1. Hacer clic en **"Agregar línea"**
2. Llenar los campos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Proveedor** | Nombre del contacto/empresa proveedora | "Transportes Cusco SAC" |
| **Tipo de servicio** | Categoría del servicio | Transporte / Guía / Hotel / Restaurante / Tren / Coordinación / Otro |
| **Producto** | Servicio específico del catálogo (opcional) | "Transfer Aeropuerto - Hotel" |
| **Costo** | Costo estimado del servicio | 150.00 |
| **Moneda** | Moneda del costo | USD / PEN / EUR |

3. Los siguientes campos se llenan **automáticamente**:
   - **Teléfono** y **Email**: se cargan del contacto del proveedor
   - **Costo en PEN**: se convierte automáticamente usando el tipo de cambio del pedido
   - **OC** y **Estado OC**: se llenan cuando se generan las órdenes de compra (ver sección 10)

### 4.3 Auto-llenado del costo desde producto

Si seleccionas un **Producto** que tiene un costo estándar configurado, y el campo **Costo** está vacío, el sistema lo llena automáticamente con el precio de costo del producto.

### 4.4 Editar o eliminar un operador

- **Editar**: hacer clic en cualquier celda de la fila
- **Eliminar**: seleccionar la casilla de la izquierda y presionar Suprimir

![Captura 5: Pestaña Biblia Operativa - Operadores](screenshots/05_biblia_operadores.png)

> **Importante:** Una vez que se genera una Orden de Compra para un operador, el campo "OC" se llena automáticamente y ese operador no se volverá a incluir en futuras generaciones de OC.

---

## 5. Biblia Operativa: Inclusiones y Observaciones

### 5.1 Inclusiones

El campo **"Inclusiones"** es un editor de texto enriquecido (HTML) donde se detalla todo lo que incluye el paquete turístico:

- Transporte (tipo de vehículo, rutas)
- Alojamiento (hoteles, noches)
- Comidas (cuáles y dónde)
- Entradas a sitios turísticos
- Guía profesional
- Seguro de viaje

**Cómo editar:**
1. Hacer clic en el campo "Inclusiones"
2. Usar la barra de herramientas para dar formato (negrita, listas, etc.)
3. El texto viene pre-llenado desde la plantilla, ajustar según el tour personalizado

### 5.2 Tiempos Clave

El campo **"Tiempos Clave"** es un texto libre para anotar los horarios críticos:

Ejemplo:
```
- Pickup hotel: 05:30 AM
- Tren a Machu Picchu: 07:15 AM (Expedition)
- Retorno tren: 16:22 PM
- Llegada Cusco: ~20:00 PM
```

### 5.3 Observaciones Especiales

El campo **"Observaciones Especiales"** sirve para notas operativas internas:

Ejemplo:
```
- Cliente con alergia al gluten - coordinar menú especial
- Necesitan silla de ruedas en estación de tren
- Celebración de aniversario - coordinar sorpresa en hotel
```

![Captura 6: Campo Inclusiones (HTML)](screenshots/06_biblia_inclusiones.png)

---

## 6. Gestión de Pasajeros

### 6.1 Ver la lista de pasajeros

1. En el formulario de la cotización, hacer clic en la pestaña **"Pasajeros"**
2. Se muestra la lista de pasajeros asociados al pedido

### 6.2 Datos de cada pasajero

Los datos de los pasajeros se muestran en la tabla pero son **de solo lectura** (no se pueden editar directamente aquí). Los datos visibles son:

| Campo | Descripción |
|-------|-------------|
| **Nombre** | Nombre completo del pasajero |
| **Nacionalidad** | País de origen |
| **Tipo de documento** | Pasaporte, DNI, Carnet de Extranjería |
| **Nro. de documento** | Número del documento de identidad |
| **Fecha de nacimiento** | Para calcular edad y tarifas especiales |
| **Teléfono** | Número de contacto |
| **Email** | Correo electrónico |
| **Idioma** | Idioma preferido del pasajero |
| **Restricciones médicas** | Alergias, condiciones de salud, dietas especiales |
| **Contacto de emergencia** | Nombre y teléfono de la persona de emergencia |
| **Grupo** | Grupo de tour asignado (ver sección 12) |

### 6.3 Semáforo de verificación de identidad

Cada pasajero tiene un indicador de color que muestra si sus documentos están completos:

- **OK (verde):** Nacionalidad + tipo de documento + número de documento están completos
- **Incompleto (rojo):** Falta al menos uno de los tres datos obligatorios
- **Sin datos (amarillo):** No se ha ingresado ningún dato de identidad

### 6.4 Editar datos de un pasajero

Para editar los datos de un pasajero:

1. Hacer clic en el nombre del pasajero en la tabla
2. Se abre el formulario del **contacto** (res.partner)
3. Editar los campos necesarios (nacionalidad, documento, restricciones médicas, etc.)
4. **Guardar** el contacto
5. Los cambios se reflejan automáticamente en la cotización

![Captura 7: Pestaña Pasajeros con semáforo](screenshots/07_pasajeros_semaforo.png)

> **Importante:** Los datos de pasajeros se gestionan centralmente en el formulario de contacto. Si el mismo pasajero viaja en varios tours, sus datos se comparten automáticamente en todos los pedidos.

---

## 7. Costos y Margen

El sistema calcula automáticamente los indicadores financieros del tour:

### 7.1 Campos calculados

| Campo | Fórmula | Ejemplo |
|-------|---------|---------|
| **Costo total estimado** | Suma de todos los costos de operadores (en PEN) | S/ 3,500.00 |
| **Margen estimado** | Precio de venta total - Costo total estimado | S/ 1,500.00 |
| **% de margen** | (Margen / Precio de venta) × 100 | 30% |

### 7.2 Cómo interpretar los márgenes

- **Margen positivo (verde):** El tour genera ganancia
- **Margen negativo (rojo):** El tour genera pérdida — revisar costos o ajustar precio
- **Margen cercano a 0:** Evaluar si vale la pena operativamente

### 7.3 Ajustar precios

Para cambiar el precio de venta:
1. Ir a la pestaña **"Líneas de pedido"**
2. Editar el **Precio unitario** de cada línea
3. El margen se recalcula automáticamente

Para cambiar costos de operadores:
1. Ir a la pestaña **"Biblia Operativa"**
2. Editar el campo **Costo** de cada operador
3. El costo total y margen se recalculan automáticamente

![Captura 8: Costos y margen (campos calculados)](screenshots/08_costos_margen.png)

---

## 8. Enviar Cotización al Cliente

### 8.1 Enviar por email

1. Con la cotización abierta, hacer clic en **"Enviar por correo"** (botón en la barra de acciones)
2. Se abre un compositor de email con:
   - **Destinatario:** email del cliente (pre-llenado)
   - **Asunto:** "Cotización [número]" (pre-llenado)
   - **Cuerpo:** mensaje personalizable
   - **Adjunto:** PDF de la cotización (adjuntado automáticamente)
3. Editar el mensaje si es necesario
4. Hacer clic en **"Enviar"**

### 8.2 Qué recibe el cliente

El cliente recibe un email con:
- El PDF de la cotización adjunto
- Un **enlace al portal** donde puede:
  - Ver la cotización en línea
  - **Aprobar** directamente (firma electrónica)
  - Dejar comentarios o preguntas

### 8.3 Estado de la cotización

Después de enviar, la cotización cambia a estado **"Cotización enviada"**. Puedes ver si el cliente:
- Abrió el email
- Visitó el portal
- Firmó/aprobó la cotización

![Captura 9: Botón Enviar por correo](screenshots/09_enviar_correo.png)

---

## 9. Confirmar el Pedido

### 9.1 Cuándo confirmar

Confirmar el pedido cuando:
- El cliente ha aprobado la cotización (desde el portal o verbalmente)
- Se ha recibido el pago (total o anticipo según la política)

### 9.2 Cómo confirmar

1. Abrir la cotización
2. Hacer clic en el botón **"Confirmar"**
3. La cotización pasa a ser un **Pedido de Venta** (estado: "Pedido de venta")

### 9.3 Qué pasa automáticamente al confirmar

Al confirmar, el sistema crea automáticamente:

1. **Un Proyecto** llamado "[Nombre del tour] - [Cliente]"
   - Basado en la plantilla "Tour Estándar"
   - Visible en: **Proyecto** (menú principal)

2. **Tareas predefinidas** dentro del proyecto:

| Tarea | Propósito |
|-------|-----------|
| Confirmar Reservas | Verificar y confirmar reservas de hoteles, tickets, restaurantes |
| Coordinar Transporte | Organizar traslados, transfers, buses |
| Asignar Guía | Designar guía turístico para el grupo |
| Verificar Documentación | Revisar pasaportes, seguros, permisos |
| Seguimiento Post-Tour | Encuesta de satisfacción, feedback |

3. Las **fechas del tour** se copian automáticamente a las tareas

![Captura 10: Botón Confirmar pedido](screenshots/10_confirmar_pedido.png)
![Captura 11: Proyecto auto-creado con tareas](screenshots/11_proyecto_tareas.png)

> **Importante:** NO se puede desconfirmar un pedido fácilmente. Asegúrate de que todo esté correcto antes de confirmar.

---

## 10. Crear Órdenes de Compra desde Operadores

Una vez confirmado el pedido, puedes generar automáticamente las Órdenes de Compra (OC) para los proveedores listados en la Biblia Operativa.

### 10.1 Generar las OC

1. Abrir el pedido de venta confirmado
2. Ir a la pestaña **"Biblia Operativa"**
3. Desplazarse hasta el final de la sección de operadores
4. Hacer clic en el botón **"Crear OC desde Operadores"**
5. Confirmar en el diálogo que aparece

### 10.2 Qué pasa al generar las OC

- Se crea **una OC por cada proveedor** (si un proveedor tiene múltiples servicios, se agrupan en la misma OC)
- Cada línea de la OC contiene:
  - El producto "Servicio de Tour"
  - El costo del operador en PEN
  - Una descripción con el tipo de servicio y código del pedido
- Se publica un mensaje en el historial del pedido con los números de OC creadas

### 10.3 Ver el estado de las OC

Después de generar las OC:

- En la tabla de operadores, las columnas **"OC"** y **"Estado OC"** se llenan automáticamente
- Los estados posibles son:
  - **Borrador**: OC creada pero no enviada al proveedor
  - **Enviado**: OC enviada al proveedor
  - **Pedido de compra**: OC confirmada/aprobada

### 10.4 Acceder a las OC desde el pedido

- Hacer clic en el botón inteligente **"Compras"** (en la barra superior del pedido)
- Se abre la lista de todas las OC vinculadas a este pedido

![Captura 12: Botón "Crear OC desde Operadores"](screenshots/12_boton_crear_oc.png)
![Captura 13: Tabla operadores con estado OC](screenshots/13_operadores_estado_oc.png)
![Captura 14: Botón inteligente "Compras"](screenshots/14_boton_compras.png)

> **Nota:** Si agregas nuevos operadores después de haber generado las OC, puedes volver a hacer clic en "Crear OC desde Operadores". Solo se crearán OC para los operadores que aún no tengan una asignada.

---

## 11. Gestión de Flota (Vehículos)

### 11.1 Asignar un vehículo a una tarea

1. Ir a **Proyecto** y abrir el proyecto del tour
2. Abrir la tarea correspondiente (ej: "Coordinar Transporte")
3. Marcar la casilla **"Requiere vehículo propio"**
4. Se despliegan los campos de flota:

| Campo | Descripción |
|-------|-------------|
| **Vehículo** | Seleccionar el vehículo de la flota |
| **Conductor** | Seleccionar el conductor asignado |
| **Asientos necesarios** | Número de asientos que requiere este tour |

5. **Guardar** la tarea

### 11.2 Validaciones automáticas

Al asignar un vehículo, el sistema valida automáticamente:

- **Vehículo en mantenimiento:** Si el vehículo está en taller (servicio en estado "En proceso"), se muestra una **alerta** en el historial de la tarea
- **Conflicto de fechas:** Si el vehículo ya está asignado a otro tour en las mismas fechas, se muestra una advertencia
- **Tour privado:** Un tour privado no puede compartir vehículo con otros tours
- **Capacidad:** Si los asientos necesarios superan la capacidad disponible, se notifica

### 11.3 Asientos disponibles

El campo **"Asientos disponibles"** se calcula automáticamente:

```
Asientos disponibles = Capacidad del vehículo - Asientos de otros tours (mismas fechas) - Asientos de esta tarea
```

Si el resultado es negativo o cero, hay un problema de capacidad.

![Captura 15: Tarea con campos de flota](screenshots/15_tarea_flota.png)
![Captura 16: Alerta de conflicto de vehículo](screenshots/16_alerta_vehiculo.png)

> **Tip:** Solo los pedidos en estado "Pedido de venta" (confirmados) bloquean vehículos. Las cotizaciones en borrador y los pedidos cancelados no generan conflictos.

---

## 12. Grupos de Tour

Los Grupos de Tour sirven para organizar pasajeros de **tours compartidos** donde viajeros de diferentes pedidos comparten el mismo servicio.

### 12.1 Crear un grupo de tour

1. Ir a **Ventas > Pedidos > Grupos de Tour**
2. Hacer clic en **"Nuevo"**
3. Llenar los campos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Nombre** | Nombre descriptivo del grupo | "Cusco Cultural Feb 15-20" |
| **Fecha inicio** | Primer día del grupo | 15/02/2026 |
| **Fecha fin** | Último día del grupo | 20/02/2026 |
| **Capacidad máxima** | Máximo de pasajeros en el grupo | 16 |
| **Pasajeros** | Contactos asignados al grupo | (seleccionar de la lista) |
| **Notas** | Observaciones operativas | "Grupo bilingüe ES/EN" |

4. **Guardar**

### 12.2 Asignar un pedido a un grupo

1. Abrir el pedido de venta
2. En el campo **"Grupos de Tour"** (sección superior), seleccionar el grupo
3. Un pedido puede pertenecer a **múltiples grupos** si es necesario

### 12.3 Asignar pasajeros individuales a un grupo

1. En la pestaña **"Pasajeros"** del pedido
2. Cada pasajero tiene un campo **"Grupo"** donde puedes asignar el grupo específico

### 12.4 Casos de uso

- **Tour compartido:** Los pedidos S00050 y S00051 tienen pasajeros que comparten el mismo bus y guía → se asignan al mismo grupo
- **Tour privado:** Un grupo exclusivo para una familia → un solo pedido en el grupo
- **Grupo grande con división:** Un pedido con 40 personas → se dividen en Grupo A (20) y Grupo B (20) con vehículos separados

![Captura 17: Lista de Grupos de Tour](screenshots/17_grupos_tour_lista.png)
![Captura 18: Formulario Grupo de Tour](screenshots/18_grupo_tour_form.png)

---

## 13. Registro de Trabajo en Tareas

Cada tarea del proyecto tiene un sistema para registrar las horas trabajadas por los operadores.

### 13.1 Registrar trabajo

1. Abrir una tarea del proyecto
2. Ir a la pestaña **"Registro de Trabajo"**
3. Hacer clic en **"Agregar línea"**
4. Llenar los campos:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Operador** | Contacto que realizó el trabajo | "Juan Pérez (Guía)" |
| **Tipo de servicio** | Categoría del servicio | Guía |
| **Descripción** | Qué se realizó | "City Tour completo con grupo" |
| **Fecha** | Cuándo se realizó | 15/03/2026 |
| **Horas** | Duración en horas | 8.0 |

5. **Guardar**

### 13.2 Totales automáticos

En la parte superior del registro de trabajo se muestran tres indicadores:

| Indicador | Descripción |
|-----------|-------------|
| **Asignadas** | Horas planificadas para la tarea (configuradas en el campo "Horas asignadas") |
| **Registradas** | Total de horas registradas en el trabajo |
| **Restantes** | Asignadas - Registradas |

### 13.3 Notificaciones automáticas

Cada vez que se registra, edita o elimina una entrada de trabajo:
- Se publica un mensaje automático en el **historial** de la tarea
- El mensaje incluye el total actualizado de horas

![Captura 19: Registro de Trabajo en tarea](screenshots/19_registro_trabajo.png)

---

## 14. Reportes PDF

El sistema incluye dos reportes PDF imprimibles directamente desde el pedido de venta.

### 14.1 Biblia Operativa (PDF)

Contiene un resumen operativo completo del tour:
- Datos del tour (fechas, pasajeros, tipo de servicio)
- Itinerario completo
- Lista de operadores con contactos
- Inclusiones
- Tiempos clave
- Observaciones especiales

**Cómo imprimir:**
1. Abrir el pedido de venta
2. Hacer clic en **Imprimir > Biblia Operativa**
3. Se descarga el PDF

### 14.2 Voucher de Pasajero

Genera una página por cada pasajero con la información del tour para entregar al viajero:
- Nombre del pasajero y datos de contacto
- Itinerario resumido
- Información del hotel
- Contactos de emergencia de la agencia

**Cómo imprimir:**
1. Abrir el pedido de venta
2. Hacer clic en **Imprimir > Voucher Pasajero**
3. Se descarga el PDF con todas las páginas

![Captura 20: PDF Biblia Operativa (preview)](screenshots/20_pdf_biblia.png)
![Captura 21: PDF Voucher Pasajero (preview)](screenshots/21_pdf_voucher.png)

---

## 15. Plantillas de Cotización

Las plantillas de cotización permiten pre-configurar tours estándar para no tener que llenar todo desde cero cada vez.

### 15.1 Ver las plantillas existentes

1. Ir a **Ventas > Configuración > Plantillas de cotización**
2. Se muestra la lista de todas las plantillas disponibles

### 15.2 Qué contiene una plantilla

Cada plantilla incluye:
- **Líneas de productos**: Los productos/servicios que se incluyen en el tour
- **Biblia Operativa pre-configurada**:
  - Itinerario por defecto (día por día)
  - Operadores por defecto (proveedores habituales)
  - Inclusiones estándar
  - Tiempos clave típicos
  - Observaciones generales

### 15.3 Crear una nueva plantilla

1. Hacer clic en **"Nuevo"**
2. Dar un nombre descriptivo (ej: "Machu Picchu 2D/1N Tren Expedition")
3. En la pestaña **"Líneas"**, agregar los productos del tour
4. En la pestaña **"Biblia Operativa"**, llenar:
   - Itinerario estándar
   - Operadores habituales
   - Inclusiones típicas
5. **Guardar**

### 15.4 Modificar una plantilla existente

1. Abrir la plantilla desde la lista
2. Editar los campos necesarios
3. **Guardar**

> **Nota:** Modificar una plantilla NO afecta las cotizaciones que ya fueron creadas con esa plantilla. Solo afecta las cotizaciones nuevas.

![Captura 22: Lista de plantillas de cotización](screenshots/22_plantillas_lista.png)
![Captura 23: Formulario plantilla con Biblia](screenshots/23_plantilla_biblia.png)

---

## 16. Hoja de Referencia Rápida

### Acciones principales

| Acción | Ruta de menú | Campos clave |
|--------|-------------|--------------|
| Crear cotización de tour | Ventas > Cotizaciones > Nuevo | Cliente, Plantilla, Es un tour, Fechas, Pasajeros |
| Ver/editar itinerario | Cotización > tab Biblia Operativa | Día, Título, Descripción, Alojamiento, Comidas |
| Agregar operador | Cotización > tab Biblia > Operadores > Agregar línea | Proveedor, Tipo servicio, Costo, Moneda |
| Ver pasajeros | Cotización > tab Pasajeros | Nombre, Documento, Nacionalidad, Semáforo |
| Editar datos de pasajero | Click en nombre del pasajero → Formulario contacto | Nacionalidad, Documento, Restricciones médicas |
| Enviar cotización | Cotización > botón "Enviar por correo" | Destinatario, Mensaje, PDF adjunto |
| Confirmar pedido | Cotización > botón "Confirmar" | — (crea proyecto + tareas automáticamente) |
| Generar OC de operadores | Pedido > tab Biblia > "Crear OC desde Operadores" | — (crea 1 OC por proveedor) |
| Ver OC vinculadas | Pedido > botón inteligente "Compras" | Proveedor, Estado, Monto |
| Asignar vehículo | Proyecto > Tarea > "Requiere vehículo propio" | Vehículo, Conductor, Asientos |
| Crear grupo de tour | Ventas > Grupos de Tour > Nuevo | Nombre, Fechas, Capacidad, Pasajeros |
| Registrar trabajo | Proyecto > Tarea > tab "Registro de Trabajo" | Operador, Servicio, Fecha, Horas |
| Imprimir Biblia Operativa | Pedido > Imprimir > Biblia Operativa | — (descarga PDF) |
| Imprimir Voucher Pasajero | Pedido > Imprimir > Voucher Pasajero | — (descarga PDF) |
| Gestionar plantillas | Ventas > Configuración > Plantillas de cotización | Nombre, Líneas, Biblia Operativa |

### Atajos útiles

| Atajo | Acción |
|-------|--------|
| **F5** | Recargar página (útil después de seleccionar plantilla) |
| **Ctrl + S** | Guardar el formulario actual |
| **/** | Buscar en cualquier lista |

### Estados del pedido

```
Borrador → Cotización enviada → Pedido de venta → Bloqueado / Cancelado
```

### Semáforo de documentos del pasajero

| Color | Significado | Acción necesaria |
|-------|-------------|-----------------|
| Verde (OK) | Documentos completos | Ninguna |
| Rojo (Incompleto) | Falta documento o nacionalidad | Completar en ficha del contacto |
| Amarillo (Sin datos) | No se ha ingresado nada | Solicitar datos al pasajero |
