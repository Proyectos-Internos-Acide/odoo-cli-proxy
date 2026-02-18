# LaTeX Report Style Guide

Standard style configurations for ProInnovate implementation reports.
These styles are designed to match Word-like formatting conventions.

## Global Styles

### Font
- **Family**: Helvetica (Arial equivalent) via `\usepackage{helvet}`
- **Activation**: `\renewcommand{\familydefault}{\sfdefault}`
- **Size**: 11pt (`\documentclass[11pt,a4paper]{article}`)

### Spacing
- **Line spacing**: 1.5 via `\usepackage{setspace}` + `\onehalfspacing`
- **Paragraph spacing**: 6pt (`\setlength{\parskip}{6pt}`)
- **Paragraph indent**: 0pt (no first-line indent)
- **Tab column sep**: 3pt (`\setlength{\tabcolsep}{3pt}`)

### Hierarchical Indentation System (toggle)

Controlled by boolean `\hierarchicalindenttrue` / `\hierarchicalindentfalse`.

When **enabled**, content paragraphs align to their section title's left edge:

```
1. Section Title ━━━━━━━━━━━━━━━━━━━━━━━━━━
Paragraph text at left margin (0cm indent)...

  1.1 Subsection Title
  Paragraph text indented 0.7cm to match title...
    • List item (0.7cm + 0.5cm = 1.2cm)

    1.1.1 Subsubsection Title
    Paragraph text indented 1.4cm to match title...
      • List item (1.4cm + 0.5cm = 1.9cm)
```

**Configurable dimensions:**
| Variable              | Default | Purpose                              |
|-----------------------|---------|--------------------------------------|
| `\secIndent`          | 0cm     | Section content left margin          |
| `\subsecIndent`       | 0.7cm   | Subsection content left margin       |
| `\subsubsecIndent`    | 1.4cm   | Subsubsection content left margin    |
| `\listIndentExtra`    | 0.5cm   | Extra indent for lists vs paragraph  |

**How it works:**
- `\titlespacing*` sets the title's own left indent
- `\titleformat` after-code sets `\global\leftskip` for subsequent paragraphs
- Tables/figures reset `\leftskip=0pt` via `\AtBeginEnvironment` hooks
- The next section heading automatically restores the correct `\leftskip`

**Critical: tables reset leftskip globally.** Any text between a table and the
next heading will be at `leftskip=0`. This is usually fine because tables are
followed by another heading or another table.

#### List Indentation within Hierarchical Indent

LaTeX's `\list` command resets `\leftskip=0pt`, so the hierarchical indent does
not propagate into enumerate/itemize environments. The `enumitem` package also
bypasses `\@listi` and resets `\labelindent` internally, making direct patches
ineffective.

**Working mechanism** -- use a length register that enumitem evaluates at runtime:
```latex
\newlength{\listlabelindent}  % updated by \titleformat after-code
\setlist[enumerate,1]{labelindent=\listlabelindent, leftmargin=*}
```

In each `\titleformat` after-code, update the register alongside `\leftskip`:
```latex
\titleformat{\subsection}
  {\normalsize\bfseries\color{primary}}{\thesubsection}{0.5em}{}
  [\global\leftskip=\subsecIndent\relax
   \global\listlabelindent=\dimexpr\subsecIndent+\listIndentExtra\relax]
```

Key points:
- Level-scoped `\setlist[enumerate,1]` -- only level 1 lists get the section
  indent; nested lists use default behavior and don't over-indent.
- `leftmargin=*` auto-calculates from `labelindent + labelwidth + labelsep`.
- The same pattern works for `\setlist[itemize,1]`.

### Title Spacing
```latex
% With hierarchical indent:
\titlespacing*{\section}{\secIndent}{18pt plus 4pt minus 2pt}{8pt plus 2pt minus 1pt}
\titlespacing*{\subsection}{\subsecIndent}{14pt plus 3pt minus 2pt}{6pt plus 2pt minus 1pt}
\titlespacing*{\subsubsection}{\subsubsecIndent}{10pt plus 2pt minus 1pt}{4pt plus 1pt minus 1pt}

% Without (flat mode):
\titlespacing*{\section}{0pt}{18pt ...}{8pt ...}
\titlespacing*{\subsection}{0pt}{14pt ...}{6pt ...}
\titlespacing*{\subsubsection}{0pt}{10pt ...}{4pt ...}
```

