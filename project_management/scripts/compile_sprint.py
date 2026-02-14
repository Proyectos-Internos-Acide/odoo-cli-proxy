#!/usr/bin/env python3
"""Compile sprint files (LaTeX or Markdown) to PDF.

Usage:
    uv run python project_management/scripts/compile_sprint.py 4
    uv run python project_management/scripts/compile_sprint.py 4 --file sprint_review.tex
    uv run python project_management/scripts/compile_sprint.py 5 --file sprint_review.md
"""

import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import typer

from defaults.config import GENERATED_DIR, LATEX_ARGS, LATEX_CMD
from helpers.md_to_pdf import md_to_pdf

app = typer.Typer(help="Compile sprint files to PDF")

PM_ROOT = Path(__file__).resolve().parent.parent


@app.command()
def compile(
    sprint_number: int = typer.Argument(..., help="Sprint number (e.g. 4)"),
    file: str = typer.Option(
        None, help="Specific .tex or .md file to compile (default: all)"
    ),
    passes: int = typer.Option(1, help="Number of pdflatex passes (default: 1)"),
):
    """Compile .tex and .md files in sprint_N/ folder to PDF."""
    sprint_dir = PM_ROOT / GENERATED_DIR / "sprints" / f"sprint_{sprint_number}"

    if not sprint_dir.exists():
        typer.secho(f"  [ERROR] Sprint folder not found: {sprint_dir}", fg=typer.colors.RED)
        raise typer.Exit(1)

    if file:
        target_files = [sprint_dir / file]
        if not target_files[0].exists():
            typer.secho(f"  [ERROR] File not found: {target_files[0]}", fg=typer.colors.RED)
            raise typer.Exit(1)
    else:
        tex_files = sorted(sprint_dir.glob("*.tex"))
        md_files = sorted(sprint_dir.glob("*.md"))
        target_files = tex_files + md_files

    if not target_files:
        typer.secho("  [WARN] No .tex or .md files found", fg=typer.colors.YELLOW)
        raise typer.Exit(1)

    typer.secho("=" * 60, bold=True)
    typer.secho(f"  COMPILE SPRINT {sprint_number}", bold=True)
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
                    cwd=sprint_dir,
                    capture_output=True,
                    text=True,
                    encoding="latin-1",
                    errors="replace",
                )
                if result.returncode != 0:
                    typer.secho(f"     [FAILED] Exit code {result.returncode}", fg=typer.colors.RED)
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
