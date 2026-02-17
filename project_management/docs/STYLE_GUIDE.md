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
- **Paragraph indent**: 1.25cm (`\setlength{\parindent}{1.25cm}`)
- **Tab column sep**: 3pt (`\setlength{\tabcolsep}{3pt}`)

### Title Spacing (section → subsection → subsubsection)
```latex
\titlespacing*{\section}{0pt}{18pt plus 4pt minus 2pt}{8pt plus 2pt minus 1pt}
\titlespacing*{\subsection}{0pt}{14pt plus 3pt minus 2pt}{6pt plus 2pt minus 1pt}
\titlespacing*{\subsubsection}{0pt}{10pt plus 2pt minus 1pt}{4pt plus 1pt minus 1pt}
```

### Margins
- All sides: 2.5cm (`\geometry{margin=2.5cm}`)

### Colors
| Name    | Hex       | Usage                            |
|---------|-----------|----------------------------------|
| primary | `#2C3E50` | Section titles, main accents     |
| accent  | `#2980B9` | Subsection titles, links         |
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
\AtBeginEnvironment{tabularx}{\noindent}

\renewcommand{\familydefault}{\sfdefault}
\onehalfspacing
\geometry{margin=2.5cm}
\setlength{\tabcolsep}{3pt}
\setlength{\parskip}{6pt}
\setlength{\parindent}{1.25cm}

\titlespacing*{\section}{0pt}{18pt plus 4pt minus 2pt}{8pt plus 2pt minus 1pt}
\titlespacing*{\subsection}{0pt}{14pt plus 3pt minus 2pt}{6pt plus 2pt minus 1pt}
\titlespacing*{\subsubsection}{0pt}{10pt plus 2pt minus 1pt}{4pt plus 1pt minus 1pt}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small COMPANY\_NAME}
\fancyhead[R]{\small Report Title}
\fancyfoot[C]{\thepage}

\definecolor{primary}{HTML}{2C3E50}
\definecolor{accent}{HTML}{2980B9}
\definecolor{success}{HTML}{27AE60}
\definecolor{warn}{HTML}{F39C12}

\titleformat{\section}{\Large\bfseries\color{primary}}{}{0em}{}[\titlerule]
\titleformat{\subsection}{\large\bfseries\color{accent}}{}{0em}{}
```

## Pending Style Refinements
- Section numbering format (currently auto from article class)
- Header/footer design (currently simple left/right text)
- Title page layout (signature block, logo placement)
- Figure caption styling
- List indentation fine-tuning
- Font size for captions and footnotes
