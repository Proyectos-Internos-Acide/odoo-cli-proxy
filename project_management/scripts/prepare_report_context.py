#!/usr/bin/env python3
"""Prepare AI context for report generation.

Collects project config, Odoo data, and input documents into a single
context file that can be:
  - Pasted into any AI chat (Antigravity, Cursor, ChatGPT, Claude)
  - Used with Claude API automatically (if ANTHROPIC_API_KEY is set)

Usage:
    # Generate context file only (paste into your AI editor)
    uv run python project_management/scripts/prepare_report_context.py

    # With Odoo data
    uv run python project_management/scripts/prepare_report_context.py \
      --start-date 2026-01-02 --end-date 2026-02-28

    # With input documents
    uv run python project_management/scripts/prepare_report_context.py \
      --diagnostico ~/docs/diagnostico.txt \
      --plan ~/docs/plan_implementacion.txt

    # Auto-generate with Claude API
    uv run python project_management/scripts/prepare_report_context.py \
      --auto --start-date 2026-01-02 --end-date 2026-02-28
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime
from pathlib import Path

import typer

from defaults.config import (
    CITY,
    CO_CONSULTANT_NAME,
    COLORS,
    COMPANY_NAME,
    CONSULTANT_NAME,
    COORDINATOR_NAME,
    COUNTRY,
    COVER_IMAGE,
    IMPLEMENTING_COMPANY,
    LEGAL_REPRESENTATIVE,
    LOGO_IMAGE,
    PROGRAM_NAME,
    PROJECT_CODE,
    PROJECT_DESCRIPTION,
    PROJECT_RUC,
    REPORT_DATE_END,
    REPORT_DATE_START,
    YEAR,
)

app = typer.Typer(help="Prepare AI context for implementation report generation")

PM_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PM_ROOT / "docs"
TEMPLATES_DIR = PM_ROOT / "templates"


def read_file_safe(path: Path) -> str | None:
    """Read a file, return None if it doesn't exist."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def read_text_input(path_str: str) -> str:
    """Read a text file provided by the user."""
    p = Path(path_str).expanduser()
    if not p.exists():
        typer.secho(f"  [WARN] File not found: {p}", fg=typer.colors.YELLOW)
        return f"[Archivo no encontrado: {path_str}]"
    return p.read_text(encoding="utf-8")


def build_config_section() -> str:
    """Build the project configuration section."""
    return f"""## Datos del Proyecto

- **Empresa beneficiaria**: {COMPANY_NAME}
- **RUC**: {PROJECT_RUC}
- **Representante legal**: {LEGAL_REPRESENTATIVE}
- **Codigo de proyecto**: {PROJECT_CODE}
- **Programa**: {PROGRAM_NAME}
- **Empresa implementadora**: {IMPLEMENTING_COMPANY}
- **Coordinador General**: {COORDINATOR_NAME}
- **Consultor**: {CONSULTANT_NAME}
- **Co-Consultor**: {CO_CONSULTANT_NAME}
- **Ciudad**: {CITY}
- **Pais**: {COUNTRY}
- **Ano**: {YEAR}
- **Fecha de informe**: {REPORT_DATE_START} -- {REPORT_DATE_END}
- **Imagen de portada**: {COVER_IMAGE}
- **Logo**: {LOGO_IMAGE}
- **Descripcion del proyecto**: {PROJECT_DESCRIPTION}
"""


def build_odoo_section(start_date: str, end_date: str) -> str:
    """Query Odoo and build the data section."""
    try:
        from helpers.odoo_query import connect, query_date_range, query_system_overview

        typer.secho("  Consultando Odoo...", fg=typer.colors.BLUE)
        client = connect()
        data = query_date_range(client, start_date, end_date)
        overview = query_system_overview(client)

        sections = []
        sections.append("## Datos de Odoo\n")
        sections.append(
            f"**Periodo consultado**: {start_date} a {end_date}\n"
        )

        total = sum(len(v) for v in data.values())
        sections.append(f"**Total de registros**: {total}\n")

        for model, records in data.items():
            if records:
                sections.append(f"\n### {model} ({len(records)} registros)\n")
                for r in records[:20]:  # Limit to 20 per model
                    name = r.get("name", r.get("display_name", str(r.get("id", ""))))
                    sections.append(f"- ID {r.get('id', '?')}: {name}")
                if len(records) > 20:
                    sections.append(f"- ... y {len(records) - 20} mas")

        modules = overview.get("installed_modules", [])
        if modules:
            sections.append(f"\n### Modulos instalados ({len(modules)})\n")
            for m in modules:
                name = m.get("shortdesc", m.get("name", "?"))
                sections.append(f"- {name}")

        typer.secho(
            f"  [OK] {total} registros, {len(modules)} modulos",
            fg=typer.colors.GREEN,
        )
        return "\n".join(sections)

    except Exception as e:
        typer.secho(f"  [ERROR] Odoo query failed: {e}", fg=typer.colors.RED)
        return "## Datos de Odoo\n\n[No se pudo conectar a Odoo]\n"


