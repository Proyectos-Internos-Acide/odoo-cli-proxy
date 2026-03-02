# Guía de Gestión de Reservas y Ventas de Hospedaje

## Tabla de Contenidos

1. [Introducción: Flujo de Reservas](#1-introducción-flujo-de-reservas)
2. [Productos de Habitación](#2-productos-de-habitación)
3. [Crear una Reserva](#3-crear-una-reserva)
4. [Confirmar la Reserva](#4-confirmar-la-reserva)
5. [Ver Ocupación (Planificación)](#5-ver-ocupación-planificación)
6. [Gestión Operativa Diaria](#6-gestión-operativa-diaria)
7. [Configurar Nuevas Habitaciones](#7-configurar-nuevas-habitaciones)
8. [Hoja de Referencia Rápida](#8-hoja-de-referencia-rápida)

---

## 1. Introducción: Flujo de Reservas

El sistema de hospedaje funciona con un flujo de **alquiler** (rental) integrado con planificación:

```
PASO 1: Se crea una COTIZACIÓN con la habitación y las fechas
    ↓
PASO 2: Se ajustan los detalles (noches, servicios adicionales)
    ↓
PASO 3: Se envía la cotización al huésped (opcional)
    ↓
PASO 4: Se CONFIRMA la reserva
    ↓
PASO 5: El sistema crea automáticamente SLOTS DE PLANIFICACIÓN
         (calendario de ocupación de la habitación)
    ↓
PASO 6: El personal del hotel ve la ocupación en PLANIFICACIÓN
    ↓
PASO 7: Check-in → Estadía → Check-out
```

**Conceptos clave:**
- **Producto de habitación:** Cada habitación o tipo de habitación es un producto en el sistema
- **Slot de planificación:** Un bloque en el calendario que muestra cuándo una habitación está ocupada
- **Fechas de alquiler:** La fecha de check-in y check-out del huésped

---

## 2. Productos de Habitación

### 2.1 Ver las habitaciones disponibles

1. Ir a **Ventas > Productos**
2. Filtrar por categoría **"Apart./Hotel"** (usar la barra de búsqueda o filtros)
3. Se muestra la lista de todas las habitaciones/apartamentos

### 2.2 Información de cada habitación

Cada producto de habitación tiene:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Nombre** | Nombre de la habitación | "Suite Deluxe 301" |
| **Categoría** | Siempre "Apart./Hotel" | Apart./Hotel |
| **Precio** | Precio por noche | S/ 650.00 |
| **Hora de check-in** | Hora de recogida/ingreso | 12:00 (mediodía) |
| **Hora de check-out** | Hora de devolución/salida | 11:00 |

### 2.3 Atributos de la habitación

Cada habitación puede tener especificaciones que se muestran en la ficha del producto y en el sitio web:

| Atributo | Valores posibles | Ejemplo |
|----------|-----------------|---------|
| Camas | Individual, Doble, King, Queen | 1 King + 1 Individual |
| Baños | 1, 2, 3 | 2 |
| WiFi / Internet | Sí, No | Sí |
| TV Cable | Sí, No | Sí |
| Agua caliente | Sí, No | Sí |
| Estacionamiento | Privado, Compartido, No | Privado |
| Servicio a la habitación | Sí, No | Sí |
| Lavandería | Sí, No | Sí |
| Área | m² | 45 m² |

> **Nota:** Estos atributos son informativos (no crean variantes de producto). Se muestran en la página web de la habitación para que el cliente conozca las comodidades.

![Captura 1: Lista de productos de habitación](screenshots/h01_productos_habitacion.png)
![Captura 2: Formulario de producto habitación con atributos](screenshots/h02_producto_atributos.png)

---

## 3. Crear una Reserva

### 3.1 Nueva cotización de hospedaje

1. Ir a **Ventas > Pedidos > Cotizaciones**
2. Hacer clic en **"Nuevo"**
3. Seleccionar o crear el **Cliente** (el huésped)

### 3.2 Agregar la habitación

1. En la pestaña **"Líneas de pedido"**, hacer clic en **"Agregar un producto"**
2. Buscar el nombre de la habitación (ej: "Suite Deluxe 301")
3. Seleccionarla de la lista

### 3.3 Configurar las fechas

Al agregar un producto de alquiler (habitación), aparecen campos adicionales:

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| **Fecha de alquiler (inicio)** | Fecha de check-in | 15/03/2026 |
| **Fecha de devolución** | Fecha de check-out | 18/03/2026 |
| **Duración** | Se calcula automáticamente | 3 noches |

4. Seleccionar la **fecha de inicio** (check-in)
5. Seleccionar la **fecha de devolución** (check-out)
6. El sistema calcula automáticamente:
   - El número de **noches**
   - El **precio total** (precio por noche × noches)

### 3.4 Agregar servicios adicionales (opcional)

Puedes agregar servicios extras como líneas adicionales:
- Desayuno adicional
- Transfer aeropuerto
- Late check-out
- Servicio de lavandería

![Captura 3: Nueva cotización con habitación y fechas](screenshots/h03_cotizacion_habitacion.png)
![Captura 4: Campos de fecha de alquiler en línea de pedido](screenshots/h04_fechas_alquiler.png)

> **Tip:** Para reservas de múltiples habitaciones, simplemente agrega más líneas de producto con sus respectivas fechas.

---

## 4. Confirmar la Reserva

### 4.1 Cómo confirmar

1. Revisar que todos los datos estén correctos (habitación, fechas, precio)
2. Hacer clic en el botón **"Confirmar"**

### 4.2 Qué sucede al confirmar

Al confirmar la reserva, el sistema automáticamente:

1. **Crea slots de planificación** — Bloques en el calendario que marcan la habitación como ocupada
2. **Ajusta los horarios** — Las horas de check-in y check-out se configuran según el producto:
   - Check-in: 12:00 PM (mediodía) por defecto
   - Check-out: 11:00 AM por defecto
3. **Sincroniza las fechas** — Las fechas del pedido y la planificación quedan alineadas

### 4.3 Verificar la confirmación

Después de confirmar:
- El estado cambia a **"Pedido de venta"**
- Aparece un botón inteligente **"Planificación"** en la barra superior
- Hacer clic en "Planificación" para ver los slots creados

![Captura 5: Pedido confirmado con smart button planificación](screenshots/h05_pedido_confirmado.png)

---

## 5. Ver Ocupación (Planificación)

### 5.1 Acceder a la vista de planificación

1. Ir a **Planificación** (menú principal)
2. Seleccionar la vista **"Por Recurso"**
3. Se muestra un **diagrama de Gantt** con todas las habitaciones y sus ocupaciones

### 5.2 Interpretar la vista

- **Eje vertical (izquierda):** Lista de habitaciones/recursos
- **Eje horizontal (arriba):** Línea de tiempo (días, semanas, meses)
- **Bloques de color:** Cada bloque es una reserva confirmada
  - El bloque muestra: nombre del huésped, fechas
  - Hacer clic en un bloque para ver detalles

### 5.3 Filtrar y navegar

| Acción | Cómo hacerlo |
|--------|-------------|
| Cambiar período | Usar los botones "Día", "Semana", "Mes" en la barra superior |
| Avanzar/retroceder | Flechas ← → junto a la fecha |
| Ir a hoy | Botón "Hoy" |
| Filtrar habitación | Usar la barra de búsqueda o filtros |
| Ver detalle de reserva | Hacer clic en el bloque de color |

### 5.4 Detalle de un slot de planificación

Al hacer clic en un bloque, se abre un popup con:
- Habitación asignada
- Fecha y hora de inicio (check-in)
- Fecha y hora de fin (check-out)
- Horas asignadas
- Pedido de venta vinculado

![Captura 6: Vista Gantt de planificación](screenshots/h06_gantt_planificacion.png)
![Captura 7: Detalle de slot de planificación](screenshots/h07_detalle_slot.png)

> **Tip:** La vista de planificación es la forma más rápida de ver qué habitaciones están disponibles para una fecha específica. Busca los espacios vacíos en el diagrama.

---

## 6. Gestión Operativa Diaria

### 6.1 Check-ins del día

Para ver qué huéspedes llegan hoy:

1. Ir a **Planificación > Por Recurso**
2. Seleccionar vista **"Día"** y navegar a la fecha de hoy
3. Los bloques que **empiezan hoy** son los check-ins del día
4. Verificar:
   - Habitación lista y limpia
   - Documentos del huésped verificados
   - Servicios especiales preparados (si aplica)

### 6.2 Check-outs del día

Para ver qué huéspedes se van hoy:

1. En la misma vista de planificación
2. Los bloques que **terminan hoy** son los check-outs del día
3. Coordinar:
   - Hora de salida
   - Inspección de habitación
   - Cobros pendientes
   - Programar limpieza

### 6.3 Coordinación de limpieza

Después de cada check-out:

1. Verificar en la planificación si hay un nuevo check-in para la misma habitación
2. Si hay check-in el mismo día: priorizar la limpieza de esa habitación
3. Si no hay check-in inmediato: programar limpieza en horario normal

> **Nota:** El sistema muestra las horas de check-in (12:00) y check-out (11:00), lo que da 1 hora de margen para preparar la habitación entre huéspedes.

---

## 7. Configurar Nuevas Habitaciones

### 7.1 Crear un nuevo producto de habitación

1. Ir a **Ventas > Productos**
2. Hacer clic en **"Nuevo"**
3. Llenar los campos básicos:

| Campo | Valor | Notas |
|-------|-------|-------|
| **Nombre** | Nombre de la habitación | Ej: "Habitación Estándar 102" |
| **Tipo** | Servicio | Siempre "Servicio" para habitaciones |
| **Categoría** | Apart./Hotel | Seleccionar de la lista |
| **Precio de venta** | Precio por noche | Ej: S/ 350.00 |
| **Es una oferta de habitación** | ✓ Marcar | Activa la integración con planificación |

### 7.2 Configurar horarios de alquiler

En la sección de alquiler del producto:

| Campo | Valor recomendado | Descripción |
|-------|-------------------|-------------|
| **Hora de recogida** | 12.0 | Check-in a las 12:00 PM |
| **Hora de devolución** | 11.0 | Check-out a las 11:00 AM |

> **Nota:** Los horarios se expresan en formato decimal. 12.0 = 12:00 PM, 11.5 = 11:30 AM, 14.0 = 2:00 PM.

### 7.3 Agregar atributos (especificaciones)

1. Ir a la pestaña **"Atributos y Variantes"**
2. Hacer clic en **"Agregar línea"**
3. Seleccionar un atributo existente (ej: "Camas", "Baños", "WiFi")
4. Seleccionar el valor correspondiente
5. Repetir para cada atributo que aplique

### 7.4 Publicar en la web (opcional)

1. En la parte superior del formulario, activar el toggle **"Publicado"**
2. O ir a la pestaña **"Ventas"** y marcar **"Publicado en el sitio web"**
3. Agregar fotos en la pestaña correspondiente

![Captura 8: Formulario crear nuevo producto habitación](screenshots/h08_nuevo_producto_habitacion.png)

---

## 8. Hoja de Referencia Rápida

### Acciones principales

| Acción | Ruta de menú | Campos clave |
|--------|-------------|--------------|
| Ver habitaciones | Ventas > Productos (filtro Apart./Hotel) | Nombre, Precio, Atributos |
| Crear reserva | Ventas > Cotizaciones > Nuevo | Cliente, Habitación, Fechas alquiler |
| Confirmar reserva | Cotización > botón "Confirmar" | — (crea slots automáticamente) |
| Ver ocupación | Planificación > Por Recurso | Vista Gantt de habitaciones |
| Ver check-ins del día | Planificación > vista "Día" > fecha hoy | Bloques que empiezan hoy |
| Ver check-outs del día | Planificación > vista "Día" > fecha hoy | Bloques que terminan hoy |
| Crear habitación nueva | Ventas > Productos > Nuevo | Nombre, Categoría, Precio, Horarios |

### Horarios estándar

| Concepto | Hora | Formato decimal |
|----------|------|----------------|
| Check-in | 12:00 PM | 12.0 |
| Check-out | 11:00 AM | 11.0 |
| Margen limpieza | 1 hora | — |

### Estados de la reserva

```
Borrador → Cotización enviada → Pedido de venta (confirmado) → Bloqueado / Cancelado
```

### Vista de planificación

| Elemento | Significado |
|----------|-------------|
| Bloque de color | Habitación ocupada (reserva confirmada) |
| Espacio vacío | Habitación disponible |
| Inicio del bloque | Fecha y hora de check-in |
| Fin del bloque | Fecha y hora de check-out |

### Formato de horarios decimales

| Decimal | Hora |
|---------|------|
| 8.0 | 8:00 AM |
| 8.5 | 8:30 AM |
| 11.0 | 11:00 AM |
| 12.0 | 12:00 PM |
| 14.0 | 2:00 PM |
| 18.0 | 6:00 PM |
