# odoo-cli-proxy

Toolkit de automatización para Odoo 19 SaaS vía XML-RPC.
Incluye una librería Python reutilizable, scripts de configuración por unidad de negocio y un sistema de reportes documentarios del proyecto.

## Tabla de Contenidos

- [Instalación](#instalación)
- [Configuración](#configuración)
- [Librería odoo\_cli](#librería-odoo_cli)
- [CLI](#cli)
- [Business Units](#business-units)
  - [Hotel](#hotel)
  - [Agencia de Viajes](#agencia-de-viajes)
  - [Restaurante](#restaurante)
  - [Defaults compartidos](#defaults-compartidos)
- [Servidor MCP](#servidor-mcp)
- [Project Management](#project-management)
- [Estructura del proyecto](#estructura-del-proyecto)

## Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/Proyectos-Internos-Acide/odoo-cli-proxy.git
   cd py-odoo-cli
   ```

2. Instalar [UV](https://docs.astral.sh/uv/) y dependencias:

   **Windows (PowerShell):**
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   uv sync
   ```

   **Linux / macOS:**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   export PATH="$HOME/.local/bin:$PATH"
   uv sync
   ```

## Configuración

Copiar `.env.example` a `.env` y completar con las credenciales de la instancia Odoo:

```bash
cp .env.example .env
```

```env
ODOO_URL=https://tu-instancia.odoo.com
ODOO_DB=tu-base-de-datos
ODOO_USER=email@ejemplo.com
ODOO_PASSWORD=tu-api-key
```

Para usar el comparador de instancias, agregar también las credenciales de la instancia destino (dejar vacío para deshabilitar):

```env
TARGET_MIGRATION_URL=https://nueva-instancia.odoo.com
TARGET_MIGRATION_DB=nueva-instancia
TARGET_MIGRATION_USERNAME=email@ejemplo.com
TARGET_MIGRATION_PASSWORD=api-key
```

## Librería odoo\_cli

Paquete Python reutilizable para interactuar con Odoo por XML-RPC. Se encuentra en `odoo_cli/`.

| Archivo     | Descripción                                  |
|-------------|----------------------------------------------|
| `config.py` | Carga credenciales desde `.env`              |
| `client.py` | Clase `OdooClient` con métodos XML-RPC       |
| `target.py` | Factory `get_target_client()` para instancia de migración |

Créditos a [@rogerinfas](https://github.com/rogerinfas)

### Uso como librería

```python
from odoo_cli import OdooClient

client = OdooClient()
uid = client.connect()

# Buscar registros
partners = client.search_read('res.partner', [['customer_rank', '>', 0]], limit=5)

# Ejecutar método XML-RPC directamente (recomendado sobre write/create)
client.execute('res.partner', 'write', [[partner_id]], {'name': 'Nuevo nombre'})
```

> **Nota:** Usar `client.execute()` directamente en lugar de `client.write()` o `client.create()`, ya que los wrappers tienen bugs conocidos.

### Conexión a múltiples instancias

`OdooClient` acepta credenciales explícitas para conectarse a cualquier instancia sin depender de `.env`:

```python
from odoo_cli import OdooClient, get_target_client

# Instancia source (desde .env)
source = OdooClient()

# Instancia target (desde TARGET_MIGRATION_* en .env, o None si no configurada)
target = get_target_client()

# Instancia arbitraria (credenciales explícitas)
other = OdooClient(url='https://otra.odoo.com', db='otra_db',
                   username='admin@mail.com', password='api-key')
```

## CLI

Punto de entrada: `main.py` (basado en Typer).

```bash
# Probar conexión
uv run python main.py test-connection

# Listar registros de cualquier modelo
uv run python main.py list res.partner --limit 5 --fields name,email

# Listar módulos instalados
uv run python main.py list-modules

# Listar configuraciones del sistema
uv run python main.py list-config
```

## Business Units

Directorio `business_units/` contiene los scripts de configuración organizados por unidad de negocio. Cada script configura una parte específica de la instancia Odoo mediante XML-RPC — creando campos personalizados, vistas, automatizaciones, productos, categorías, etc.

La carpeta está pensada para que un desarrollador pueda **replicar o restaurar** toda la configuración de una instancia Odoo ejecutando los scripts en orden.

Actualmente existe una unidad de negocio: `hotel-trip-agency/`.

### Verificación y auditoría

Scripts de nivel superior para verificar el estado de la instancia:

| Script                 | Descripción                                                  |
|------------------------|--------------------------------------------------------------|
| `check_modules.py`     | Audita módulos instalados vs. requeridos                     |
| `verify_setup.py`      | Verificación completa: módulos, categorías, atributos, zona horaria |
| `setup_products.py`    | Configura atributos de producto y asigna categorías          |
| `compare_instances.py` | Compara configuración entre instancia source y target para migración |

```bash
uv run python business_units/hotel-trip-agency/verify_setup.py
```

---

### Hotel

Directorio: `business_units/hotel-trip-agency/hotel/`

Configuración específica del módulo de hotel (planificación de habitaciones, zona horaria, atributos de producto).

| Script                        | Descripción                                                          |
|-------------------------------|----------------------------------------------------------------------|
| `setup_timezone.py`           | Configura zona horaria America/Lima en usuarios, calendarios y recursos |
| `fix_slot_times_automation.py`| **Parche crítico** — corrige bug de doble offset UTC en slots de planificación. Ejecutar en cada instancia nueva |
| `debug_planning.py`           | Diagnóstico de configuración de zona horaria                         |

**Defaults:**
- `defaults/attributes.py` — IDs de atributos de hotel (14 attrs: camas, baños, área, etc.) y tour (8 attrs)

**Documentación:**
- `docs/TIMEZONE_BUG_FIX.md` — Detalle del bug de planificación y su solución
- `docs/TIMEZONE_SETUP.md` — Guía de configuración de zona horaria
- `docs/PRODUCT_ATTRIBUTES_GUIDE.md` — Guía de atributos de producto

---

### Agencia de Viajes

Directorio: `business_units/hotel-trip-agency/agency/`

Configuración completa de la agencia de viajes: cotizaciones, proyectos, flota, ecommerce y la "Biblia Operativa".

#### Scripts de configuración

| Script                      | Descripción                                                                   |
|-----------------------------|-------------------------------------------------------------------------------|
| `setup_biblia_operativa.py` | Crea modelos personalizados (itinerario, operadores), vista "Biblia Operativa" en cotizaciones, automatización de copia desde plantilla, acción de creación de OC desde operadores |
| `setup_projects.py`         | Plantilla de proyecto "Tour Estándar" con etapas y tareas predefinidas        |
| `setup_fleet_automations.py`| Campos de flota en tareas (vehículo, conductor, asientos), modelo x_task_work_log, 6 automatizaciones (validar fechas, conflictos de vehículo, sync, etc.) |
| `setup_ecommerce.py`        | Vistas QWeb heredadas: reemplaza "Agregar al carrito" por "Solicitar Cotización", formulario modal que crea leads CRM, prefijo "Desde" en precios |
| `setup_custom_fields.py`    | Campos personalizados en contactos (fecha nacimiento, médico, emergencia) y en cotización (fecha viaje, ciudad salida, tipo servicio) |
| `setup_partner_form.py`     | Vista heredada en formulario de contacto con campos de pasajero              |
| `setup_sales_settings.py`   | Activa módulo sale_margin y plantillas de cotización                          |
| `setup_expenses.py`         | Configura productos de gasto para re-facturación                              |
| `setup_kits.py`             | Configuración BoM/Kit (descartado para tours, mantenido como referencia)     |

#### Scripts de prueba y debug

| Script                       | Descripción                                                       |
|------------------------------|-------------------------------------------------------------------|
| `create_test_quotations.py`  | Crea pasajeros, fuentes UTM y cotizaciones de prueba. Flujo completo: Lead CRM → Cotización → Confirmar → Proyecto → Operaciones |
| `check_fleet_availability.py`| Consulta disponibilidad de vehículos con ocupación de asientos    |
| `_debug_ecommerce_views.py`  | Debug de vistas QWeb de ecommerce                                 |
| `_debug_product_page.py`     | Debug de página de producto                                       |
| `_debug_read_archs.py`       | Lee arch_db de vistas QWeb para inspección                        |

**Defaults:**
- `defaults/products.py` — Producto de transporte, zona horaria
- `defaults/projects.py` — Nombre de plantilla, tareas estándar, etapas
- `defaults/automations.py` — Código Python de las 6 automatizaciones de flota
- `defaults/views.py` — Definiciones arch QWeb (ecommerce CTA, Biblia Operativa, etc.)
- `defaults/kits.py` — Definiciones de kits (deprecado)

**Documentación:**
- `docs/TRAVEL_AGENCY_SETUP.md` — Guía completa de setup con diagrama de arquitectura (CRM → Cotización → Proyecto → Operaciones)
- `docs/AGENCY_SETUP_GUIDE.md` — Guía de configuración de agencia
- `docs/FISCAL_PENDIENTE.md` — Configuración fiscal pendiente (IGV 18%)
- `docs/LOGISTICS_SETUP.md` — Setup de logística y flota

---

### Restaurante

Directorio: `business_units/hotel-trip-agency/restaurant/`

Configuración del POS de restaurante: categorías, productos, pantalla de preparación y auto-pedido.

| Script              | Descripción                                                              |
|---------------------|--------------------------------------------------------------------------|
| `setup_pos.py`      | Categorías POS (Bebidas, Desayuno, Platos de fondo, etc.), pantalla de preparación "Despacho restaurante" con 3 etapas, traducciones para self-ordering |
| `setup_products.py` | Productos por defecto del restaurante (Agua, Gaseosa) con traducciones i18n |

**Defaults:**
- `defaults/pos_categories.py` — Categorías POS, pantalla de preparación, etapas
- `defaults/products.py` — Productos del restaurante con i18n

**Documentación:**
- `docs/RESTAURANT_SETUP.md` — Guía de configuración POS (self-ordering, mesas, impresoras, pantalla prep)

---

### Defaults compartidos

Directorio: `business_units/hotel-trip-agency/defaults/`

Datos de configuración compartidos entre todas las unidades:

| Archivo          | Descripción                                                                    |
|------------------|--------------------------------------------------------------------------------|
| `categories.py`  | IDs de categorías de producto (servicios, restaurante, hotel, tours)           |
| `modules.py`     | Módulos requeridos (`REQUIRED_MODULES`), módulos de auditoría, campos de settings |
| `i18n.py`        | Helpers de internacionalización para setup bilingüe es_419 + en_US: `write_translations()`, `search_translatable()`, `update_field_translations()` |

---

### Incidencias

Directorio: `business_units/hotel-trip-agency/incidencies/`

Reportes de problemas específicos de instancias de test. No contiene scripts, solo documentación de problemas encontrados y sus soluciones.

---

## Servidor MCP

El proyecto incluye un servidor [MCP (Model Context Protocol)](https://modelcontextprotocol.io/) que expone las operaciones de Odoo como herramientas para asistentes de IA como Claude Code. Archivo: `mcp_server.py`.

### Tools disponibles

| Tool | Descripción | Parámetros principales |
|------|-------------|------------------------|
| `search_read` | Buscar y leer registros | model, domain (JSON), fields (CSV), limit, offset, order |
| `execute` | Ejecutar cualquier método XML-RPC | model, method, args (JSON), kwargs (JSON) |
| `read_fields` | Inspeccionar campos de un modelo | model, attributes (CSV) |
| `list_models` | Listar modelos disponibles | filter (opcional) |
| `create_record` | Crear un registro | model, vals (JSON) |
| `write_record` | Actualizar registros | model, ids (JSON), vals (JSON) |
| `unlink_record` | Eliminar registros | model, ids (JSON) |

### Probar con MCP Inspector

```bash
uv run mcp dev mcp_server.py
```

### Registrar en Claude Code

Agregar a `.claude/settings.json` (global) o al settings del proyecto:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "uv",
      "args": ["run", "--directory", "/ruta/al/py-odoo-cli", "mcp_server.py"]
    }
  }
}
```

Una vez registrado, Claude Code puede interactuar directamente con la instancia Odoo. Por ejemplo: "busca las cotizaciones del último mes" o "muestra los campos del modelo sale.order".

---

## Project Management

Directorio `project_management/` es un sistema de generación de **reportes documentarios del proyecto** — documentación formal de las entregas, avances por sprint y reportes post-implementación. Genera PDFs a partir de plantillas LaTeX o Markdown.

**No configura Odoo.** Su propósito es producir documentación formal del proyecto de implementación.

### Tipos de reporte

| Tipo                  | Descripción                                              |
|-----------------------|----------------------------------------------------------|
| Sprint Review         | Revisión de entregables por sprint                       |
| Product Increment     | Incremento de producto con evidencias                    |
| Implementation Report | Reporte post-implementación                              |
| Executive Summary     | Resumen ejecutivo para stakeholders                      |
| Lessons Learned       | Lecciones aprendidas                                     |

### Scripts

```bash
# Crear carpeta de sprint con plantillas renderizadas
uv run python project_management/scripts/create_sprint.py 4

# Crear sprint con datos de Odoo (por rango de fechas)
uv run python project_management/scripts/create_sprint.py 4 --from-date 2025-06-01 --to-date 2025-06-15

# Compilar sprint a PDF (requiere pdflatex o pandoc)
uv run python project_management/scripts/compile_sprint.py 4

# Crear reporte post-implementación
uv run python project_management/scripts/create_report.py implementation

# Compilar reporte a PDF
uv run python project_management/scripts/compile_report.py implementation

# Limpiar archivos auxiliares LaTeX
uv run python project_management/scripts/clean_sprint.py 4

# Consultar datos de Odoo por rango de fechas (JSON)
uv run python project_management/scripts/query_odoo.py --from-date 2025-06-01 --to-date 2025-06-15
```

### Estructura interna

```
project_management/
├── scripts/          # Scripts ejecutables (create, compile, clean, query)
├── helpers/          # Lógica de renderizado, consulta Odoo, conversión PDF
├── defaults/         # Configuración (nombre empresa, colores, rutas)
├── templates/        # Plantillas .tex.template y .md.template
├── generated/        # PDFs generados (gitignored)
│   ├── sprints/      # sprint_1/, sprint_2/, ...
│   └── reports/      # Reportes post-implementación
└── docs/
    ├── WORKFLOW.md    # Flujo de trabajo paso a paso
    └── LATEX_SETUP.md # Guía de instalación de LaTeX y Pandoc
```

## Estructura del proyecto

```
py-odoo-cli/
├── odoo_cli/                          # Librería XML-RPC reutilizable
│   ├── client.py                      # Clase OdooClient
│   ├── config.py                      # Carga de credenciales
│   └── target.py                      # Factory para instancia de migración
├── main.py                            # CLI (Typer)
├── mcp_server.py                      # Servidor MCP para asistentes IA
├── business_units/                    # Configuración por unidad de negocio
│   └── hotel-trip-agency/
│       ├── check_modules.py           # Auditoría de módulos
│       ├── verify_setup.py            # Verificación completa
│       ├── compare_instances.py       # Comparador source vs target
│       ├── setup_products.py          # Productos y atributos
│       ├── defaults/                  # Datos compartidos (categorías, módulos, i18n)
│       ├── hotel/                     # Zona horaria, planning, atributos
│       ├── agency/                    # Cotizaciones, proyectos, flota, ecommerce
│       ├── restaurant/               # POS, categorías, preparación
│       └── incidencies/              # Reportes de problemas
├── project_management/                # Reportes documentarios del proyecto
│   ├── scripts/                       # Crear, compilar, limpiar sprints/reportes
│   ├── helpers/                       # Renderizado, consulta Odoo, PDF
│   ├── templates/                     # Plantillas LaTeX/Markdown
│   └── generated/                     # PDFs generados (gitignored)
├── tests/                             # Tests unitarios
├── .env.example                       # Plantilla de credenciales
└── pyproject.toml                     # Dependencias (UV)
```
