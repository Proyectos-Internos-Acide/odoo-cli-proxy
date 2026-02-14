# Configuracion de Agencia de Viajes High-Ticket en Odoo 19

Guia completa para configurar los flujos de venta, operaciones, logistica y estructura
de datos para una agencia de viajes con hotel y restaurante en Odoo 19 (saas-19.1).

---

## Arquitectura General

```
Cliente (Web) --> Catalogo de Tours (sin carrito)
                       |
                  "Solicitar Cotizacion"
                       |
                  Lead en CRM (New)
                       |
              Vendedor crea Cotizacion
             /                        \
   Metodo A: Template             Metodo B: Kit/BoM
   (lineas individuales)          (producto Kit con costo auto)
             \                        /
              Envia por Email al Cliente
                       |
              Cliente paga en Portal
                       |
              Orden de Venta confirmada
                       |
              Proyecto creado automaticamente
              (con tareas: Reservas, Transporte, Guia, etc.)
                       |
              Ejecucion del Tour
              - Fleet (vehiculo propio) o Purchase (tercero)
              - Gastos operativos -> Cuenta Analitica
              - Gastos re-facturables -> Se agregan a la SO
```

---

## 1. Modulos Requeridos

| Modulo | Proposito | Estado |
|--------|-----------|--------|
| sale_management | Ventas y cotizaciones | Requerido |
| sale_margin | Margenes en cotizaciones | Requerido |
| crm | Pipeline de leads | Requerido |
| project + sale_project | Proyectos por venta | Requerido |
| hr_expense | Gastos re-facturables | Requerido |
| purchase | Compras (transporte externo) | Requerido |
| fleet | Flotilla propia | Requerido |
| mrp | Kits/BoM para paquetes | Requerido |
| website_sale | eCommerce | Requerido |
| planning + sale_renting | Hotel/Rental | Ya instalado |

### Instalar modulos faltantes

Desde la UI: **Ajustes > Apps > Buscar modulo > Instalar**

Verificar con script:
```bash
uv run python business_units/hotel-trip-agency/setup_sales_settings.py
```

---

## 2. Ajustes de Ventas

### Margenes
El modulo `sale_margin` ya esta instalado. Permite ver el margen (precio - costo) en cada
linea de la cotizacion.

### Plantillas de Presupuesto
Activado automaticamente por el script. Permite crear templates de cotizacion reutilizables.

### Productos Opcionales
En Odoo 19, los productos opcionales se manejan como lineas con `is_optional=True` dentro
del template de cotizacion. No hay pestana separada.

---

## 3. Flujo de Ventas: CRM -> Cotizacion -> Portal

### 3.1 Catalogo Web (sin carrito directo)
Los paquetes turisticos se publican en el website como vitrina/catalogo. El boton
"Add to Cart" se reemplaza por "Solicitar Cotizacion" que crea un Lead en CRM.

**Configuracion desde la UI**:
1. Ir a **Website > Personalizar** en la pagina del producto
2. Reemplazar el boton de carrito por un formulario de contacto
3. O usar el campo `website_form` para crear leads automaticamente

### 3.2 Dos metodos de cotizacion

**Metodo A: Template con lineas individuales**
- Usar la plantilla "Paquete Cusco Prueba"
- Personalizar lineas segun el cliente
- Cada producto tiene su precio individual
- Flexible para cotizaciones unicas

**Metodo B: Kit/BoM**
- Agregar el producto Kit "Cusco 3D/2N" a la cotizacion
- Costo auto-calculado desde componentes (Hotel + Tour + Transporte)
- Margen visible automaticamente con sale_margin
- Ideal para paquetes estandar

### 3.3 Template de cotizacion existente
**"Paquete Cusco Prueba"** (id=1):
- Day 1: Landing and City Tour (Transport + City Tour)
- Day 2: Valle Sagrado (Palcoyo)
- Lodging (Apartment 301)
- Optional Products (Agua Mineral)

---

## 4. Proyectos y Operaciones

### Template de proyecto "Tour Estandar"
Al confirmar una venta de tour, Odoo crea automaticamente un proyecto con estas tareas:

1. **Confirmar Reservas** - Hotel, entradas, restaurantes
2. **Coordinar Transporte** - Vehiculo propio o externo
3. **Asignar Guia Turistico** - Disponibilidad por fechas
4. **Verificar Documentacion** - Pasaportes, seguros
5. **Seguimiento Post-Tour** - Feedback y reviews

### Configuracion de producto tour
- `type`: service
- `service_tracking`: task_in_project
- `invoice_policy`: delivery (por hitos)
- `project_template_id`: Tour Estandar

### Contabilidad Analitica
Cada proyecto genera una cuenta analitica automatica. Esto permite:
- Imputar compras de transporte externo al tour
- Imputar gastos operativos al tour
- Medir rentabilidad por viaje individual

```bash
uv run python business_units/hotel-trip-agency/setup_projects.py
```

---

## 5. Logistica y Flotilla

### Vehiculos propios (Fleet)
- Registrar vehiculos en **Flotilla > Vehiculos**
- Controlar mantenimiento, combustible, seguros
- **Asignacion a tours**: Manual, en las Tareas del Proyecto
- No se vincula automaticamente a Ventas

