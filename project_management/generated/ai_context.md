# Contexto para Generar Informe de Implementacion

Generado el 2026-02-18 13:07

---

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
- Formal, tercera persona, pasado ("se implemento", "se configuro")
- Parrafos cortos (3-5 oraciones)
- Datos concretos: IDs, cantidades, fechas, nombres de modulos
- No inventar datos — si no hay informacion, dejar un TODO especifico

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

---

## Datos del Proyecto

- **Empresa beneficiaria**: A\&F Destiny E.I.R.L.
- **RUC**: 20600144813
- **Representante legal**: Nohemi Milagros Cjumo Ovalle
- **Codigo de proyecto**: N\textdegree{} 471-PROINNOVATE-IMTEMD-2025
- **Programa**: PROGRAMA PROINNOVATE -- IMTEMD 2025
- **Empresa implementadora**: VISEPRO
- **Coordinador General**: Nohemi Milagros Cjumo Ovalle
- **Consultor**: Marco Rosendo Mejia Miranda
- **Co-Consultor**: Gonzalo Enrique Guti\'errez Castillo
- **Ciudad**: CUSCO
- **Pais**: PER\'U
- **Ano**: 2026
- **Fecha de informe**: 01/01/2026 -- 28/02/2026
- **Imagen de portada**: VISEPRO_portada.jpg
- **Logo**: MACHU-PICCHU-AF-DESTINY-LOGO.png
- **Descripcion del proyecto**: Fortalecimiento de la Competitividad y Optimizaci\'on de Procesos en A\&F Destiny E.I.R.L. mediante la Digitalizaci\'on de Reservas, Gesti\'on de Datos y Estrategias de Gesti\'on Comercial.


---

## Plantilla LaTeX (referencia de estructura)

