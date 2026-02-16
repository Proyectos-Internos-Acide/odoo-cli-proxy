#!/usr/bin/env python3
"""Create sprint folder structure with rendered templates.

Usage:
    uv run python project_management/scripts/create_sprint.py 4 --period "10 de Febrero, 2026 -- 21 de Febrero, 2026"
    uv run python project_management/scripts/create_sprint.py 5 --period "26 Ene -- 31 Ene" --start-date 2026-01-26 --end-date 2026-02-01 --format markdown
    uv run python project_management/scripts/create_sprint.py 5 --period "26 Ene -- 31 Ene" --format markdown --with-pdf --evidence img1.png,img2.png
"""

import shutil
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import typer

from defaults.config import (
    COLORS,
    COMPANY_NAME,
    GENERATED_DIR,
    PROJECT_DESCRIPTION,
    PROJECT_SUBTITLE,
)
from helpers.renderer import (
    render_template,
    build_all_data_sections,
    summary_to_latex_rows,
    summary_to_md_rows,
    evidence_to_latex,
    evidence_to_md,
)

app = typer.Typer(help="Create sprint folder structure with templates")

PM_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PM_ROOT / "templates"


def _build_odoo_replacements(
    data: dict, summary: list[dict], fmt: str
) -> dict[str, str]:
    """Build template replacements from Odoo query results."""
    from helpers.odoo_query import MODEL_LABELS

    is_latex = fmt == "latex"
    replacements: dict[str, str] = {}

    # All data sections (tables for each model with results)
    if data:
        replacements["ODOO_DATA_SECTIONS"] = build_all_data_sections(
            data, MODEL_LABELS, fmt
        )
    else:
        comment = (
            "% TODO: Agregar configuracion de Odoo"
            if is_latex
            else "<!-- TODO: Agregar configuracion de Odoo -->"
        )
        replacements["ODOO_DATA_SECTIONS"] = comment

    # Summary table
    if summary:
        if is_latex:
            replacements["CONFIG_SUMMARY_TABLE"] = summary_to_latex_rows(summary)
        else:
            replacements["CONFIG_SUMMARY_TABLE"] = summary_to_md_rows(summary)
    else:
        comment = (
            "% TODO: Agregar resumen"
            if is_latex
            else "<!-- TODO: Agregar resumen -->"
        )
        replacements["CONFIG_SUMMARY_TABLE"] = comment

    # Odoo summary section (one-liner for sprint review)
    total = sum(len(v) for v in data.values())
    if total > 0:
        parts = []
        for key, records in data.items():
            label = MODEL_LABELS.get(key, key)
            short = label.split("(")[0].strip().lower()
            parts.append(f"{len(records)} {short}")
        detail = ", ".join(parts)
        if is_latex:
            replacements["ODOO_SUMMARY_SECTION"] = (
                f"Se configuraron \\textbf{{{total}}} registros en Odoo: {detail}."
            )
        else:
            replacements["ODOO_SUMMARY_SECTION"] = (
                f"Se configuraron **{total}** registros en Odoo: {detail}."
            )
    else:
        comment = (
            "% TODO: Agregar resumen de configuracion"
            if is_latex
            else "<!-- TODO: Agregar resumen de configuracion -->"
        )
        replacements["ODOO_SUMMARY_SECTION"] = comment

    # Dynamic totals: TOTAL_RECORDS, TOTAL_PRODUCTS, TOTAL_CATEGORIES, etc.
    replacements["TOTAL_RECORDS"] = str(total)
    for key in data:
        replacements[f"TOTAL_{key.upper()}"] = str(len(data[key]))

    return replacements


