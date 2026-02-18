# Checklist para Generar un Informe de Implementacion

Lista completa de todo lo que necesitas tener listo antes de generar el informe.

## 1. Documentos de Entrada

Estos documentos son la fuente de contenido para redactar el informe:

| # | Documento | Para que se usa | Formato |
|---|-----------|-----------------|---------|
| 1 | **Informe de Diagnostico** de la empresa | Seccion 1: Analisis Inicial, brechas, madurez digital | PDF o Word |
| 2 | **Informe de Plan de Implementacion** | Seccion 1: Arquitectura, requerimientos, cronograma | PDF o Word |
| 3 | **Sprint Reviews** (de cada sprint) | Seccion 1: Desarrollo iterativo por sprints | PDF |
| 4 | **Product Increments** (de cada sprint) | Seccion 1: Detalle de configuracion por sprint | PDF |
| 5 | **Metricas de resultados** | Seccion 2: Tablas de antes/despues por indicador | Tabla o texto |
| 6 | **Plan de capacitaciones** (si existe) | Seccion 3: Cronograma y contenido de sesiones | Texto |

## 2. Datos de la Empresa Beneficiaria

Editar en `project_management/defaults/config.py`:

| Campo | Variable en config.py | Ejemplo |
|-------|----------------------|---------|
| Razon social | `COMPANY_NAME` | `r"A\&F Destiny E.I.R.L."` |
| RUC | `PROJECT_RUC` | `"20600144813"` |
| Representante legal | `LEGAL_REPRESENTATIVE` | `"Nohemi Milagros Cjumo Ovalle"` |

## 3. Datos del Proyecto

| Campo | Variable en config.py | Ejemplo |
|-------|----------------------|---------|
| Codigo de proyecto | `PROJECT_CODE` | `r"N\textdegree{} 471-PROINNOVATE-IMTEMD-2025"` |
| Programa | `PROGRAM_NAME` | `r"PROGRAMA PROINNOVATE -- IMTEMD 2025"` |
| Descripcion del proyecto | `PROJECT_DESCRIPTION` | Titulo largo del proyecto (se muestra en caratula) |
| Fecha inicio del informe | `REPORT_DATE_START` | `"01/01/2026"` (formato dd/mm/yyyy) |
| Fecha fin del informe | `REPORT_DATE_END` | `"28/02/2026"` (formato dd/mm/yyyy) |

## 4. Personas que Firman

| Campo | Variable en config.py | Ejemplo |
|-------|----------------------|---------|
| Coordinador General | `COORDINATOR_NAME` | `"Nohemi Milagros Cjumo Ovalle"` |
| Consultor | `CONSULTANT_NAME` | `"Marco Rosendo Mejia Miranda"` |
| Co-Consultor | `CO_CONSULTANT_NAME` | `r"Gonzalo Enrique Guti\'errez Castillo"` |

> Nota: Los nombres aparecen en mayusculas automaticamente en la caratula.
> Las firmas se colocan manualmente sobre las lineas guiadoras despues de imprimir.

## 5. Ubicacion y Fecha

| Campo | Variable en config.py | Ejemplo |
|-------|----------------------|---------|
| Ciudad | `CITY` | `"CUSCO"` |
| Pais | `COUNTRY` | `r"PER\'U"` |
| Ano | `YEAR` | `"2026"` |

## 6. Empresa Implementadora

| Campo | Variable en config.py | Ejemplo |
|-------|----------------------|---------|
| Nombre | `IMPLEMENTING_COMPANY` | `"VISEPRO"` |

## 7. Imagenes Requeridas

Colocar en la carpeta `img/` del reporte generado:

### Obligatorias (portada y caratula)

| Archivo | Variable en config.py | Descripcion |
|---------|----------------------|-------------|
| Imagen de portada | `COVER_IMAGE` | Imagen a pagina completa de la empresa implementadora (JPG o PNG) |
| Logo de la empresa | `LOGO_IMAGE` | Logotipo de la empresa beneficiaria (PNG, fondo transparente recomendado) |