```latex

\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish]{babel}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{longtable}
\usepackage{float}
\usepackage{amsmath}
\usepackage{tikz}
\usetikzlibrary{arrows.meta, positioning, shapes.geometric, fit, backgrounds}
\usepackage{helvet}              % Fuente Helvetica (equivalente a Arial)
\usepackage{setspace}            % Control de interlineado
\usepackage{etoolbox}            % Hooks para entornos
\usepackage{caption}             % Control de captions
\usepackage{pdflscape}           % P\'aginas horizontales (rotadas en visor PDF)
\captionsetup{justification=raggedright, singlelinecheck=false, position=above}

% --- Estilos globales ---
\renewcommand{\familydefault}{\sfdefault}   % Arial/Helvetica como fuente principal
\onehalfspacing                              % Interlineado 1.5
\geometry{margin=2.5cm}
\setlength{\tabcolsep}{3pt}
\setlength{\parskip}{6pt}                   % Espacio entre p\'arrafos
\setlength{\parindent}{0pt}                  % Sin sangr\'ia de primera l\'inea

% ===========================================================================
% INDENTACI\'ON JER\'ARQUICA (toggle: true/false)
% ===========================================================================
\newif\ifhierarchicalindent
\hierarchicalindenttrue   % <-- Cambiar a \hierarchicalindentfalse para desactivar

% --- Dimensiones de la jerarqu\'ia ---
\newlength{\secIndent}            \setlength{\secIndent}{0cm}
\newlength{\subsecIndent}         \setlength{\subsecIndent}{0.7cm}
\newlength{\subsubsecIndent}      \setlength{\subsubsecIndent}{1.4cm}
\newlength{\listIndentExtra}      \setlength{\listIndentExtra}{0.5cm}
\newlength{\currentindent}        \setlength{\currentindent}{0cm}
\newlength{\listlabelindent}      \setlength{\listlabelindent}{0.5cm}

\ifhierarchicalindent
  \titlespacing*{\section}{\secIndent}{18pt plus 4pt minus 2pt}{8pt plus 2pt minus 1pt}
  \titlespacing*{\subsection}{\subsecIndent}{14pt plus 3pt minus 2pt}{6pt plus 2pt minus 1pt}
  \titlespacing*{\subsubsection}{\subsubsecIndent}{10pt plus 2pt minus 1pt}{4pt plus 1pt minus 1pt}

  \titleformat{\section}
    {\normalsize\bfseries\color{primary}}{\thesection.}{0.5em}{}
    [\titlerule\global\leftskip=\secIndent\relax
     \global\currentindent=\secIndent\relax
     \global\listlabelindent=\dimexpr\secIndent+\listIndentExtra\relax]
  \titleformat{\subsection}
    {\normalsize\bfseries\color{primary}}{\thesubsection}{0.5em}{}
    [\global\leftskip=\subsecIndent\relax
     \global\currentindent=\subsecIndent\relax
     \global\listlabelindent=\dimexpr\subsecIndent+\listIndentExtra\relax]
  \titleformat{\subsubsection}
    {\normalsize\bfseries\color{primary}}{\thesubsubsection}{0.5em}{}
    [\global\leftskip=\subsubsecIndent\relax
     \global\currentindent=\subsubsecIndent\relax
     \global\listlabelindent=\dimexpr\subsubsecIndent+\listIndentExtra\relax]

  \setlist[itemize,1]{labelindent=\listlabelindent, leftmargin=*, labelsep=0.3cm, topsep=2pt}
  \setlist[enumerate,1]{labelindent=\listlabelindent, leftmargin=*, labelsep=0.3cm, topsep=2pt}
  \setlist[itemize,2]{labelsep=0.3cm, topsep=2pt}
  \setlist[enumerate,2]{labelsep=0.3cm, topsep=2pt}

  \AtBeginEnvironment{tabularx}{\par\global\leftskip=0pt\relax\noindent}
  \AtBeginEnvironment{longtable}{\par\global\leftskip=0pt\relax\noindent}
  \AtBeginEnvironment{table}{\global\leftskip=0pt\relax}
  \AtBeginEnvironment{figure}{\global\leftskip=0pt\relax}
\else
  \titlespacing*{\section}{0pt}{18pt plus 4pt minus 2pt}{8pt plus 2pt minus 1pt}
  \titlespacing*{\subsection}{0pt}{14pt plus 3pt minus 2pt}{6pt plus 2pt minus 1pt}
  \titlespacing*{\subsubsection}{0pt}{10pt plus 2pt minus 1pt}{4pt plus 1pt minus 1pt}

  \titleformat{\section}{\normalsize\bfseries\color{primary}}{\thesection.}{0.5em}{}[\titlerule]
  \titleformat{\subsection}{\normalsize\bfseries\color{primary}}{\thesubsection}{0.5em}{}
  \titleformat{\subsubsection}{\normalsize\bfseries\color{primary}}{\thesubsubsection}{0.5em}{}

  \AtBeginEnvironment{tabularx}{\noindent}
\fi

% --- Estilo de p\'agina ---
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small Informe de Implementaci\'on -- {{COMPANY_NAME}}\\
\small Contrato: {{PROJECT_CODE}}}
\renewcommand{\headrulewidth}{0.4pt}
\setlength{\headheight}{28pt}
\fancyfoot[R]{\thepage}

% Estilo para car\'atula: header visible, sin n\'umero de p\'agina
\fancypagestyle{coverstyle}{%
  \fancyhf{}%
  \fancyhead[L]{\small Informe de Implementaci\'on -- {{COMPANY_NAME}}\\
  \small Contrato: {{PROJECT_CODE}}}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \fancyfoot{}%
}

% --- Colores ---
\definecolor{primary}{HTML}{{{PRIMARY_COLOR}}}
\definecolor{accent}{HTML}{{{ACCENT_COLOR}}}
\definecolor{success}{HTML}{{{SUCCESS_COLOR}}}
\definecolor{warn}{HTML}{{{WARN_COLOR}}}

\begin{document}

% --- Portada (imagen a p\'agina completa, sin m\'argenes) ---
\newpage
\thispagestyle{empty}
\begin{tikzpicture}[remember picture, overlay]
    \node[inner sep=0pt] at (current page.center) {%
        \includegraphics[width=\paperwidth, height=\paperheight]{img/{{COVER_IMAGE}}}%
    };
\end{tikzpicture}
\clearpage

% --- Car\'atula ---
\begin{titlepage}
\thispagestyle{coverstyle}
\centering

\vspace*{0.5cm}
{\large\bfseries INFORME DE IMPLEMENTACI\'ON}\\[0.8cm]
{\normalsize\bfseries\MakeUppercase{{{PROJECT_DESCRIPTION}}}}\\[0.8cm]

% Logo de la empresa
\includegraphics[width=0.22\textwidth]{img/{{LOGO_IMAGE}}}\\[0.8cm]

% Tabla de datos del proyecto
\begin{tabular}{r@{\quad:\quad}l}
    \toprule
    \textbf{ENTIDAD SOLICITANTE} & \textbf{{{ENTITY_NAME_UPPER}}} \\
    \midrule
    \textbf{RUC} & \textbf{{{RUC}}} \\
    \midrule
    \textbf{C\'ODIGO DE PROYECTO} & \textbf{{{PROJECT_CODE}}} \\
    \midrule
    \textbf{FECHA DE INFORME} & \textbf{{{REPORT_DATE_START}} -- {{REPORT_DATE_END}}} \\
    \bottomrule
\end{tabular}

\vspace{1cm}

% Firmas - fila 1: dos firmantes
\begin{tabular}{p{7cm}p{7cm}}
    \centering\vspace{1cm}\rule{5cm}{0.4pt} &
    \centering\vspace{1cm}\rule{5cm}{0.4pt} \tabularnewline[4pt]
    \centering\textbf{\MakeUppercase{{{COORDINATOR_NAME}}}} &
    \centering\textbf{\MakeUppercase{{{CONSULTANT_NAME}}}} \tabularnewline
    \centering Coordinador General &
    \centering Consultor del proyecto \tabularnewline
\end{tabular}

\vspace{0.5cm}

% Firmas - fila 2: un firmante centrado
\vspace{1.2cm}
\rule{5cm}{0.4pt}\\[4pt]
\textbf{\MakeUppercase{{{CO_CONSULTANT_NAME}}}}\\
Co-Consultor

\vspace{1cm}
{\large\bfseries {{CITY}} -- {{COUNTRY}}}\\
{\large {{YEAR}}}
\end{titlepage}

% Paginaci\'on comienza desde el \'indice
\setcounter{page}{1}

\tableofcontents
\newpage
\listoffigures
\listoftables
\newpage

% =============================================================================
% SECCI\'ON 1: IMPLEMENTACI\'ON
% =============================================================================
\section{Implementaci\'on}

\subsection{An\'alisis Inicial de Procesos y Necesidades}

% TODO: Describir el proceso de an\'alisis inicial.
% Fuente: Informe de Diagn\'ostico de la empresa.
% Puntos a cubrir:
% - Entrevistas con la gerencia y personal operativo
% - Identificaci\'on de puntos de dolor en los procesos manuales
% - Validaci\'on de objetivos del proyecto
% - Formalizaci\'on de necesidades en requerimientos funcionales

\subsection{Requerimientos Funcionales y No Funcionales}

\subsubsection{Requerimientos Funcionales}

\begin{tabularx}{\textwidth}{clX}
    \toprule
    \textbf{C\'odigo} & \textbf{Requerimiento} & \textbf{Descripci\'on} \\
    \midrule
    RF-001 & {[Requerimiento]} & {[Descripci\'on]} \\
    RF-002 & {[Requerimiento]} & {[Descripci\'on]} \\
    RF-003 & {[Requerimiento]} & {[Descripci\'on]} \\
    RF-004 & {[Requerimiento]} & {[Descripci\'on]} \\
    RF-005 & {[Requerimiento]} & {[Descripci\'on]} \\
    \bottomrule
\end{tabularx}

\subsubsection{Requerimientos No Funcionales}

\begin{tabularx}{\textwidth}{clX}
    \toprule
    \textbf{C\'odigo} & \textbf{Requerimiento} & \textbf{Descripci\'on} \\
    \midrule
    RNF-01 & {[Requerimiento]} & {[Descripci\'on]} \\
    RNF-02 & {[Requerimiento]} & {[Descripci\'on]} \\
    RNF-03 & {[Requerimiento]} & {[Descripci\'on]} \\
    \bottomrule
\end{tabularx}

\subsection{Dise\~no del Sistema de Gesti\'on Digital}

\subsubsection{Casos de Uso}

% TODO: Insertar diagrama de casos de uso generado con PlantUML.
% \begin{figure}[H]
%     \centering
%     \caption{Diagrama de casos de uso del sistema}
%     \label{fig:use_case}
%     \includegraphics[width=0.85\textwidth]{img/use_case.png}
% \end{figure}

\subsubsection{Arquitectura del Sistema}

% TODO: Describir la arquitectura. Incluir diagrama TikZ o imagen.
% Fuente: Informe de Plan de Implementaci\'on.

\subsubsection{Dise\~no de la Experiencia e Interfaz de Usuario (UX/UI)}

% TODO: Describir personalizaci\'on de la interfaz.

\subsubsection{Configuraci\'on de la Base de Datos}

% TODO: Describir la estructura de datos configurada.

\subsubsection{Modelos de Datos}

% TODO: Insertar diagrama ER generado con PlantUML.
% \begin{figure}[H]
%     \centering
%     \caption{Modelo de datos del sistema}
%     \label{fig:er_diagram}
%     \includegraphics[width=\textwidth]{img/data_model.png}
% \end{figure}

\subsection{Selecci\'on y Aplicaci\'on de Tecnolog\'ias}

\subsubsection{Backend}

% TODO: Odoo 19 (saas-19.1), Python, XML-RPC API

\subsubsection{Frontend}

% TODO: Odoo Website, eCommerce, Self-Ordering, Portal

\subsubsection{Base de Datos}

% TODO: PostgreSQL (gestionado por Odoo SaaS)

\subsubsection{Infraestructura y Despliegue}

% TODO: Odoo.sh / SaaS, dominio, configuraci\'on DNS

\subsection{Desarrollo Iterativo Basado en Sprints}

% TODO: Describir el proceso de sprints.
% Fuente: Sprint Reviews y Product Increments de cada sprint.

\subsubsection{Sprint 1}

% TODO: Resumen del Sprint 1

\subsubsection{Sprint 2}

% TODO: Resumen del Sprint 2

\subsubsection{Sprint 3}

% TODO: Resumen del Sprint 3

% TODO: Agregar m\'as sprints seg\'un corresponda

\subsection{M\'odulos del Sistema y su Integraci\'on}

% TODO: Describir cada m\'odulo configurado con capturas de pantalla.
% Incluir: Hotel, Agencia, Restaurante, CRM, Web, Compras, etc.

% =============================================================================
% SECCI\'ON 2: RESULTADOS
% =============================================================================
\section{Resultados}

% TODO: Completar con m\'etricas reales del proyecto.

\subsection{M\'etrica R1}

% TODO: Nombre y descripci\'on de la m\'etrica

\begin{tabularx}{\textwidth}{Xlll}
    \toprule
    \textbf{Indicador} & \textbf{Antes (manual)} & \textbf{Despu\'es (sistema)} & \textbf{Mejora} \\
    \midrule
    {[Indicador]} & {[Antes]} & {[Despu\'es]} & {[Mejora]} \\
    \bottomrule
\end{tabularx}

\subsection{M\'etrica R2}

% TODO: Nombre y descripci\'on de la m\'etrica

\begin{tabularx}{\textwidth}{Xlll}
    \toprule
    \textbf{Indicador} & \textbf{Antes (manual)} & \textbf{Despu\'es (sistema)} & \textbf{Mejora} \\
    \midrule
    {[Indicador]} & {[Antes]} & {[Despu\'es]} & {[Mejora]} \\
    \bottomrule
\end{tabularx}

\subsection{M\'etrica R3}

% TODO: Nombre y descripci\'on de la m\'etrica

\begin{tabularx}{\textwidth}{Xlll}
    \toprule
    \textbf{Indicador} & \textbf{Antes (manual)} & \textbf{Despu\'es (sistema)} & \textbf{Mejora} \\
    \midrule
    {[Indicador]} & {[Antes]} & {[Despu\'es]} & {[Mejora]} \\
    \bottomrule
\end{tabularx}

% =============================================================================
% SECCI\'ON 3: PLAN DE CAPACITACIONES
% =============================================================================
\section{Plan de Capacitaciones}

\subsection{Objetivo de la Capacitaci\'on}

% TODO: Describir el objetivo

\subsection{Alcance}

% TODO: A qui\'enes va dirigida

\subsection{Metodolog\'ia}

% TODO: Sesiones din\'amicas, ejercicios pr\'acticos, etc.

\subsection{Recursos Utilizados}

% TODO: Materiales, equipos, infraestructura

\subsection{Cronograma de Capacitaciones}

\begin{tabularx}{\textwidth}{lXllc}
    \toprule
    \textbf{Sesi\'on} & \textbf{Tema Principal} & \textbf{Dirigido a} & \textbf{Horas} & \textbf{Mes} \\
    \midrule
    Sesi\'on 1 & {[Tema]} & {[Audiencia]} & 4 & {[Mes]} \\
    Sesi\'on 2 & {[Tema]} & {[Audiencia]} & 4 & {[Mes]} \\
    Sesi\'on 3 & {[Tema]} & {[Audiencia]} & 4 & {[Mes]} \\
    \bottomrule
\end{tabularx}

\subsection{Desarrollo de las Sesiones}

\subsubsection{Sesi\'on 1}

% TODO: Describir contenido impartido y evidencia

\subsubsection{Sesi\'on 2}

% TODO: Describir contenido impartido y evidencia

\subsubsection{Sesi\'on 3}

% TODO: Describir contenido impartido y evidencia

\subsection{Evaluaci\'on de la Adopci\'on}

% TODO: Resultados de la evaluaci\'on

% =============================================================================
% SECCI\'ON 4: CONCLUSIONES
% =============================================================================
\section{Conclusiones}

% TODO: 3-5 p\'arrafos de conclusiones

% =============================================================================
% SECCI\'ON 5: RECOMENDACIONES
% =============================================================================
\section{Recomendaciones}

% TODO: 3-5 recomendaciones

% =============================================================================
% SECCI\'ON 6: ANEXOS
% =============================================================================
\section{Anexos}

\subsection{Presupuesto}

% TODO: Tabla de presupuesto

\subsection{Cronograma de Implementaci\'on}

% TODO: Tabla de cronograma por sprints

\subsection{KPIs del Plan}

% TODO: Tabla de KPIs

\subsection{M\'odulos Instalados}

% TODO: Lista de m\'odulos de Odoo

\subsection{Evidencia Visual}

{{EVIDENCE_IMAGES}}

\end{document}

```


---

## Reglas de Formato LaTeX

- Acentos: `\'a`, `\'e`, `\'i`, `\'o`, `\'u`, `\~n`
- Captions ARRIBA de `\includegraphics`
- Linea en blanco antes de `\begin{tabularx}`
- NO agregar `[leftmargin=...]` a listas individuales
- Usar `\textbf{}` para enfasis, evitar `\texttt{}` en columnas estrechas
- Redaccion formal, tercera persona, tiempo pasado


---

## Instruccion Final


Con toda la informacion de arriba, genera el contenido completo para todas las secciones marcadas con `% TODO` en el archivo `implementation.tex`. Tambien genera los archivos `.puml` para los 4 diagramas (use_case, sequence_tour, sequence_reservation, data_model). Escribe el contenido directamente en LaTeX listo para copiar al archivo .tex.