### Margins
- All sides: 2.5cm (`\geometry{margin=2.5cm}`)

### Colors
| Name    | Hex       | Usage                            |
|---------|-----------|----------------------------------|
| primary | `#2C3E50` | All section titles, main accents |
| accent  | `#2980B9` | Links, highlights                |
| success | `#27AE60` | Success indicators, completions  |
| warn    | `#F39C12` | Warning indicators               |

## Required LaTeX Packages

### Core (already in LATEX_SETUP.md)
`inputenc`, `fontenc`, `babel`, `geometry`, `graphicx`, `booktabs`, `tabularx`,
`enumitem`, `hyperref`, `xcolor`, `fancyhdr`, `titlesec`, `longtable`, `float`, `amsmath`

### Added for Standard Service
| Package     | Purpose                                          |
|-------------|--------------------------------------------------|
| `helvet`    | Helvetica/Arial font family                      |
| `setspace`  | Line spacing control (`\onehalfspacing`)         |
| `etoolbox`  | Environment hooks (auto `\noindent` on tabularx) |
| `tikz`      | Native LaTeX diagrams (architecture diagram)     |
| `caption`   | Caption positioning and left-alignment           |
| `pdflscape` | Landscape pages (rotated in PDF viewer)           |

### TikZ Libraries
`arrows.meta`, `positioning`, `shapes.geometric`, `fit`, `backgrounds`

## Critical Fixes and Patterns

### 1. tabularx + parindent Interaction (CRITICAL)
**Problem**: When `\parindent > 0`, bare `\begin{tabularx}` environments get indented,
causing the table to overflow by exactly `\parindent` (e.g., 1.25cm = 35.56pt).

**Fix**: Use `etoolbox` to auto-prepend `\noindent`:
```latex
\usepackage{etoolbox}
\AtBeginEnvironment{tabularx}{\noindent}
```

Tables inside `\begin{table}[H]` floats are NOT affected (already centered).

### 2. Inline tabularx Overflow
**Problem**: When `\begin{tabularx}` follows text WITHOUT a blank line, it renders inline,
adding its width to the text line width (92-133pt overflow).

**Fix**: Always add a blank line before bare `\begin{tabularx}`:
```latex
\textbf{Title:}

\noindent\begin{tabularx}{\textwidth}{...}
```

### 3. booktabs + tabularx Rule Extension
**Problem**: `\toprule`/`\bottomrule` rules extend ~17pt beyond tabularx width.
This is a known LaTeX cosmetic issue (not visible as content overflow).

**Status**: Accepted as cosmetic. Not fixable without modifying booktabs internals.

### 4. Monospace Text (`\texttt{}`) in Narrow Columns
**Problem**: `\texttt{}` text does NOT hyphenate. In `p{Ncm}` columns, long model names
like `\texttt{product.attribute.value}` overflow.

**Fixes** (choose one):
- Use `\footnotesize` for the entire table
- Widen the column to accommodate the longest `\texttt{}` entry
- Use `\allowbreak{}` inside the texttt: `\texttt{long-\allowbreak{}name}`
- Remove `\texttt{}` and describe in plain text

### 5. Helvetica vs Computer Modern Width
**Impact**: Helvetica (phv) is ~15-20% wider than Computer Modern (cmr).
When switching to Helvetica, ALL column widths need review.

**Affected**: `l` columns (no wrapping), `c` columns, `p{Ncm}` with tight widths.

**Fix**: Reduce `\tabcolsep` (3pt instead of default 6pt) and widen `p{}` columns.

### 6. Long URLs in Text
**Problem**: URLs in `\texttt{}` or `\url{}` don't break at arbitrary points.

**Fixes**:
- Use `\linebreak` before the URL: `available at:\linebreak \url{...}`
- Use `\small\url{...}` to reduce font size
- Use `\allowbreak{}` at breakpoints in `\texttt{}`

## Table Column Patterns