@app.command()
def prepare(
    start_date: str = typer.Option(None, help="Odoo query start date YYYY-MM-DD"),
    end_date: str = typer.Option(None, help="Odoo query end date YYYY-MM-DD"),
    diagnostico: str = typer.Option(
        None, help="Path to diagnostic report (.txt or .md)"
    ),
    plan: str = typer.Option(
        None, help="Path to implementation plan (.txt or .md)"
    ),
    sprints: str = typer.Option(
        None, help="Comma-separated paths to sprint review files"
    ),
    auto: bool = typer.Option(
        False, help="Auto-generate with Claude API (requires ANTHROPIC_API_KEY)"
    ),
    output: str = typer.Option(
        None, help="Output path for context file (default: generated/ai_context.md)"
    ),
):
    """Prepare AI context for implementation report generation.

    Without --auto: generates a context file to paste into any AI chat.
    With --auto: calls Claude API to generate the report automatically.
    """
    typer.secho("=" * 60, bold=True)
    typer.secho("  PREPARE REPORT CONTEXT", bold=True)
    typer.secho("=" * 60, bold=True)

    parts: list[str] = []

    # Header
    parts.append("# Contexto para Generar Informe de Implementacion\n")
    parts.append(
        f"Generado el {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    )

    # Instructions
    ai_instructions = read_file_safe(DOCS_DIR / "AI_INSTRUCTIONS.md")
    if ai_instructions:
        parts.append("---\n")
        parts.append(ai_instructions)

    # Config
    parts.append("---\n")
    parts.append(build_config_section())

    # Odoo data
    if start_date and end_date:
        parts.append("---\n")
        parts.append(build_odoo_section(start_date, end_date))

    # Input documents
    if diagnostico:
        parts.append("---\n")
        parts.append("## Informe de Diagnostico (documento de entrada)\n")
        parts.append(read_text_input(diagnostico))

    if plan:
        parts.append("\n---\n")
        parts.append("## Informe de Plan de Implementacion (documento de entrada)\n")
        parts.append(read_text_input(plan))

    if sprints:
        parts.append("\n---\n")
        parts.append("## Sprint Reviews (documentos de entrada)\n")
        for i, path in enumerate(sprints.split(","), 1):
            parts.append(f"\n### Sprint {i}\n")
            parts.append(read_text_input(path.strip()))

    # Template
    template = read_file_safe(TEMPLATES_DIR / "implementation.tex.template")
    if template:
        parts.append("\n---\n")
        parts.append("## Plantilla LaTeX (referencia de estructura)\n")
        parts.append("```latex\n")
        parts.append(template)
        parts.append("```\n")

    # Style guide summary
    parts.append("\n---\n")
    parts.append("## Reglas de Formato LaTeX\n")
    parts.append(
        """- Acentos: `\\'a`, `\\'e`, `\\'i`, `\\'o`, `\\'u`, `\\~n`
- Captions ARRIBA de `\\includegraphics`
- Linea en blanco antes de `\\begin{tabularx}`
- NO agregar `[leftmargin=...]` a listas individuales
- Usar `\\textbf{}` para enfasis, evitar `\\texttt{}` en columnas estrechas
- Redaccion formal, tercera persona, tiempo pasado
"""
    )

    # Final instruction
    parts.append("\n---\n")
    parts.append("## Instruccion Final\n\n")
    parts.append(
        "Con toda la informacion de arriba, genera el contenido completo "
        "para todas las secciones marcadas con `% TODO` en el archivo "
        "`implementation.tex`. Tambien genera los archivos `.puml` para "
        "los 4 diagramas (use_case, sequence_tour, sequence_reservation, "
        "data_model). Escribe el contenido directamente en LaTeX listo "
        "para copiar al archivo .tex.\n"
    )

    # Assemble
    context = "\n".join(parts)

    # Output
    if output:
        output_path = Path(output)
    else:
        output_dir = PM_ROOT / "generated"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "ai_context.md"

    output_path.write_text(context, encoding="utf-8")
    typer.secho(f"\n  [OK] Context file: {output_path}", fg=typer.colors.GREEN)
    typer.secho(f"  Size: {len(context):,} characters", fg=typer.colors.BLUE)

    if auto:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            typer.secho(
                "\n  [WARN] ANTHROPIC_API_KEY not set. Cannot auto-generate.",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                "  Use the context file above with your preferred AI chat instead.",
                fg=typer.colors.YELLOW,
            )
        else:
            typer.secho(
                "\n  [INFO] Claude API auto-generation not yet implemented.",
                fg=typer.colors.YELLOW,
            )
            typer.secho(
                "  For now, use the context file with Claude Code or claude.ai.",
                fg=typer.colors.YELLOW,
            )
    else:
        typer.secho("\nSiguientes pasos:", bold=True)
        typer.secho(
            f"  1. Abre {output_path.name} en tu editor de codigo"
        )
        typer.secho(
            "  2. Copia TODO el contenido al chat de IA de tu editor"
        )
        typer.secho(
            "     (Antigravity, Cursor, Claude Code, etc.)"
        )
        typer.secho(
            "  3. La IA generara el contenido LaTeX y los diagramas PlantUML"
        )
        typer.secho(
            "  4. Copia el resultado al archivo implementation.tex"
        )
        typer.secho(
            "  5. Compila: pdflatex implementation.tex (2 veces)"
        )


if __name__ == "__main__":
    app()
