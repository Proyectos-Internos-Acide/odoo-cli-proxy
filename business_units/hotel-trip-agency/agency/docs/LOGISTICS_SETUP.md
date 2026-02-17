# Logistica y Transporte para Agencia de Viajes

## Estrategia Hibrida: Vehiculos Propios + Tercerizados

La agencia opera con dos tipos de transporte:
1. **Vehiculos propios**: Gestionados con el modulo Fleet
2. **Vehiculos tercerizados**: Gestionados con ordenes de compra (Purchase)

---

## 1. Vehiculos Propios (Fleet)

### Registro
- **Donde**: Flotilla > Vehiculos > Crear
- **Campos clave**: Marca, Modelo, Placa, Conductor asignado, Fecha de compra

### Mantenimiento
- Registrar mantenimiento preventivo y correctivo
- Alertas automaticas por fecha o kilometraje
- Historial completo por vehiculo

### Combustible
- Registrar cargas de combustible
- Control de consumo por vehiculo
- Imputar gastos de combustible a la cuenta analitica del tour

### Tipos de Servicio
Creados por `setup_fleet_automations.py` en Flotilla > Configuracion > Tipos de servicio:

| Tipo | Categoria |
|------|-----------|
| Cambio de aceite | Servicio (puntual) |
| Revision tecnica | Servicio |
| Lavado | Servicio |
| Reparacion general | Servicio |
| Cambio de llantas | Servicio |
| SOAT | Contrato (recurrente) |
| Seguro vehicular | Contrato |

### Asignacion a Tours
La asignacion se hace desde la tarea del proyecto marcando "Requiere vehiculo propio":

1. En el Proyecto del tour, abrir la tarea de transporte
2. Marcar checkbox **"Requiere vehiculo propio"**
3. Seleccionar vehiculo y chofer
4. La automatizacion valida conflictos de fechas, capacidad y estado de servicio
5. Registrar los gastos de combustible como Expenses contra la cuenta analitica

---

## 2. Vehiculos Tercerizados (Purchase)

### Producto de compra
**"Servicio de Transporte Externo"** (ya creado):
- Tipo: Servicio
- Solo compra (sale_ok=False, purchase_ok=True)
- Categoria: Services

### Flujo

1. Desde la tarea del proyecto "2. Coordinar Transporte"
2. Crear **Orden de Compra** al proveedor de transporte
3. Agregar producto "Servicio de Transporte Externo"
4. **Vincular a la cuenta analitica** del proyecto del tour
5. Confirmar la compra
6. Registrar la factura del proveedor

### Proveedores
Registrar proveedores de transporte en Compras > Proveedores:
- Nombre de la empresa
- Contacto
- Condiciones de pago
- Precios habituales (se pueden registrar como listas de precios de proveedor)

---

## 3. Comparativa

| Aspecto | Vehiculo Propio (Fleet) | Tercerizado (Purchase) |
|---------|------------------------|----------------------|
| Registro | Modulo Fleet | Orden de Compra |
| Costo fijo | Si (depreciacion, seguro) | No |
| Costo variable | Combustible, mantenimiento | Por servicio |
| Control | Total | Limitado |
| Asignacion | Manual en tarea del proyecto | OC vinculada a analitica |
| Escalabilidad | Limitada | Alta |
| Rentabilidad | Via Fleet + Expenses | Via Purchase + Analitica |

---

## 4. Cuenta Analitica

Ambos tipos de gasto se imputan a la **cuenta analitica del proyecto** del tour:

- **Combustible vehiculo propio**: Expense > vinculado a cuenta analitica
- **Servicio transporte externo**: Purchase > vinculado a cuenta analitica
- **Resultado**: Se puede medir el costo total de transporte por tour

### Ver rentabilidad
Ir a **Contabilidad > Reportes > Analitica** para ver costos vs ingresos por proyecto/tour.

---

## 5. Validacion Cruzada Fleet ↔ Tours

Las automatizaciones garantizan coherencia entre el estado de mantenimiento de los vehiculos y su asignacion a tours.

### Direccion 1: Vehiculo en taller → bloquea asignacion a tour

Cuando un usuario intenta asignar un vehiculo a una tarea de tour (via `x_vehicle_id`), la automatizacion **Warn Vehicle Date Conflict** verifica:
1. Conflictos con otros tours (fechas, capacidad, tours privados)
2. **Servicios en proceso**: busca en `fleet.vehicle.log.services` cualquier registro con estado "En proceso" para ese vehiculo

Si el vehiculo tiene un servicio en estado "En proceso":
- **Accion**: BLOQUEA la asignacion con UserError
- **Mensaje**: Lista los servicios en proceso con fecha y descripcion
- **Solucion**: Completar o cancelar el servicio en Flotilla antes de asignar

### Direccion 2: Vehiculo en tour → advertencia al entrar a taller

Cuando un servicio de mantenimiento cambia a estado "En proceso" (o se crea directamente en ese estado), la automatizacion **Warn Tour on Fleet Service State** verifica:
1. Busca tareas de proyecto con ese vehiculo asignado
2. Solo considera tours con SO confirmado (`state='sale'`) y fecha fin futura

Si el vehiculo tiene tours activos:
- **Accion**: Publica ADVERTENCIA en el chatter del servicio (NO bloquea)
- **Mensaje**: Lista los tours afectados con fechas y asientos
- **Razon**: No bloquea porque podria necesitarse reparacion de emergencia

### Resumen de validaciones

| Situacion | Accion | Tipo |
|-----------|--------|------|
| Asignar vehiculo en taller a tour | BLOQUEA | UserError |
| Asignar vehiculo con conflicto de fechas | BLOQUEA/ADVIERTE | Depende de capacidad |
| Asignar vehiculo reservado para privado | BLOQUEA | UserError |
| Vehiculo en tour entra a taller | ADVIERTE | Chatter message |
