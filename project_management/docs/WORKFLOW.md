# Report Generation Workflow

Step-by-step guide for creating sprint reports and post-implementation reports.

## Sprint Reports

Each sprint produces two documents (LaTeX or Markdown):

- **Sprint Review** (`sprint_review`): Summary of work done, deliverables table, sprint retrospective (dejar de hacer / continuar haciendo / implementar), meetings with recording links, and visual evidence.
- **Product Increment** (`product_increment`): Detailed evidence of Odoo configuration changes with tables of IDs, names, dates, prices, categories, and acceptance criteria (PASS/WARN).

### Step 1: Create sprint folder

Basic (LaTeX, no Odoo query):

```bash
uv run python project_management/scripts/create_sprint.py 4 \
  --period "10 de Febrero, 2026 -- 21 de Febrero, 2026"
```

With Odoo query and markdown format:

```bash
uv run python project_management/scripts/create_sprint.py 4 \
  --period "10 de Febrero, 2026 -- 21 de Febrero, 2026" \
  --start-date 2026-02-10 --end-date 2026-02-22 \
  --format markdown
```

With evidence images and PDF conversion:

```bash
uv run python project_management/scripts/create_sprint.py 4 \
  --period "10 de Febrero, 2026 -- 21 de Febrero, 2026" \
  --start-date 2026-02-10 --end-date 2026-02-22 \
  --format markdown --with-pdf \
  --evidence "/path/to/screenshot1.png,/path/to/screenshot2.png"
```

**Options:**

| Option | Description |
|---|---|
| `--period` | Display text for the sprint period |
| `--start-date` | Odoo query start date (YYYY-MM-DD) |
| `--end-date` | Odoo query end date (YYYY-MM-DD) |
| `--format` | `latex` (default) or `markdown` |
| `--with-pdf` | Convert markdown to PDF via pandoc |
| `--evidence` | Comma-separated image file paths |

When `--start-date` and `--end-date` are provided, the script queries Odoo for:
- Products (`product.template`)
- Product categories (`product.category`)
- Product attributes (`product.attribute`)
- Attribute values (`product.attribute.value`)
- Projects (`project.project`)

The query results are pre-populated into the template tables.

### Step 2: Fill in content

Edit the generated files and complete the `TODO` sections:

**Sprint Review:**
1. **Objetivo del Sprint**: One paragraph describing the sprint goal.
2. **Resumen de lo Realizado**: Subsections per work area.
3. **Sprint Retrospective**: Summary + 3-column table (dejar/continuar/implementar).
4. **Reuniones del Sprint**: Table with meeting name, date, topic.
5. **Evidencia Visual**: Screenshots.

**Product Increment:**
1. **Descripcion del Incremento**: Summary of what was delivered.
2. **Configuracion de Odoo Realizada**: Tables with record IDs (auto-populated if Odoo was queried).
3. **Resumen de Configuracion por Fecha**: Summary table (auto-populated).
4. **Criterios de Aceptacion**: PASS/WARN table.
5. **Evidencia Visual**: Screenshots.

### Step 3: Add screenshots

Place PNG files in the sprint's `img/` folder. Reference in LaTeX:

```latex
\begin{figure}[H]
    \centering
    \caption{Description of the figure}
    \label{fig:screenshot_name}
    \includegraphics[width=0.9\textwidth]{img/screenshot_name.png}
\end{figure}
```

**Important:** Caption and label go ABOVE `\includegraphics` (see `STYLE_GUIDE.md` > Captions).

Reference in Markdown:

```markdown
![Description](img/screenshot_name.png)
```

### Step 4: Compile PDFs

```bash
uv run python project_management/scripts/compile_sprint.py 4
uv run python project_management/scripts/compile_sprint.py 4 --file sprint_review.tex
uv run python project_management/scripts/compile_sprint.py 4 --file sprint_review.md
```

### Step 5: Clean auxiliary files

```bash
uv run python project_management/scripts/clean_sprint.py 4
uv run python project_management/scripts/clean_sprint.py --all
```

## Post-Implementation Reports

> **First time?** See `REPORT_CHECKLIST.md` for a complete list of everything you need
> (documents, images, metadata, diagrams) before starting.

Three report types are available for project completion:

| Report | Description | Reference size |
|---|---|---|
| `implementation` | Full implementation details, requirements, technology, sprints, results, training plan | ~60-70 pages |
| `executive_summary` | Concise project summary with problem, methodology, results, impacts, financing | ~7 pages |
| `lessons_learned` | Project reflection with 3-round lessons table | ~5 pages |

### Create a report

```bash
uv run python project_management/scripts/create_report.py implementation --format markdown
uv run python project_management/scripts/create_report.py executive_summary --format latex
uv run python project_management/scripts/create_report.py lessons_learned --format markdown \
  --start-date 2026-01-02 --end-date 2026-02-22 \
  --evidence "/path/to/img1.png,/path/to/img2.png"
```

**Options:** Same as `create_sprint.py` plus `--project-code`, `--entity-name`, `--ruc`, `--report-date`.

### Compile a report

```bash
uv run python project_management/scripts/compile_report.py implementation
uv run python project_management/scripts/compile_report.py lessons_learned --file lessons_learned.md
```

Note: The implementation report uses `\tableofcontents` and requires 2 pdflatex passes (default).

## Standalone Odoo Query

Preview what data would populate templates without creating files:

```bash
uv run python project_management/scripts/query_odoo.py \
  --start-date 2026-01-26 --end-date 2026-02-01
```

## Table Formatting Tips (LaTeX)

- Use `tabularx` with `X` columns for flexible-width text.
- Use `p{Ncm}` for columns with long text that needs wrapping.
- Use `c`, `l`, `r` only for short content (IDs, prices, dates).
- For tables exceeding one page, switch from `tabularx` to `longtable`.

