# Instrucciones para Generar Informe de Implementacion con IA

Estas instrucciones son para que un agente de IA (Claude Code, Cursor, Antigravity,
u otro) genere el contenido completo del Informe de Implementacion.

## Contexto del Proyecto

Este proyecto genera informes PDF de implementacion de ERP para el programa
ProInnovate del gobierno peruano. Los informes documentan la implementacion de
Odoo 19 en empresas beneficiarias.

## Archivos Clave que el Agente Debe Leer

Antes de generar contenido, el agente DEBE leer estos archivos:

### Configuracion y estilo
1. `project_management/defaults/config.py` — Datos de la empresa, proyecto, personas
2. `project_management/docs/STYLE_GUIDE.md` — Formato LaTeX completo
3. `project_management/docs/REPORT_CHECKLIST.md` — Lista de inputs necesarios

### Plantilla
4. `project_management/templates/implementation.tex.template` — Estructura del informe

### Reporte actual (si existe)
5. `project_management/generated/reports/implementation/implementation.tex` — Archivo a editar

## Documentos de Entrada

El usuario debe proporcionar o indicar la ruta de:

1. **Informe de Diagnostico** — Contiene: analisis de madurez digital, brechas,
   procesos actuales de la empresa. Se usa para la Seccion 1.
2. **Informe de Plan de Implementacion** — Contiene: arquitectura propuesta,
   requerimientos funcionales/no funcionales, cronograma. Se usa para Seccion 1.
3. **Sprint Reviews / Product Increments** — Resumen de lo hecho en cada sprint.
   Se usa para la subseccion de desarrollo iterativo.

## Instrucciones para el Agente

### Paso 1: Leer contexto

Lee los archivos de configuracion (1-3 arriba) y el reporte actual (5).
Identifica todas las secciones con `% TODO`.

### Paso 2: Leer documentos de entrada

Lee los documentos que el usuario proporcione (diagnostico, plan, sprints).
Extrae la informacion relevante para cada seccion.

### Paso 3: Completar las secciones TODO

Para cada `% TODO` en el .tex, genera contenido LaTeX que:

- Use el formato definido en STYLE_GUIDE.md (normalsize, hierarchical indent)
- NO agregue `[leftmargin=...]` a listas individuales (el preambulo lo maneja)
- Ponga `\caption` y `\label` ARRIBA de `\includegraphics` en figuras
- Deje una linea en blanco antes de `\begin{tabularx}`
- Use `\textbf{}` para enfasis, NO `\texttt{}` en columnas estrechas
- Escriba en espanol con acentos LaTeX (`\'a`, `\'e`, `\'i`, `\'o`, `\'u`, `\~n`)

### Paso 4: Generar diagramas PlantUML

Crear archivos `.puml` en `diagrams/` para:

1. **use_case.puml** — Diagrama de casos de uso
   - Actores: los roles de la empresa (recepcionista, agente, cocinero, gerente, cliente)
   - Casos de uso: las funcionalidades principales del sistema

2. **sequence_tour.puml** — Flujo principal del negocio
   - El proceso mas importante (ej: gestion de un tour desde cotizacion hasta cierre)

3. **sequence_reservation.puml** — Flujo secundario
   - Un proceso secundario (ej: reserva de habitacion, pedido en restaurante)

4. **data_model.puml** — Modelo de datos
   - Los modelos principales de Odoo configurados y sus relaciones

Todos los diagramas deben usar este encabezado:
```plantuml
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName Arial
skinparam defaultFontSize 11
skinparam shadowing false
skinparam roundCorner 8
```

### Paso 5: Generar PNGs y compilar

```bash
cd project_management/generated/reports/implementation/
for f in diagrams/*.puml; do plantuml -tpng "$f" -o "$(pwd)/img/"; done
pdflatex -interaction=nonstopmode implementation.tex
pdflatex -interaction=nonstopmode implementation.tex
```

### Paso 6: Verificar overflows

```bash
grep "Overfull" implementation.log
```

Si hay overflows significativos (>20pt), corregir:
- Tablas: ajustar column specs (ver STYLE_GUIDE.md > Table Column Patterns)
- Texto largo en listas: simplificar o dividir en mas items
- `\texttt{}`: reemplazar con texto plano en contextos estrechos

## Reglas de Contenido

### Tono y estilo de redaccion

**Principio general**: El informe debe sentirse escrito por un profesional, no generado
por una maquina. El lenguaje debe ser formal pero natural, con parrafos que fluyan
logicamente y conecten las ideas entre si. NO simplemente reportar datos en seco.