### Recommended Column Specs (with Helvetica 11pt)
| Table Type           | Column Spec                        | Notes                          |
|----------------------|------------------------------------|--------------------------------|
| RF (functional req.) | `cp{4cm}p{8cm}`                    | longtable, multi-page          |
| RNF (non-functional) | `cp{3cm}X`                         | tabularx                       |
| Results (R1-R6)      | `p{3.5cm}XXl`                      | tabularx, `l` for short values |
| Architecture         | `lXp{5.5cm}`                       | tabularx                       |
| Budget               | `p{3.5cm}Xr`                       | tabularx                       |
| KPIs                 | `p{2.5cm}Xcp{3cm}`                 | tabularx                       |
| Sprint cronogram     | `lp{3cm}Xc`                        | tabularx                       |
| Training cronogram   | `lXp{2.5cm}cp{2.5cm}`              | tabularx                       |
| Modules list         | `lX`                               | tabularx                       |
| Data models          | `p{4.2cm}p{2.5cm}p{7.3cm}`        | longtable, `\footnotesize`     |
| DB config            | `lX` (0.85\textwidth)              | tabularx                       |

### Column Width Guidelines
- `l` column: Only for SHORT text (< 8 chars). E.g., "Sprint 1", "+100%", numbers.
- `c` column: Only for very short text. E.g., "4", "Completado".
- `p{Ncm}`: Use for text that MUST wrap. Calculate N based on longest expected content.
- `X`: Auto-expanding. Use for descriptions and long text.
- `r`: Right-aligned numbers only.

## PlantUML Diagrams

### Installation
```bash
# Arch Linux
sudo pacman -S graphviz   # Required dependency for class/use-case diagrams
# PlantUML jar (user-local, no sudo needed)
mkdir -p ~/.local/lib ~/.local/bin
curl -L -o ~/.local/lib/plantuml.jar \
  "https://github.com/plantuml/plantuml/releases/download/v1.2024.7/plantuml-1.2024.7.jar"
echo '#!/bin/sh\njava -jar ~/.local/lib/plantuml.jar "$@"' > ~/.local/bin/plantuml
chmod +x ~/.local/bin/plantuml
```

### Generation
```bash
cd project_management/generated/reports/implementation
plantuml -tpng diagrams/diagram_name.puml -o /absolute/path/to/img/
```

### Standard Diagram Types for Implementation Reports
1. **Use Case Diagram** (`use_case.puml`) - Actors and system functionality
2. **Sequence Diagram: Main Flow** (`sequence_tour.puml`) - Core business process
3. **Sequence Diagram: Secondary Flow** (`sequence_reservation.puml`) - Secondary process
4. **Data Model / ER Diagram** (`data_model.puml`) - Entity relationships

### PlantUML Style Defaults
```plantuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName Arial
skinparam defaultFontSize 11
skinparam shadowing false
skinparam roundCorner 8
```

### Graphviz Dependency
- **Sequence diagrams**: Work WITHOUT Graphviz (PlantUML native renderer)
- **Class/Use-case/ER diagrams**: REQUIRE Graphviz (`dot` executable)
- Without Graphviz, PlantUML generates an error image (small ~10KB PNG)

## Full LaTeX Preamble (Standard Service)

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
\usepackage{helvet}
\usepackage{setspace}
\usepackage{etoolbox}
\usepackage{caption}             % Caption control
\usepackage{pdflscape}           % Landscape pages (rotated in PDF viewer)
\captionsetup{justification=raggedright, singlelinecheck=false, position=above}

% --- Global Styles ---
\renewcommand{\familydefault}{\sfdefault}   % Helvetica/Arial as main font
\onehalfspacing                              % 1.5 line spacing
\geometry{margin=2.5cm}
\setlength{\tabcolsep}{3pt}
\setlength{\parskip}{6pt}                   % Paragraph spacing
\setlength{\parindent}{0pt}                  % No first-line indent

% --- Colors ---
\definecolor{primary}{HTML}{2C3E50}
\definecolor{accent}{HTML}{2980B9}
\definecolor{success}{HTML}{27AE60}
\definecolor{warn}{HTML}{F39C12}

% ===========================================================================
% HIERARCHICAL INDENTATION (toggle: true/false)
% ===========================================================================
\newif\ifhierarchicalindent
\hierarchicalindenttrue   % <-- Change to \hierarchicalindentfalse to disable

