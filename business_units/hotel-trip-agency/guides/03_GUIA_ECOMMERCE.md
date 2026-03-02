# Guía de Gestión y Personalización del E-commerce

## Tabla de Contenidos

1. [Introducción: Cómo Funciona la Tienda Online](#1-introducción-cómo-funciona-la-tienda-online)
2. [Gestionar Productos en la Web](#2-gestionar-productos-en-la-web)
3. [Precios y Monedas](#3-precios-y-monedas)
4. [Comisiones de Métodos de Pago](#4-comisiones-de-métodos-de-pago)
5. [Livechat con IA](#5-livechat-con-ia)
6. [WhatsApp: Plantillas de Auto-respuesta](#6-whatsapp-plantillas-de-auto-respuesta)
7. [Personalización Básica del Sitio Web](#7-personalización-básica-del-sitio-web)
8. [Hoja de Referencia Rápida](#8-hoja-de-referencia-rápida)

---

## 1. Introducción: Cómo Funciona la Tienda Online

La tienda online de A y F Destiny tiene dos tipos de productos con comportamientos diferentes:

### Tours y paquetes turísticos

Los tours **NO se venden directamente** por la web. En lugar de un botón "Agregar al carrito", el visitante ve un botón **"Solicitar Cotización"** que abre un formulario:

```
Visitante ve el tour en la web
    ↓
Hace clic en "Solicitar Cotización"
    ↓
Llena formulario: nombre, email, teléfono, mensaje
    ↓
Se crea automáticamente un LEAD en el CRM
    ↓
Un asesor contacta al cliente y crea la cotización manualmente
```

Esto es así porque cada tour se personaliza según el cliente (fechas, número de personas, servicios adicionales, etc.).

### Habitaciones de hotel

Las habitaciones se pueden reservar directamente desde el sitio web con selección de fechas y pago en línea.

### Precios según el idioma

- Visitantes en **español**: ven precios en **Soles (S/)**
- Visitantes en **inglés**: ven precios en **Dólares ($)**

El cambio es automático cuando el visitante cambia el idioma del sitio.

---

## 2. Gestionar Productos en la Web

### 2.1 Publicar o despublicar un producto

Para que un producto aparezca (o desaparezca) de la tienda online:

1. Ir a **Ventas > Productos**
2. Abrir el producto que quieres modificar
3. En la esquina superior derecha, buscar el interruptor **"Publicado"**
   - **Activado (verde):** El producto es visible en la web
   - **Desactivado (gris):** El producto NO aparece en la web
4. Hacer clic para cambiar el estado

> **Importante:** Despublicar un producto NO elimina las cotizaciones o pedidos existentes. Solo lo oculta de la tienda online.

### 2.2 Editar información del producto

Para cambiar la información que el cliente ve en la web:

1. Abrir el producto en **Ventas > Productos**
2. Editar los campos:

| Campo | Dónde se ve | Ejemplo |
|-------|------------|---------|
| **Nombre** | Título del producto en la web | "City Tour Cusco" |
| **Precio de venta** | Precio mostrado (en Soles) | S/ 150.00 |
| **Descripción e-commerce** | Texto corto debajo del título | "Descubre la mágica ciudad imperial..." |
| **Descripción extendida** | Texto completo en la página del producto | Itinerario detallado, incluye/no incluye |

3. Para las fotos: ir a la sección de **imágenes** del producto y subir/reemplazar

### 2.3 Categorías del sitio web

Los productos se organizan en categorías que el visitante puede filtrar:

1. Ir a **Sitio Web > E-commerce > Categorías del e-commerce**
2. Las categorías principales son:
   - **Tours** (todos los tours y paquetes)
   - **Hospedaje** (habitaciones de hotel)
3. Para cambiar la categoría web de un producto:
   - Abrir el producto
   - En el campo **"Categorías del sitio web"**, agregar o quitar categorías

### 2.4 Productos relacionados (venta cruzada)

Los "productos relacionados" son las sugerencias que aparecen debajo de cada producto en la web ("También te puede interesar..."):

1. Abrir el producto en **Ventas > Productos**
2. Ir a la pestaña **"Ventas"**
3. En el campo **"Productos opcionales"**, agregar los productos que quieres sugerir
4. **Guardar**

**Ejemplo:** En la página del "City Tour Cusco" se sugieren:
- Valle Sagrado Tradicional
- Rainbow Mountain
- Chinchero, Moray y Maras

![Captura 1: Página de producto tour en el sitio web](screenshots/e01_producto_web.png)
![Captura 2: Modal de solicitud de cotización](screenshots/e02_modal_cotizacion.png)
![Captura 3: Listado de productos en tienda](screenshots/e03_listado_tienda.png)
![Captura 14: Productos relacionados en el backend](screenshots/e14_productos_relacionados.png)

---

## 3. Precios y Monedas

### 3.1 Cómo funciona el sistema de precios

El sistema usa **listas de precios** para mostrar precios en diferentes monedas:

| Idioma del visitante | Moneda | Lista de precios |
|---------------------|--------|-----------------|
| Español | Soles (S/) | PEN (por defecto) |
| Inglés | Dólares ($) | USD |

El cambio es **automático**: cuando un visitante cambia el idioma del sitio de español a inglés (o viceversa), los precios se convierten automáticamente.

### 3.2 Dónde ver las listas de precios

1. Ir a **Ventas > Configuración > Listas de precios**
2. Verás dos listas principales:
   - **PEN** (lista por defecto): Precios base en Soles peruanos
   - **USD**: Precios convertidos a Dólares americanos

### 3.3 Cómo funciona la conversión automática

La lista USD tiene una **regla global de conversión**:
- Toma el precio base en PEN
- Lo convierte a USD usando el **tipo de cambio** configurado en el sistema
- El tipo de cambio se actualiza en: **Contabilidad > Configuración > Monedas**

**Ejemplo:**
- Precio base del City Tour: S/ 500.00 PEN
- Tipo de cambio: 1 USD = 3.75 PEN
- Precio en USD: $133.33 (500 ÷ 3.75)

### 3.4 Poner un precio manual en USD

Si quieres que un producto tenga un precio específico en USD (en lugar de la conversión automática):

1. Ir a **Ventas > Configuración > Listas de precios**
2. Abrir la lista **"USD"**
3. En la sección de reglas, hacer clic en **"Agregar línea"**
4. Configurar:

| Campo | Valor |
|-------|-------|
| **Aplicar en** | 1 Producto |
| **Producto** | (seleccionar el producto) |
| **Calcular precio** | Precio fijo |
| **Precio fijo** | (escribir el precio en USD) |

5. **Guardar**

**Ejemplo:** Si quieres que el "Machu Picchu 2D/1N" cueste exactamente $450 USD (en lugar del precio convertido):
- Aplicar en: 1 Producto → "Machu Picchu 2D/1N"
- Calcular precio: Precio fijo
- Precio fijo: 450.00

> **Nota:** Las reglas de precio fijo para un producto específico siempre tienen prioridad sobre la regla de conversión general.

### 3.5 Actualizar el tipo de cambio

1. Ir a **Contabilidad > Configuración > Monedas**
2. Buscar **USD (Dólar americano)**
3. Hacer clic en la moneda
4. En la pestaña de tasas, puedes:
   - Ver el tipo de cambio actual
   - Agregar un nuevo tipo de cambio con la fecha de hoy

![Captura 4: Lista de precios en backend](screenshots/e04_listas_precios.png)
![Captura 5: Regla de conversión USD](screenshots/e05_regla_conversion.png)
![Captura 6: Tipo de cambio](screenshots/e06_tipo_cambio.png)
![Captura 7: Precio manual para un producto](screenshots/e07_precio_manual.png)

---

## 4. Comisiones de Métodos de Pago

### 4.1 Qué es una comisión de pasarela de pago

Cuando un cliente paga por internet (Mercado Pago, PayPal, tarjeta de crédito), la empresa que procesa el pago **cobra una comisión** por el servicio. Esta comisión se descuenta del monto que recibes en tu cuenta bancaria.

**Punto clave:** La comisión NO la paga el cliente. El cliente siempre paga el precio completo. Es la pasarela de pago la que retiene un porcentaje antes de depositarte el dinero.

### 4.2 Ejemplo con Mercado Pago (comisión 3.49%)

Supongamos que vendes un tour de **$500.00 USD**:

```
┌─────────────────────────────────────────────────┐
│  LO QUE PAGA EL CLIENTE                        │
│  ─────────────────────                          │
│  Precio del tour:              $500.00          │
│  El cliente paga:              $500.00          │
│                                                 │
│  LO QUE RECIBES EN TU CUENTA BANCARIA          │
│  ────────────────────────────────                │
│  Monto pagado:                 $500.00          │
│  Comisión Mercado Pago (3.49%): -$17.45         │
│  ─────────────────────────────                  │
│  Deposito en tu cuenta:        $482.55          │
│                                                 │
│  EN ODOO                                        │
│  ───────                                        │
│  Factura al cliente:           $500.00          │
│  Pago registrado:              $500.00          │
│  Depósito real en banco:       $482.55          │
│  Diferencia (comisión):         $17.45          │
│                                                 │
│  → La diferencia de $17.45 aparece como         │
│    "gasto bancario" o "comisión financiera"     │
│    al CONCILIAR el extracto bancario            │
└─────────────────────────────────────────────────┘
```

### 4.3 Ejemplo con PayPal (comisión 4.4% + $0.30)

Supongamos el mismo tour de **$500.00 USD**:

```
┌─────────────────────────────────────────────────┐
│  LO QUE PAGA EL CLIENTE                        │
│  ─────────────────────                          │
│  Precio del tour:              $500.00          │
│  El cliente paga:              $500.00          │
│                                                 │
│  LO QUE RECIBES EN TU CUENTA BANCARIA          │
│  ────────────────────────────────                │
│  Monto pagado:                 $500.00          │
│  Comisión PayPal (4.4%):        -$22.00         │
│  Tarifa fija PayPal:             -$0.30         │
│  ─────────────────────────────                  │
│  Deposito en tu cuenta:        $477.70          │
│                                                 │
│  EN ODOO                                        │
│  ───────                                        │
│  Factura al cliente:           $500.00          │
│  Pago registrado:              $500.00          │
│  Depósito real en banco:       $477.70          │
│  Diferencia (comisión):         $22.30          │
│                                                 │
│  → La diferencia de $22.30 aparece como         │
│    "gasto bancario" al conciliar                │
└─────────────────────────────────────────────────┘
```

### 4.4 Tabla comparativa de comisiones

| Método de pago | Comisión | Tour de $500 | Tour de $1,000 | Tour de $200 |
|---------------|----------|-------------|----------------|-------------|
| **Mercado Pago** | 3.49% | $17.45 | $34.90 | $6.98 |
| **PayPal** | 4.4% + $0.30 | $22.30 | $44.30 | $9.10 |
| **Transferencia bancaria** | ~$0 | $0 | $0 | $0 |
| **Efectivo** | $0 | $0 | $0 | $0 |

> **Tip:** Las transferencias bancarias y pagos en efectivo no tienen comisión. Para ventas grandes, puedes sugerir al cliente pagar por transferencia.

### 4.5 Dónde se registra la comisión en Odoo

La comisión NO se registra manualmente. Aparece automáticamente durante la **conciliación bancaria**:

1. Ir a **Contabilidad > Banco > Conciliación**
2. Cuando importas o sincronizas el extracto bancario:
   - Odoo muestra el pago registrado ($500.00)
   - El extracto bancario muestra el depósito real ($482.55)
   - La diferencia ($17.45) se propone como **"Gasto bancario"** o **"Comisión financiera"**
3. Aceptar la conciliación → la comisión queda registrada como gasto

### 4.6 Importante sobre las comisiones

- **NO modificar el precio de la factura** por la comisión. La factura siempre es por el monto total ($500)
- **NO registrar el pago por el monto neto** ($482.55). El pago siempre se registra por $500
- La comisión se maneja **exclusivamente en la conciliación bancaria**
- Las comisiones son un **gasto deducible** del negocio

![Captura 8: Conciliación bancaria mostrando comisión](screenshots/e08_conciliacion_comision.png)

---

## 5. Livechat con IA

### 5.1 Qué es el Livechat con IA

Es un chatbot inteligente que aparece en la esquina inferior derecha del sitio web. Utiliza inteligencia artificial para:

- Responder preguntas sobre los tours disponibles
- Recomendar tours según las preferencias del visitante
- Crear automáticamente leads en el CRM cuando el visitante quiere cotizar

### 5.2 Cómo funciona para el visitante

1. El visitante entra al sitio web
2. Después de 15 segundos, aparece una burbuja de chat: **"Chatea con nosotros"**
3. El visitante escribe su consulta
4. El chatbot responde con información de los tours, precios y detalles
5. Si el visitante quiere cotizar, el chatbot le pide nombre, email y teléfono
6. Se crea automáticamente un lead en el CRM

### 5.3 Configurar el Livechat

1. Ir a **Sitio Web > Livechat > Canales**
2. Abrir el canal **"A y F Destiny - Asistente de Tours"**

Desde aquí puedes:

| Configuración | Dónde | Descripción |
|--------------|-------|-------------|
| Nombre del canal | Pestaña principal | Nombre interno del chat |
| Texto del botón | Sección "Apariencia" | Texto que ve el visitante (ej: "Chatea con nosotros") |
| Color del botón | Sección "Apariencia" | Color de la burbuja de chat |
| Mensaje de bienvenida | Sección "Apariencia" | Primer mensaje que ve el visitante |
| Tiempo de aparición | Regla del canal | Segundos antes de que aparezca el chat (default: 15) |

### 5.4 Ver las conversaciones

Para ver las conversaciones que ha tenido el chatbot con los visitantes:

1. Ir a **Conversaciones** (menú principal)
2. Buscar los canales de livechat
3. Cada conversación muestra:
   - Mensajes del visitante y respuestas del chatbot
   - Si se creó un lead (aparece como nota interna)

![Captura 9: Canal de Livechat](screenshots/e09_canal_livechat.png)
![Captura 10: Conversación de Livechat con IA](screenshots/e10_conversacion_livechat.png)

---

## 6. WhatsApp: Plantillas de Auto-respuesta

### 6.1 Cómo funciona

Cuando un cliente envía un mensaje por WhatsApp al número de la agencia (+51 987 318 885), el sistema responde automáticamente con un menú de opciones:

```
¡Hola! Bienvenido a A y F Destiny. ¿En qué podemos ayudarte?

Escribe el número de la opción que desees:
1 - Información sobre nuestros tours
2 - Solicitar una cotización
3 - Estado de mi reserva
4 - Hablar con un asesor
5 - Recomendar un tour según mis preferencias
```

El cliente responde con un número y recibe la respuesta correspondiente.

### 6.2 Ver las plantillas de auto-respuesta

1. Ir a **Marketing > WhatsApp > Plantillas**
2. En la barra de búsqueda, escribir **"Auto:"** para filtrar solo las plantillas de auto-respuesta
3. Las plantillas disponibles son:

| Plantilla | Keyword | Qué hace |
|-----------|---------|----------|
| Auto: Bienvenida | (primer mensaje) | Saludo inicial con menú de opciones |
| Auto: Info Tours | 1 | Información general sobre los tours |
| Auto: Cotización | 2 | Instrucciones para solicitar cotización |
| Auto: Estado Reserva | 3 | Cómo consultar estado de reserva |
| Auto: Hablar con Asesor | 4 | Mensaje que un asesor se comunicará pronto |
| Auto: Recomendar Tour | 5 | Inicia el flujo de recomendación inteligente |

### 6.3 Editar una plantilla

1. Abrir la plantilla desde la lista
2. Editar el campo **"Cuerpo"** (texto en español)
3. Si existe el campo **"Cuerpo en inglés"**, editar también la versión en inglés
4. **Guardar**

> **Nota:** El sistema detecta automáticamente el idioma del cliente según su número de teléfono (prefijo del país) y envía la versión correspondiente.

### 6.4 Agregar o cambiar keywords

Para cambiar qué número activa cada respuesta:

1. Abrir la plantilla
2. En el campo **"Keywords"**, escribir el nuevo número o palabra
3. Se pueden poner múltiples keywords separadas por comas (ej: "1, tours, info")
4. **Guardar**

### 6.5 Flujo de recomendación inteligente (keyword "5")

Cuando el cliente escribe "5":

1. El sistema le pide que describa sus preferencias (duración, intereses, presupuesto)
2. El cliente responde con texto libre
3. El sistema busca en el catálogo de tours publicados
4. Recomienda los 3 tours más relevantes con nombre, precio y descripción
5. Se publica una nota interna en la conversación con los detalles completos

![Captura 11: Plantillas WhatsApp (lista filtrada "Auto:")](screenshots/e11_plantillas_whatsapp.png)
![Captura 12: Formulario de plantilla WhatsApp](screenshots/e12_plantilla_whatsapp_form.png)

---

## 7. Personalización Básica del Sitio Web

### 7.1 Acceder al editor web

1. Ir a **Sitio Web** (menú principal)
2. Navegar a la página que quieres editar
3. Hacer clic en **"Editar"** (botón en la esquina superior derecha)
4. Se activa el modo de edición

### 7.2 Editar textos

1. En modo de edición, hacer clic directamente sobre cualquier texto
2. Escribir o modificar el contenido
3. Usar la barra de herramientas flotante para:
   - Cambiar el estilo (título, subtítulo, párrafo)
   - Aplicar negrita, cursiva, subrayado
   - Crear listas
   - Agregar enlaces

### 7.3 Cambiar imágenes

1. En modo de edición, hacer clic sobre la imagen que quieres cambiar
2. Aparece un menú con opciones:
   - **Reemplazar:** Subir una nueva imagen o elegir del media library
   - **Recortar:** Ajustar el encuadre
   - **Eliminar:** Quitar la imagen

### 7.4 Agregar bloques de contenido (Snippets)

1. En modo de edición, buscar el panel de **snippets** (generalmente a la derecha o abajo)
2. Arrastrar un bloque al lugar deseado en la página
3. Los bloques disponibles incluyen:
   - Texto con imagen
   - Galería de fotos
   - Testimonios
   - Llamada a la acción (CTA)
   - Mapa
   - Formulario de contacto

### 7.5 Guardar los cambios

1. Después de editar, hacer clic en **"Guardar"** (botón verde, esquina superior derecha)
2. Los cambios se publican inmediatamente en el sitio

> **Importante:** Los cambios en el editor web son inmediatos y públicos. Asegúrate de revisar bien antes de guardar.

![Captura 13: Editor web frontend](screenshots/e13_editor_web.png)

---

## 8. Hoja de Referencia Rápida

### Gestión de productos web

| Acción | Ruta de menú | Qué hacer |
|--------|-------------|-----------|
| Publicar/despublicar producto | Ventas > Productos > [producto] | Toggle "Publicado" |
| Editar descripción web | Ventas > Productos > [producto] | Editar "Descripción e-commerce" |
| Cambiar precio base (PEN) | Ventas > Productos > [producto] | Editar "Precio de venta" |
| Poner precio fijo USD | Ventas > Configuración > Listas de precios > USD | Agregar regla con precio fijo |
| Productos sugeridos | Ventas > Productos > [producto] > tab Ventas | Editar "Productos opcionales" |
| Cambiar fotos | Ventas > Productos > [producto] | Sección de imágenes |

### Precios y monedas

| Acción | Ruta de menú |
|--------|-------------|
| Ver listas de precios | Ventas > Configuración > Listas de precios |
| Actualizar tipo de cambio | Contabilidad > Configuración > Monedas > USD |
| Agregar precio manual USD | Listas de precios > USD > Agregar regla |

### Comisiones - Resumen

| Pasarela | Comisión | Tour $500 | Recibes |
|----------|----------|-----------|---------|
| Mercado Pago | 3.49% | $17.45 | $482.55 |
| PayPal | 4.4% + $0.30 | $22.30 | $477.70 |
| Transferencia | ~$0 | $0 | $500.00 |
| Efectivo | $0 | $0 | $500.00 |

**Regla de oro:** La factura siempre es por el monto total. La comisión se registra en la conciliación bancaria.

### Comunicación con clientes

| Canal | Configuración | Ver conversaciones |
|-------|--------------|-------------------|
| Livechat (IA) | Sitio Web > Livechat > Canales | Conversaciones > Canales livechat |
| WhatsApp | Marketing > WhatsApp > Plantillas | Conversaciones > WhatsApp |

### WhatsApp - Keywords de auto-respuesta

| Keyword | Respuesta |
|---------|-----------|
| (primer mensaje) | Bienvenida + menú |
| 1 | Info de tours |
| 2 | Solicitar cotización |
| 3 | Estado de reserva |
| 4 | Contactar asesor |
| 5 | Recomendación inteligente |

### Editor web

| Acción | Cómo |
|--------|------|
| Abrir editor | Sitio Web > navegar a la página > "Editar" |
| Editar texto | Clic sobre el texto > escribir |
| Cambiar imagen | Clic sobre la imagen > "Reemplazar" |
| Agregar bloque | Arrastrar snippet al lugar deseado |
| Guardar | Botón "Guardar" (verde, esquina superior) |
