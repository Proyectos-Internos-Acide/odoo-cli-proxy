#!/usr/bin/env python3
"""Create post-implementation report with rendered templates.

Usage:
    uv run python project_management/scripts/create_report.py implementation --format markdown
    uv run python project_management/scripts/create_report.py executive_summary --format latex
    uv run python project_management/scripts/create_report.py lessons_learned
    uv run python project_management/scripts/create_report.py implementation --start-date 2026-01-02 --end-date 2026-02-22
"""

import shutil
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

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
    GENERATED_DIR,
    LEGAL_REPRESENTATIVE,
    LOGO_IMAGE,
    PROGRAM_NAME,
    PROJECT_CODE,
    PROJECT_DATE,
    PROJECT_DESCRIPTION,
    PROJECT_ENTITY,
    PROJECT_RUC,
    PROJECT_SUBTITLE,
    REPORT_DATE_END,
    REPORT_DATE_START,
    REPORT_TYPES,
    YEAR,
)
from helpers.renderer import (
    render_template,
    build_all_data_sections,
    evidence_to_latex,
    evidence_to_md,
)

app = typer.Typer(help="Create post-implementation reports")

PM_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PM_ROOT / "templates"


@app.command()
def create(
    report_type: str = typer.Argument(
        ..., help=f"Report type: {', '.join(REPORT_TYPES)}"
    ),
    fmt: str = typer.Option(
        "markdown", "--format", help="Output format: latex or markdown"
    ),
    start_date: str = typer.Option(
        None, help="Odoo query start date YYYY-MM-DD"
    ),
    end_date: str = typer.Option(
        None, help="Odoo query end date YYYY-MM-DD"
    ),
    with_pdf: bool = typer.Option(
        False, help="Also convert markdown to PDF (only with --format markdown)"
    ),
    evidence: str = typer.Option(
        None, help="Comma-separated evidence image paths"
    ),
    project_code: str = typer.Option(PROJECT_CODE, help="Project code"),
    entity_name: str = typer.Option(PROJECT_ENTITY, help="Entity/company name"),
    ruc: str = typer.Option(PROJECT_RUC, help="RUC number"),
    report_date: str = typer.Option(PROJECT_DATE, help="Report date text"),
):
    """Create a post-implementation report from templates."""
    if report_type not in REPORT_TYPES:
        typer.secho(
            f"  [ERROR] Unknown report type: {report_type}", fg=typer.colors.RED
        )
        typer.secho(f"  Available: {', '.join(REPORT_TYPES)}")
        raise typer.Exit(1)

    if fmt not in ("latex", "markdown"):
        typer.secho("  [ERROR] --format must be 'latex' or 'markdown'", fg=typer.colors.RED)
        raise typer.Exit(1)

    # Output directory
    report_dir = PM_ROOT / GENERATED_DIR / "reports" / report_type
    img_dir = report_dir / "img"
    img_dir.mkdir(parents=True, exist_ok=True)

    # Template selection
    ext = "tex" if fmt == "latex" else "md"
    template_name = f"{report_type}.{ext}.template"
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        typer.secho(
            f"  [ERROR] Template not found: {template_path}", fg=typer.colors.RED
        )
        raise typer.Exit(1)

    typer.secho("=" * 60, bold=True)
    typer.secho(f"  CREATE REPORT: {report_type} ({fmt})", bold=True)
    typer.secho("=" * 60, bold=True)

    # Build replacements
    replacements: dict[str, str] = {
        # Company
        "COMPANY_NAME": COMPANY_NAME,
        "ENTITY_NAME_UPPER": entity_name.upper().replace(
            r"A\&F", r"A \& F"
        ) if r"\&" in entity_name else entity_name.upper(),
        "PROJECT_SUBTITLE": PROJECT_SUBTITLE,
        "PROJECT_DESCRIPTION": PROJECT_DESCRIPTION,
        "RUC": ruc,
        "LEGAL_REPRESENTATIVE": LEGAL_REPRESENTATIVE,
        # Project
        "PROJECT_CODE": project_code,
        "PROGRAM_NAME": PROGRAM_NAME,
        "REPORT_DATE": report_date,
        "REPORT_DATE_START": REPORT_DATE_START,
        "REPORT_DATE_END": REPORT_DATE_END,
        # People
        "COORDINATOR_NAME": COORDINATOR_NAME,
        "CONSULTANT_NAME": CONSULTANT_NAME,
        "CO_CONSULTANT_NAME": CO_CONSULTANT_NAME,
        # Location
        "CITY": CITY,
        "COUNTRY": COUNTRY,
        "YEAR": YEAR,
        # Images
        "COVER_IMAGE": COVER_IMAGE,
        "LOGO_IMAGE": LOGO_IMAGE,
        # Colors
        "PRIMARY_COLOR": COLORS["primary"],
        "ACCENT_COLOR": COLORS["accent"],
        "SUCCESS_COLOR": COLORS["success"],
        "WARN_COLOR": COLORS["warn"],
    }

    # Optional Odoo query
    if start_date and end_date:
        typer.secho("  Querying Odoo...", fg=typer.colors.BLUE)
        from helpers.odoo_query import (
            connect,
            query_date_range,
            query_system_overview,
            MODEL_LABELS,
        )

        client = connect()
        data = query_date_range(client, start_date, end_date)
        total = sum(len(v) for v in data.values())
        typer.secho(f"  [ODOO] {total} records found", fg=typer.colors.GREEN)

        # Dynamic totals: TOTAL_RECORDS, TOTAL_PRODUCTS, TOTAL_CATEGORIES, etc.
        replacements["TOTAL_RECORDS"] = str(total)
        for key in data:
            replacements[f"TOTAL_{key.upper()}"] = str(len(data[key]))

        # Build data sections for implementation report
        replacements["ODOO_DATA_SECTIONS"] = build_all_data_sections(
            data, MODEL_LABELS, fmt
        )

        # System overview
        overview = query_system_overview(client)
        replacements["TOTAL_MODULES"] = str(
            len(overview.get("installed_modules", []))
        )
    elif start_date or end_date:
        typer.secho(
            "  [WARN] Both --start-date and --end-date required for Odoo query",
            fg=typer.colors.YELLOW,
        )

    # Evidence images
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
                typer.secho(
                    f"  [WARN] File not found: {src} (reference added anyway)",
                    fg=typer.colors.YELLOW,
                )

        if fmt == "latex":
            replacements["EVIDENCE_IMAGES"] = evidence_to_latex(copied_names)
        else:
            replacements["EVIDENCE_IMAGES"] = evidence_to_md(copied_names)
    else:
        if fmt == "latex":
            replacements["EVIDENCE_IMAGES"] = "% TODO: Agregar evidencia visual"
        else:
            replacements["EVIDENCE_IMAGES"] = "<!-- TODO: Agregar evidencia visual -->"

    # Render and write
    rendered = render_template(template_path, replacements)
    output_name = template_name.replace(".template", "")
    output_path = report_dir / output_name
    output_path.write_text(rendered, encoding="utf-8")
    typer.secho(f"  [CREATED] {output_name}", fg=typer.colors.GREEN)
    typer.secho(f"  [CREATED] img/", fg=typer.colors.GREEN)

    # Optional markdown -> PDF
    if with_pdf and fmt == "markdown":
        from helpers.md_to_pdf import md_to_pdf

        typer.secho("\n  Converting markdown to PDF...", fg=typer.colors.BLUE)
        success, msg = md_to_pdf(output_path)
        if success:
            typer.secho(f"  [PDF] {msg}", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  [FAILED] {msg}", fg=typer.colors.RED)

    typer.secho(
        f"\nReport ready at: {report_dir.relative_to(PM_ROOT)}",
        fg=typer.colors.BLUE,
        bold=True,
    )
    typer.secho("Next steps:", bold=True)
    typer.secho(f"  1. Edit the .{ext} file to fill in report content")
    typer.secho("  2. Place screenshots/evidence in the img/ folder")
    typer.secho(
        f"  3. Run: uv run python project_management/scripts/compile_report.py {report_type}"
    )


if __name__ == "__main__":
    app()