% --- Hierarchy dimensions ---
\newlength{\secIndent}            \setlength{\secIndent}{0cm}
\newlength{\subsecIndent}         \setlength{\subsecIndent}{0.7cm}
\newlength{\subsubsecIndent}      \setlength{\subsubsecIndent}{1.4cm}
\newlength{\listIndentExtra}      \setlength{\listIndentExtra}{0.5cm}
\newlength{\currentindent}        \setlength{\currentindent}{0cm}
\newlength{\listlabelindent}      \setlength{\listlabelindent}{0.5cm}

\ifhierarchicalindent
  % --- Titles: same size and color, only indentation differentiates ---
  \titlespacing*{\section}{\secIndent}{18pt plus 4pt minus 2pt}{8pt plus 2pt minus 1pt}
  \titlespacing*{\subsection}{\subsecIndent}{14pt plus 3pt minus 2pt}{6pt plus 2pt minus 1pt}
  \titlespacing*{\subsubsection}{\subsubsecIndent}{10pt plus 2pt minus 1pt}{4pt plus 1pt minus 1pt}

  % --- Content indented to match its section level ---
  %     after-code propagates \leftskip, \currentindent, \listlabelindent
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

  % --- Lists: label aligned to paragraph indent + offset ---
  %     \listlabelindent is updated by \titleformat after-code (above).
  %     enumitem reads the register at runtime when the list opens.
  %     Level 1 only; nested lists use standard defaults.
  \setlist[itemize,1]{labelindent=\listlabelindent, leftmargin=*, labelsep=0.3cm, topsep=2pt}
  \setlist[enumerate,1]{labelindent=\listlabelindent, leftmargin=*, labelsep=0.3cm, topsep=2pt}
  \setlist[itemize,2]{labelsep=0.3cm, topsep=2pt}
  \setlist[enumerate,2]{labelsep=0.3cm, topsep=2pt}

  % --- Tables and figures: reset leftskip for full width ---
  %     The next heading automatically restores the correct leftskip
  \AtBeginEnvironment{tabularx}{\par\global\leftskip=0pt\relax\noindent}
  \AtBeginEnvironment{longtable}{\par\global\leftskip=0pt\relax\noindent}
  \AtBeginEnvironment{table}{\global\leftskip=0pt\relax}
  \AtBeginEnvironment{figure}{\global\leftskip=0pt\relax}
\else
  % --- Flat mode: same uniform style, no indentation ---
  \titlespacing*{\section}{0pt}{18pt plus 4pt minus 2pt}{8pt plus 2pt minus 1pt}
  \titlespacing*{\subsection}{0pt}{14pt plus 3pt minus 2pt}{6pt plus 2pt minus 1pt}
  \titlespacing*{\subsubsection}{0pt}{10pt plus 2pt minus 1pt}{4pt plus 1pt minus 1pt}

  \titleformat{\section}{\normalsize\bfseries\color{primary}}{\thesection.}{0.5em}{}[\titlerule]
  \titleformat{\subsection}{\normalsize\bfseries\color{primary}}{\thesubsection}{0.5em}{}
  \titleformat{\subsubsection}{\normalsize\bfseries\color{primary}}{\thesubsubsection}{0.5em}{}

  \AtBeginEnvironment{tabularx}{\noindent}
\fi

% --- Page style ---
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small Report Title -- COMPANY\_NAME\\
\small Contrato: CONTRACT\_NUMBER}
\renewcommand{\headrulewidth}{0.4pt}
\setlength{\headheight}{28pt}
\fancyfoot[R]{\thepage}
```

### Captions
- **Position**: Always ABOVE the content (table or figure)
- **Alignment**: Left-aligned (`raggedright, singlelinecheck=false`)
- In figure environments, place `\caption{...}` and `\label{...}` BEFORE `\includegraphics`
- Table captions go inside `\begin{table}[H]` before `\begin{tabularx}`

### Landscape Pages

Use `\begin{landscape}...\end{landscape}` for any content that doesn't fit in portrait
(wide tables, large images, diagrams, etc.).
The `pdflscape` package rotates the page in the PDF viewer (unlike `lscape` which only rotates content).

```latex
% Wide table
\begin{landscape}
\begin{table}[H]
    \centering
    \caption{Wide table title}
    \begin{tabularx}{\linewidth}{lXXXXX}
        \toprule
        ...
        \bottomrule
    \end{tabularx}