### Capturas de pantalla del sistema (para la seccion de modulos)

Estas son capturas de pantalla de Odoo que ilustran cada modulo implementado:

| Imagen sugerida | Seccion donde aparece |
|-----------------|----------------------|
| `planning.png` | Modulo Hotel - Planning de habitaciones |
| `modulo_agencia.png` | Modulo Agencia - Biblia Operativa |
| `modulo_restaurante.png` | Modulo Restaurante - POS |
| `modulo_CRM.png` | Modulo CRM - Pipeline |
| `modulo_web.png` | Modulo Web/eCommerce |
| `modulo_compras.png` | Modulo Compras |
| `prototipo_figma.png` | Diseno UX/UI (si aplica) |
| `dashboard.png` | Anexos - Dashboard principal |

> Formato: PNG, ancho minimo 1200px para buena calidad en el PDF.

### Capturas de capacitaciones (para la seccion de capacitaciones)

| Imagen sugerida | Descripcion |
|-----------------|-------------|
| `capacitacion_sesion1.png` | Evidencia de la sesion 1 |
| `capacitacion_sesion2.png` | Evidencia de la sesion 2 |
| `capacitacion_sesion3.png` | Evidencia de la sesion 3 |

## 8. Diagramas a Crear

Se crean como archivos `.puml` en la carpeta `diagrams/` y se generan como PNG:

| Diagrama | Archivo | Necesita Graphviz |
|----------|---------|-------------------|
| Casos de uso | `use_case.puml` | Si |
| Secuencia: flujo principal | `sequence_tour.puml` | No |
| Secuencia: flujo secundario | `sequence_reservation.puml` | No |
| Modelo de datos / ER | `data_model.puml` | Si |

Para generar los PNG:

```bash
cd generated/reports/implementation/
for f in diagrams/*.puml; do plantuml -tpng "$f" -o "$(pwd)/img/"; done
```

## 9. Instancia de Odoo Configurada

El script puede consultar Odoo automaticamente para obtener datos de:
- Productos configurados
- Categorias de productos
- Atributos y valores
- Proyectos creados
- Modulos instalados

Para esto necesitas:
- Archivo `.env` con credenciales de la instancia Odoo
- Que la instancia tenga datos reales (no de prueba)

## Como Generar el Informe

### Paso 1: Editar config.py

Abre `project_management/defaults/config.py` y completa todos los campos de las secciones 2-6 de este checklist.

### Paso 2: Crear el reporte desde la plantilla

```bash
uv run python project_management/scripts/create_report.py implementation \
  --format latex \
  --start-date 2026-01-02 --end-date 2026-02-28
```

### Paso 3: Colocar imagenes

Copia las imagenes de la seccion 7 a:
```
project_management/generated/reports/implementation/img/
```

### Paso 4: Crear y generar diagramas PlantUML

Crea los archivos `.puml` en `diagrams/` (ver seccion 8) y genera los PNG.

### Paso 5: Completar el contenido

Edita el archivo `.tex` generado y completa todas las secciones marcadas con `% TODO`.
Usa los documentos de entrada (seccion 1) como fuente.

### Paso 6: Compilar

```bash
cd project_management/generated/reports/implementation/
pdflatex -interaction=nonstopmode implementation.tex
pdflatex -interaction=nonstopmode implementation.tex
```

Se necesitan 2 pasadas para que el indice y las referencias se generen correctamente.

### Paso 7: Verificar

```bash
# Revisar overflows (deben ser 0-3 cosmeticos)
grep -c "Overfull" implementation.log
```

Abrir el PDF y verificar:
- Portada (imagen completa sin margenes)
- Caratula (logo, datos, firmas)
- Indice con numeros de pagina correctos
- Figuras con caption arriba
- Listas indentadas correctamente
