#!/usr/bin/env python3
"""Compile report files (LaTeX or Markdown) to PDF.

Usage:
    uv run python project_management/scripts/compile_report.py implementation
    uv run python project_management/scripts/compile_report.py lessons_learned --file lessons_learned.md
    uv run python project_management/scripts/compile_report.py implementation --passes 2
"""

import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import typer

from defaults.config import GENERATED_DIR, LATEX_ARGS, LATEX_CMD, REPORT_TYPES
from helpers.md_to_pdf import md_to_pdf

app = typer.Typer(help="Compile report files to PDF")

PM_ROOT = Path(__file__).resolve().parent.parent


@app.command()
def compile(
    report_type: str = typer.Argument(
        ..., help=f"Report type: {', '.join(REPORT_TYPES)}"
    ),
    file: str = typer.Option(
        None, help="Specific .tex or .md file to compile (default: all)"
    ),
    passes: int = typer.Option(
        2, help="Number of pdflatex passes (default: 2 for TOC)"
    ),
):
    """Compile .tex or .md files in a report folder to PDF."""
    if report_type not in REPORT_TYPES:
        typer.secho(
            f"  [ERROR] Unknown report type: {report_type}", fg=typer.colors.RED
        )
        typer.secho(f"  Available: {', '.join(REPORT_TYPES)}")
        raise typer.Exit(1)

    report_dir = PM_ROOT / GENERATED_DIR / "reports" / report_type

    if not report_dir.exists():
        typer.secho(
            f"  [ERROR] Report folder not found: {report_dir}", fg=typer.colors.RED
        )
        raise typer.Exit(1)

    if file:
        target_files = [report_dir / file]
        if not target_files[0].exists():
            typer.secho(
                f"  [ERROR] File not found: {target_files[0]}", fg=typer.colors.RED
            )
            raise typer.Exit(1)
    else:
        tex_files = sorted(report_dir.glob("*.tex"))
        md_files = sorted(report_dir.glob("*.md"))
        target_files = tex_files + md_files

    if not target_files:
        typer.secho("  [WARN] No .tex or .md files found", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    typer.secho("=" * 60, bold=True)
    typer.secho(f"  COMPILE REPORT: {report_type}", bold=True)
    typer.secho("=" * 60, bold=True)

    success_count = 0
    for target_file in target_files:
        typer.secho(f"\n  -> {target_file.name}", bold=True)

        if target_file.suffix == ".tex":
            cmd = [LATEX_CMD, *LATEX_ARGS, target_file.name]
            for pass_num in range(1, passes + 1):
                if passes > 1:
                    typer.secho(f"     Pass {pass_num}/{passes}...")
                result = subprocess.run(
                    cmd,
                    cwd=report_dir,
                    capture_output=True,
                    text=True,
                    encoding="latin-1",
                    errors="replace",
                )
                if result.returncode != 0:
                    typer.secho(
                        f"     [FAILED] Exit code {result.returncode}",
                        fg=typer.colors.RED,
                    )
                    last_lines = result.stdout.strip().split("\n")[-5:]
                    for line in last_lines:
                        typer.secho(f"     {line}", fg=typer.colors.RED)
                    break
            else:
                pdf_name = target_file.stem + ".pdf"
                typer.secho(f"     [OK] {pdf_name}", fg=typer.colors.GREEN)
                success_count += 1

        elif target_file.suffix == ".md":
            success, msg = md_to_pdf(target_file)
            if success:
                typer.secho(f"     [OK] {msg}", fg=typer.colors.GREEN)
                success_count += 1
            else:
                typer.secho(f"     [FAILED] {msg}", fg=typer.colors.RED)

    typer.secho(
        f"\nDone. {success_count}/{len(target_files)} files compiled successfully.",
        fg=typer.colors.BLUE,
        bold=True,
    )


if __name__ == "__main__":
    app()