@app.command()
def create(
    sprint_number: int = typer.Argument(..., help="Sprint number (e.g. 4)"),
    period: str = typer.Option(
        "TBD", help="Sprint period text for display"
    ),
    start_date: str = typer.Option(
        None, help="Query start date YYYY-MM-DD (queries Odoo if provided)"
    ),
    end_date: str = typer.Option(
        None, help="Query end date YYYY-MM-DD"
    ),
    fmt: str = typer.Option(
        "latex", "--format", help="Output format: latex or markdown"
    ),
    with_pdf: bool = typer.Option(
        False, help="Also convert markdown to PDF (only with --format markdown)"
    ),
    evidence: str = typer.Option(
        None, help="Comma-separated evidence image file paths"
    ),
):
    """Create sprint_N/ folder with rendered templates."""
    if fmt not in ("latex", "markdown"):
        typer.secho("  [ERROR] --format must be 'latex' or 'markdown'", fg=typer.colors.RED)
        raise typer.Exit(1)

    sprint_dir = PM_ROOT / GENERATED_DIR / "sprints" / f"sprint_{sprint_number}"
    img_dir = sprint_dir / "img"

    if sprint_dir.exists():
        typer.secho(
            f"  [SKIP] {sprint_dir.relative_to(PM_ROOT)} already exists",
            fg=typer.colors.YELLOW,
        )
        raise typer.Exit(1)

    img_dir.mkdir(parents=True, exist_ok=True)

    # --- Base replacements (config values) ---
    replacements: dict[str, str] = {
        "SPRINT_NUMBER": str(sprint_number),
        "COMPANY_NAME": COMPANY_NAME,
        "PROJECT_SUBTITLE": PROJECT_SUBTITLE,
        "PERIOD": period,
        "PROJECT_DESCRIPTION": PROJECT_DESCRIPTION,
        "PRIMARY_COLOR": COLORS["primary"],
        "ACCENT_COLOR": COLORS["accent"],
        "SUCCESS_COLOR": COLORS["success"],
        "WARN_COLOR": COLORS["warn"],
    }

    # --- Odoo query (optional) ---
    data: dict = {}
    summary: list[dict] = []

    if start_date and end_date:
        typer.secho("  Querying Odoo...", fg=typer.colors.BLUE)
        from helpers.odoo_query import connect, query_date_range, build_summary_table

        client = connect()
        data = query_date_range(client, start_date, end_date)
        summary = build_summary_table(data)

        total = sum(len(v) for v in data.values())
        typer.secho(f"  [ODOO] {total} records found", fg=typer.colors.GREEN)
    elif start_date or end_date:
        typer.secho(
            "  [WARN] Both --start-date and --end-date required for Odoo query",
            fg=typer.colors.YELLOW,
        )

    odoo_replacements = _build_odoo_replacements(data, summary, fmt)
    replacements.update(odoo_replacements)

    # --- Evidence images ---
    if evidence:
        image_paths = [p.strip() for p in evidence.split(",") if p.strip()]
        copied_names = []
        for src in image_paths:
            src_path = Path(src)
            if src_path.exists():
                dest = img_dir / src_path.name
                shutil.copy2(src_path, dest)
                copied_names.append(f"img/{src_path.name}")
                typer.secho(f"  [COPIED] {src_path.name} -> img/", fg=typer.colors.GREEN)
            else:
                copied_names.append(f"img/{src_path.name}")
                typer.secho(f"  [WARN] File not found: {src} (reference added anyway)", fg=typer.colors.YELLOW)

        if fmt == "latex":
            replacements["EVIDENCE_IMAGES"] = evidence_to_latex(copied_names)
        else:
            replacements["EVIDENCE_IMAGES"] = evidence_to_md(copied_names)
    else:
        if fmt == "latex":
            replacements["EVIDENCE_IMAGES"] = "% TODO: Agregar evidencia visual"
        else:
            replacements["EVIDENCE_IMAGES"] = "<!-- TODO: Agregar evidencia visual -->"

    # --- Render templates ---
    typer.secho("=" * 60, bold=True)
    typer.secho(f"  CREATE SPRINT {sprint_number} ({fmt})", bold=True)
    typer.secho("=" * 60, bold=True)

    ext = "tex" if fmt == "latex" else "md"
    template_names = [
        f"sprint_review.{ext}.template",
        f"product_increment.{ext}.template",
    ]

    for template_name in template_names:
        template_path = TEMPLATES_DIR / template_name
        if not template_path.exists():
            typer.secho(f"  [ERROR] Template not found: {template_path}", fg=typer.colors.RED)
            continue

        output_name = template_name.replace(".template", "")
        rendered = render_template(template_path, replacements)
        output_path = sprint_dir / output_name
        output_path.write_text(rendered, encoding="utf-8")
        typer.secho(f"  [CREATED] {output_name}", fg=typer.colors.GREEN)

    typer.secho(f"  [CREATED] img/", fg=typer.colors.GREEN)

    # --- Optional markdown -> PDF ---
    if with_pdf and fmt == "markdown":
        from helpers.md_to_pdf import md_to_pdf

        typer.secho("\n  Converting markdown to PDF...", fg=typer.colors.BLUE)
        for md_file in sorted(sprint_dir.glob("*.md")):
            success, msg = md_to_pdf(md_file)
            if success:
                typer.secho(f"  [PDF] {msg}", fg=typer.colors.GREEN)
            else:
                typer.secho(f"  [FAILED] {msg}", fg=typer.colors.RED)

    typer.secho(
        f"\nSprint folder ready at: {sprint_dir.relative_to(PM_ROOT)}",
        fg=typer.colors.BLUE,
        bold=True,
    )
    typer.secho("Next steps:", bold=True)
    typer.secho(f"  1. Edit the .{ext} files to fill in sprint content")
    typer.secho("  2. Place screenshots in the img/ folder")
    typer.secho(
        f"  3. Run: uv run python project_management/scripts/compile_sprint.py {sprint_number}"
    )


if __name__ == "__main__":
    app()