**Reglas basicas**:
- Formal, tercera persona, pasado ("se implemento", "se configuro")
- Parrafos cortos (3-5 oraciones)
- Datos concretos: IDs, cantidades, fechas, nombres de modulos
- No inventar datos — si no hay informacion, dejar un TODO especifico

**Parrafos introductorios** (CRITICO):
Cada seccion y subseccion debe abrir con un parrafo introductorio que contextualice
lo que se va a presentar. Estos parrafos NO deben ser solo una oracion declarativa
("Se selecciono X"), sino que deben:

1. **Conectar con la seccion anterior** — Usar transiciones como "Una vez definidos
   los requerimientos...", "Con la estructura base configurada...", "Aprovechando la
   experiencia de los sprints anteriores...". Esto da continuidad narrativa.

2. **Explicar el "por que"** — No solo decir QUE se hizo, sino POR QUE. Ejemplo:
   - MAL: "Se selecciono Odoo 19 Enterprise como plataforma."
   - BIEN: "La decision central fue la seleccion de Odoo 19 Enterprise como plataforma.
     Esta eleccion no fue arbitraria: se evaluo frente a alternativas como un desarrollo
     a medida y otros ERPs del mercado, y se fundamento en los siguientes criterios..."

3. **Describir la situacion anterior** — Especialmente en modulos y resultados,
   arrancar con como era el proceso ANTES de la implementacion. Ejemplo:
   - MAL: "El CRM centraliza la gestion de prospectos y clientes."
   - BIEN: "Antes de la implementacion, A&F Destiny no contaba con ninguna herramienta
     de seguimiento de clientes. Los datos de huespedes se perdian tras el checkout.
     El CRM resuelve esta carencia al centralizar la gestion desde el primer contacto
     hasta la post-venta."

4. **Usar lenguaje accesible** — Evitar jerga tecnica innecesaria en los parrafos
   narrativos. Los detalles tecnicos van en las listas y tablas que siguen.

**Patrones para tipos de seccion**:

| Tipo de seccion | Patron de parrafo introductorio |
|-----------------|-------------------------------|
| Sprint N | Conectar con sprint anterior + objetivo de este sprint + contexto |
| Modulo X | Situacion anterior (dolor) + como el modulo lo resuelve |
| Resultado RN | Problematica + objetivo + solucion (ya esta en la plantilla) |
| Diseno/Arquitectura | Transicion desde fase anterior + decision tomada + justificacion |
| Capacitaciones | Reconocer perfil del equipo + necesidad + enfoque elegido |

**Ejemplo completo de parrafo introductorio para un sprint**:

```latex
% MAL (robotico):
El Sprint 2 se enfoco en la configuracion inicial del modulo de hotel/apartamentos,
estableciendo la estructura de datos base para los productos de alojamiento.

% BIEN (narrativo):
Con el plan de proyecto validado y la plataforma comprendida, el equipo se enfoco en
la primera unidad de negocio: el hotel. Este sprint establecio la estructura de datos
base ---categorias, atributos y productos--- que serviria como cimiento para las
configuraciones posteriores de agencia y restaurante.
```

**Lo que NO cambiar**: Las listas (`\begin{itemize/enumerate}`), tablas, datos
tecnicos, formulas y contenido estructurado se mantienen concisos y directos.
Solo los parrafos de prosa entre ellos reciben el tratamiento narrativo.

### Secciones y su fuente de datos

| Seccion | Fuente principal |
|---------|-----------------|
| 1.1 Analisis Inicial | Informe de Diagnostico |
| 1.2 Requerimientos | Informe de Plan de Implementacion |
| 1.3 Diseno del Sistema | Plan + datos de Odoo |
| 1.4 Tecnologias | Fijo: Odoo 19, PostgreSQL, Python |
| 1.5 Sprints | Sprint Reviews + Product Increments |
| 1.6 Modulos | Capturas de pantalla + datos de Odoo |
| 2. Resultados | Metricas antes/despues del proyecto |
| 3. Capacitaciones | Registro de sesiones |
| 4. Conclusiones | Sintesis de todo lo anterior |
| 5. Recomendaciones | Basado en lecciones aprendidas |
| 6. Anexos | Presupuesto, cronograma, KPIs, evidencia |

### Tablas de metricas (Seccion 2)

Cada metrica R1-R6 debe tener:
- Nombre del indicador
- Valor ANTES (proceso manual)
- Valor DESPUES (con el sistema)
- Porcentaje de mejora
- Breve descripcion de como se midio

## Ejemplo de Uso con Claude Code

```
usuario> Lee los archivos de project_management/docs/AI_INSTRUCTIONS.md y
         project_management/docs/REPORT_CHECKLIST.md, luego lee el informe
         de diagnostico en ~/docs/diagnostico.pdf y completa todas las
         secciones TODO del informe de implementacion.
```
