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
\begin{figure}[h]
    \centering
    \includegraphics[width=0.9\textwidth]{img/screenshot_name.png}
    \caption{Description}
\end{figure}
```

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

1. Edit `project_management/defaults/config.py` to change company name, project subtitle, description, colors, and project metadata.
2. The templates use `{{PLACEHOLDER}}` tokens replaced by values in `config.py`.
3. Run `create_sprint.py` or `create_report.py` as usual.
