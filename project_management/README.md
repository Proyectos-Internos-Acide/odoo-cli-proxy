# Project Management

Report generation service for Odoo ERP implementation projects.

## Reports

**Sprint reports** (per sprint):
- **Sprint Review**: Work summary, retrospective table, meetings.
- **Product Increment**: Odoo configuration evidence with record IDs, tables, acceptance criteria.

**Post-implementation reports** (end of project):
- **Implementation Report**: Full implementation details, requirements, technology, results, training.
- **Executive Summary**: Concise project summary with problem, methodology, results, impacts.
- **Lessons Learned**: Reflection with 3-round lessons table.

Supports **LaTeX** and **Markdown** output. Markdown can be converted to PDF via pandoc.

## Quick Start

### Sprint reports

```bash
# 1. Create sprint folder (LaTeX)
uv run python project_management/scripts/create_sprint.py 4 \
  --period "10 de Febrero, 2026 -- 21 de Febrero, 2026"

# 1b. Or with Odoo query + Markdown + PDF
uv run python project_management/scripts/create_sprint.py 4 \
  --period "10 de Febrero, 2026 -- 21 de Febrero, 2026" \
  --start-date 2026-02-10 --end-date 2026-02-22 \
  --format markdown --with-pdf

# 2. Edit the files and add screenshots to img/

# 3. Compile PDFs
uv run python project_management/scripts/compile_sprint.py 4

# 4. Clean auxiliary files
uv run python project_management/scripts/clean_sprint.py 4
```

### Post-implementation reports

```bash
# Create report
uv run python project_management/scripts/create_report.py lessons_learned --format markdown

# Compile to PDF
uv run python project_management/scripts/compile_report.py lessons_learned
```

### Standalone Odoo query

```bash
uv run python project_management/scripts/query_odoo.py \
  --start-date 2026-01-26 --end-date 2026-02-01
```

## Folder Structure

```
project_management/
├── README.md
├── docs/
│   ├── WORKFLOW.md              # Full step-by-step workflow
│   └── LATEX_SETUP.md           # LaTeX + Pandoc installation
├── defaults/
│   └── config.py                # Company name, colors, paths, metadata
├── helpers/
│   ├── odoo_query.py            # Odoo XML-RPC queries by date range
│   ├── renderer.py              # Template rendering + table formatters
│   └── md_to_pdf.py             # Pandoc wrapper (markdown -> PDF)
├── templates/
│   ├── sprint_review.{tex,md}.template
│   ├── product_increment.{tex,md}.template
│   ├── implementation_report.{tex,md}.template
│   ├── executive_summary.{tex,md}.template
│   └── lessons_learned.{tex,md}.template
├── scripts/
│   ├── create_sprint.py         # Create sprint_N/ with templates
│   ├── create_report.py         # Create post-implementation reports
│   ├── compile_sprint.py        # Compile .tex/.md -> .pdf
│   ├── compile_report.py        # Compile report files -> .pdf
│   ├── clean_sprint.py          # Remove auxiliary files
│   └── query_odoo.py            # Standalone Odoo data query
└── generated/                   # Gitignored output directory
    ├── sprints/
    │   ├── sprint_1/
    │   └── ...
    └── reports/
        ├── implementation/
        ├── executive_summary/
        └── lessons_learned/
```

## Prerequisites

- **LaTeX** must be installed for `.tex` compilation. See [docs/LATEX_SETUP.md](docs/LATEX_SETUP.md).
- **Pandoc** is needed only for Markdown-to-PDF conversion. See [docs/LATEX_SETUP.md](docs/LATEX_SETUP.md).
- **Odoo connection** (`.env` file) is needed only for `--start-date`/`--end-date` queries.

## Documentation

- [WORKFLOW.md](docs/WORKFLOW.md) -- Full workflow for sprint and post-implementation reports
- [LATEX_SETUP.md](docs/LATEX_SETUP.md) -- LaTeX and Pandoc installation guide
