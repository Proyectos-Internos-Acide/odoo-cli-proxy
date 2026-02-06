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

### Asignacion a Tours
La asignacion de vehiculos propios a tours **no es automatica**. Se hace manualmente:

1. En el Proyecto del tour, abrir tarea "2. Coordinar Transporte"
2. Indicar en la descripcion que vehiculo se asigna
3. Registrar los gastos de combustible como Expenses contra la cuenta analitica

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