## Adapting for Other Projects

1. Edit `project_management/defaults/config.py` — all project metadata is centralized there:
   company name, RUC, project code, people (coordinator, consultant, co-consultant),
   city, year, images (cover, logo), dates, colors.
2. The templates use `{{PLACEHOLDER}}` tokens replaced by values in `config.py`.
3. Place the cover image and logo in the report's `img/` folder.
4. Run `create_sprint.py` or `create_report.py` as usual.
5. See `REPORT_CHECKLIST.md` for the full list of required inputs.

## Replication Guide for AI Agents

Complete checklist for an AI agent to replicate this report pipeline from scratch.

### 1. Environment Setup

Install required system packages (see `LATEX_SETUP.md` for full details):

```bash
# Arch Linux
sudo pacman -S texlive-basic texlive-latexrecommended texlive-latexextra \
  texlive-fontsrecommended texlive-langspanish graphviz

# Ubuntu / Debian
sudo apt install texlive-latex-base texlive-latex-recommended texlive-latex-extra \
  texlive-fonts-recommended texlive-lang-spanish graphviz default-jre

# Pandoc (optional, for .md → PDF)
sudo pacman -S pandoc    # Arch
sudo apt install pandoc  # Ubuntu
```

Install PlantUML (user-local):

```bash
mkdir -p ~/.local/lib ~/.local/bin
curl -L -o ~/.local/lib/plantuml.jar \
  "https://github.com/plantuml/plantuml/releases/download/v1.2024.7/plantuml-1.2024.7.jar"
printf '#!/bin/sh\njava -jar ~/.local/lib/plantuml.jar "$@"\n' > ~/.local/bin/plantuml
chmod +x ~/.local/bin/plantuml
export PATH="$HOME/.local/bin:$PATH"
```

Verify all tools:

```bash
pdflatex --version      # TeX Live
plantuml -version        # PlantUML + Java
dot -V                   # Graphviz
pandoc --version         # Pandoc (optional)
```

### 2. Required LaTeX Packages

All these must be available (installed via texlive-latexextra on Linux):

| Package | Purpose |
|---|---|
| `inputenc`, `fontenc`, `babel` | UTF-8, T1 encoding, Spanish |
| `geometry` | Page margins (2.5cm) |
| `graphicx` | Image inclusion |
| `booktabs`, `tabularx`, `longtable` | Professional tables |
| `enumitem` | Custom list indentation |
| `hyperref` | Clickable links |
| `xcolor` | Custom colors |
| `fancyhdr` | Headers and footers |
| `titlesec` | Section title formatting |
| `float` | Figure/table placement `[H]` |
| `amsmath` | Math support |
| `tikz` | Vector diagrams |
| `helvet` | Helvetica/Arial font |
| `setspace` | Line spacing (1.5) |
| `etoolbox` | Environment hooks |
| `caption` | Caption positioning and alignment |

### 3. Document Structure

Follow the directory layout in `LATEX_SETUP.md` > Report Directory Structure.

Key conventions:
- **Preamble**: Copy the full preamble from `STYLE_GUIDE.md` > Full LaTeX Preamble
- **Replace placeholders**: `COMPANY_NAME`, `CONTRACT_NUMBER`, `Report Title`
- **Colors**: Define `primary`, `accent`, `success`, `warn` before `\ifhierarchicalindent`
- **Figures**: Caption + label ABOVE `\includegraphics`; tables: caption ABOVE `\begin{tabularx}`
- **Lists**: Do NOT add `[leftmargin=...]` to individual lists — the preamble handles it globally
- **Tables**: Always leave a blank line before `\begin{tabularx}` to avoid inline rendering
- **Wide content** (tables, images, diagrams): Wrap in `\begin{landscape}...\end{landscape}` (from `pdflscape`); use `\linewidth` not `\textwidth`

### 4. PlantUML Diagrams

Create `.puml` files in the `diagrams/` folder. Standard style header:

```plantuml
@startuml
!theme plain
skinparam backgroundColor white
skinparam defaultFontName Arial
skinparam defaultFontSize 11
skinparam shadowing false
skinparam roundCorner 8
```

Standard diagram types for implementation reports:
1. **Use Case** (`use_case.puml`) — actors + system functionality
2. **Sequence: Main Flow** (`sequence_tour.puml`) — core business process
3. **Sequence: Secondary Flow** (`sequence_reservation.puml`) — secondary process
4. **Data Model / ER** (`data_model.puml`) — entity relationships

Generate PNGs:

```bash
cd generated/reports/<report_name>/
for f in diagrams/*.puml; do plantuml -tpng "$f" -o "$(pwd)/img/"; done
```

### 5. Compilation

```bash
cd generated/reports/<report_name>/
pdflatex -interaction=nonstopmode <report>.tex
pdflatex -interaction=nonstopmode <report>.tex   # 2nd pass for TOC/refs
```

Check for issues:

```bash
# Count overflows (aim for 0-3 cosmetic only)
grep -c "Overfull" <report>.log

# See overflow details
grep "Overfull" <report>.log
```

### 6. Known Pitfalls (see STYLE_GUIDE.md for details)

- **Helvetica is 15-20% wider than Computer Modern** — all table column widths need adjusting
- **`\texttt{}` does NOT hyphenate** — avoid in narrow `p{}` columns; use plain text or `\allowbreak{}`
- **tabularx without blank line** — renders inline, causes overflow
- **`\list` resets `\leftskip`** — lists won't inherit hierarchical indent without the `\listlabelindent` mechanism
- **booktabs rules extend ~17pt** beyond tabularx width — cosmetic, accepted