### Vehiculos tercerizados (Purchase)
- Usar producto **"Servicio de Transporte Externo"** (ya creado)
- Crear Orden de Compra desde la Tarea del proyecto
- Imputar a la cuenta analitica del tour
- El costo queda registrado contra el proyecto para medir rentabilidad

---

## 6. Gastos (Expenses)

### Re-facturacion habilitada
Todos los productos de gasto estan configurados con `expense_policy=sales_price`:
- Communication, Expenses, Meals, Gifts, Mileage
- Travel & Accommodation, Transportation from Airport

### Flujo operativo
1. Empleado crea gasto y lo vincula a la cuenta analitica del proyecto
2. **Gasto operativo**: Se registra como costo del tour
3. **Gasto re-facturable**: Marcar "A re-facturar" -> Se agrega a la Orden de Venta del cliente

```bash
uv run python business_units/hotel-trip-agency/setup_expenses.py
```

---

## 7. Kit/BoM (Paquetes con costo auto-calculado)

### Producto Kit: "Cusco 3D/2N"
- **Tipo**: Consumible (consu)
- **Precio de venta**: $500
- **BoM tipo Kit (phantom)**: Al vender, se expande en componentes

### Componentes
| Componente | Cantidad | Costo unitario |
|------------|----------|----------------|
| Apartment 301 | 2 noches | (configurar) |
| City Tour Cusco | 1 | (configurar) |
| Palcoyo | 1 | (configurar) |
| Transportation from Airport | 1 | (configurar) |

### Configurar costos
Desde la UI: Ir a cada producto > Informacion General > **Costo** (standard_price)

O via script:
```python
client.execute('product.product', 'write', [product_id], {'standard_price': 50.0})
```

### Margen automatico
Con `sale_margin`, al agregar el Kit a una cotizacion:
- Costo = suma de costos de componentes
- Margen = precio de venta - costo
- El vendedor puede ajustar el precio final

```bash
uv run python business_units/hotel-trip-agency/setup_kits.py
```

---

## 8. Verificacion

```bash
uv run python business_units/hotel-trip-agency/verify_setup.py
```

### Resultado esperado
- 12 modulos: PASS
- Atributos hotel: PASS (si todos estan en no_variant)
- Tours: PASS (con tracking + template)
- Proyecto template: PASS (5 tareas)
- Cotizacion template: PASS
- Kit/BoM: PASS (4 componentes)
- Gastos: 7/7 re-facturables
- Timezone: America/Lima

> Si hay WARN en atributos, ver `hotel/docs/PRODUCT_ATTRIBUTES_GUIDE.md` para la guia
> y `incidencies/` para problemas especificos de la instancia de prueba.

---

## Scripts disponibles

| Script | Ubicacion | Proposito |
|--------|-----------|-----------|
| `setup_timezone.py` | `hotel/` | Timezone de todos los componentes |
| `debug_planning.py` | `hotel/` | Debug de slots de planificacion |
| `setup_sales_settings.py` | `agency/` | Ajustes de ventas, modulos, templates |
| `setup_projects.py` | `agency/` | Template de proyecto y tareas |
| `setup_kits.py` | `agency/` | Kit/BoM para paquetes |
| `setup_expenses.py` | `agency/` | Gastos re-facturables |
| `setup_products.py` | raiz | Atributos y productos (cross-cutting) |
| `verify_setup.py` | raiz | Verificacion completa |
| `check_modules.py` | raiz | Auditoria de modulos y estado |
| `fix_slot_times_automation.py` | `hotel/` | Parche critico para bug de planning slots |
| `setup_custom_fields.py` | `agency/` | Campos custom, categorias proveedor, alojamiento externo |
| `create_test_quotations.py` | `agency/` | Datos de prueba: pasajeros y cotizaciones |

Base path: `business_units/hotel-trip-agency/`

---

## Orden de ejecucion para nueva instancia

1. Instalar modulos faltantes (mrp) desde UI
2. `uv run python business_units/hotel-trip-agency/hotel/setup_timezone.py America/Lima`
3. `uv run python business_units/hotel-trip-agency/hotel/fix_slot_times_automation.py` **(CRITICO)**
4. `uv run python business_units/hotel-trip-agency/agency/setup_sales_settings.py`
5. `uv run python business_units/hotel-trip-agency/setup_products.py`
6. `uv run python business_units/hotel-trip-agency/agency/setup_projects.py`
7. `uv run python business_units/hotel-trip-agency/agency/setup_expenses.py`
8. `uv run python business_units/hotel-trip-agency/agency/setup_kits.py`
9. `uv run python business_units/hotel-trip-agency/agency/setup_custom_fields.py`
10. `uv run python business_units/hotel-trip-agency/verify_setup.py`
11. Configurar catalogo web desde UI (Website Builder)
12. Agregar campos custom a vistas desde Odoo Studio (drag & drop)

> **IMPORTANTE**: El paso 3 (fix_slot_times_automation) es **obligatorio** antes de
> confirmar cualquier orden de venta. Sin el, la automatizacion del booking engine
> crashea al crear planning slots sin fechas. Ver `hotel/docs/TIMEZONE_BUG_FIX.md`.
