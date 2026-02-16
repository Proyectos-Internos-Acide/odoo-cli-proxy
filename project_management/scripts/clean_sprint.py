#!/usr/bin/env python3
"""Clean LaTeX auxiliary files from sprint folders.

Usage:
    uv run python project_management/scripts/clean_sprint.py 4
    uv run python project_management/scripts/clean_sprint.py --all
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import typer

from defaults.config import AUX_EXTENSIONS, GENERATED_DIR

app = typer.Typer(help="Clean LaTeX auxiliary files from sprint folders")

PM_ROOT = Path(__file__).resolve().parent.parent


def clean_directory(directory: Path) -> int:
    """Remove auxiliary files from a directory. Returns count of removed files."""
    removed = 0
    for ext in AUX_EXTENSIONS:
        for f in directory.glob(f"*{ext}"):
            f.unlink()
            removed += 1
    return removed


@app.command()
def clean(
    sprint_number: int = typer.Argument(
        None, help="Sprint number to clean (e.g. 4)"
    ),
    all: bool = typer.Option(False, "--all", help="Clean all sprint folders"),
):
    """Remove .aux, .log, .out and other auxiliary files."""
    sprints_dir = PM_ROOT / GENERATED_DIR / "sprints"

    if all:
        if not sprints_dir.exists():
            typer.secho("  [WARN] No sprints directory found", fg=typer.colors.YELLOW)
            raise typer.Exit(1)
        sprint_dirs = sorted(sprints_dir.glob("sprint_*"))
    elif sprint_number is not None:
        sprint_dir = sprints_dir / f"sprint_{sprint_number}"
        if not sprint_dir.exists():
            typer.secho(f"  [ERROR] Sprint folder not found: {sprint_dir}", fg=typer.colors.RED)
            raise typer.Exit(1)
        sprint_dirs = [sprint_dir]
    else:
        typer.secho("  [ERROR] Provide a sprint number or use --all", fg=typer.colors.RED)
        raise typer.Exit(1)

    total_removed = 0
    for d in sprint_dirs:
        removed = clean_directory(d)
        if removed > 0:
            typer.secho(f"  [CLEANED] {d.name}: {removed} files removed", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  [OK] {d.name}: already clean", fg=typer.colors.GREEN)
        total_removed += removed

    typer.secho(
        f"\nDone. {total_removed} auxiliary files removed.",
        fg=typer.colors.BLUE,
        bold=True,
    )


if __name__ == "__main__":
    app()