\end{table}
\end{landscape}

% Wide image or diagram
\begin{landscape}
\begin{figure}[H]
    \centering
    \caption{Wide diagram description}
    \includegraphics[width=\linewidth]{img/wide_diagram.png}
\end{figure}
\end{landscape}
```

Notes:
- Use `\linewidth` inside landscape — both `\linewidth` and `\textwidth` are updated
  to the landscape width (~24.7cm on A4 with 2.5cm margins), but `\linewidth` is the
  safer choice as it always adapts to the current environment
- Each `\begin{landscape}` creates a page break before and after
- Works with any content: tables, figures, tikz diagrams, longtables, etc.

**Headers/footers in landscape pages:**

`fancyhdr` draws headers/footers outside the rotated box, so they appear sideways
in the PDF viewer. The solution is to suppress `fancyhdr` with `\thispagestyle{empty}`
and replicate the header/footer manually inside the landscape environment (where
everything is properly oriented). Portrait pages are NOT affected — `fancyhdr`
continues working normally on them.

Full pattern:

```latex
\begin{landscape}
\thispagestyle{empty}

% --- Manual header (replicates fancyhdr) ---
{\small Report Title -- COMPANY\_NAME\hfill
Contrato: CONTRACT\_NUMBER}
\vspace{-2pt}\hrule\vspace{8pt}

% --- Content ---
\begin{table}[H]
    \centering
    \caption{Wide table}
    \begin{tabularx}{\linewidth}{lXXXXX}
        \toprule
        ...
        \bottomrule
    \end{tabularx}
\end{table}

% --- Manual footer (page number right-aligned) ---
\vfill
\hfill{\thepage}

\end{landscape}
```

## Cover Page (Portada)

Full-bleed image that covers the entire first page with no margins, headers, or page number.
Uses TikZ overlay to bypass page geometry:

```latex
\thispagestyle{empty}
\begin{tikzpicture}[remember picture, overlay]
    \node[inner sep=0pt] at (current page.center) {%
        \includegraphics[width=\paperwidth, height=\paperheight]{img/COVER_IMAGE.jpg}%
    };
\end{tikzpicture}
\clearpage
```

Notes:
- Must be the FIRST content in `\begin{document}` (before the title page)
- The image will be stretched to fill the entire page — use an image with A4 aspect ratio (210x297mm) for best results
- `\thispagestyle{empty}` suppresses header, footer, and page number

## Title Page (Caratula)

The title page uses the `titlepage` environment with a custom `coverstyle` page style
(header visible, no page number). Structure:

1. Title: "INFORME DE IMPLEMENTACION" centered
2. Project description in uppercase
3. Company logo (`\includegraphics[width=0.22\textwidth]`)
4. Data table (`tabular{r@{\quad:\quad}l}`) with booktabs rules — natural width, centered
5. Signature blocks: 2 side-by-side + 1 centered below, each with `\rule{5cm}{0.4pt}` guide line
6. City + Year

Page numbering starts after the title page with `\setcounter{page}{1}`.

The `coverstyle` page style is defined as:
```latex
\fancypagestyle{coverstyle}{%
  \fancyhf{}%
  \fancyhead[L]{\small Report Title -- COMPANY\_NAME\\
  \small Contrato: CONTRACT\_NUMBER}%
  \renewcommand{\headrulewidth}{0.4pt}%
  \fancyfoot{}%  % no page number
}
```

## Writing Tone and Narrative Style

The report must feel written by a professional, not generated by a machine.
Full guidelines are in `AI_INSTRUCTIONS.md > Tono y estilo de redaccion`.

**Key rules**:
- Formal, third person, past tense
- Every section/subsection opens with an introductory paragraph that provides context
- Introductory paragraphs must: connect to the previous section, explain the "why", and describe the situation before the implementation (for modules and results)
- Lists, tables, formulas, and technical content stay concise — only prose paragraphs get narrative treatment
- Never sound robotic: "Se selecciono X" is not enough. Explain WHY X was selected and what problem it solves.

## Pending Style Refinements
- Font size for captions and footnotes
