#!/usr/bin/env python3
"""Clean ALL generated files for project switch.

Removes reports, sprints, and generated context — everything in generated/
except .gitkeep. Use this when switching to a new company/project.

Usage:
    # Preview what will be deleted (dry run)
    uv run python project_management/scripts/clean_project.py

    # Actually delete everything
    uv run python project_management/scripts/clean_project.py --confirm

    # Clean only a specific area
    uv run python project_management/scripts/clean_project.py --only reports
    uv run python project_management/scripts/clean_project.py --only sprints
    uv run python project_management/scripts/clean_project.py --only context
"""

import shutil
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import typer

from defaults.config import GENERATED_DIR

app = typer.Typer(help="Clean all generated files for project switch")

PM_ROOT = Path(__file__).resolve().parent.parent
GEN_DIR = PM_ROOT / GENERATED_DIR

KEEP_FILES = {".gitkeep"}


def count_files(directory: Path) -> tuple[int, int]:
    """Count files and total size in a directory recursively."""
    count = 0
    size = 0
    if directory.exists():
        for f in directory.rglob("*"):
            if f.is_file() and f.name not in KEEP_FILES:
                count += 1
                size += f.stat().st_size
    return count, size


def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def clean_directory(directory: Path, dry_run: bool = True) -> tuple[int, int]:
    """Remove all files in directory except .gitkeep. Returns (count, size)."""
    removed_count = 0
    removed_size = 0

    if not directory.exists():
        return 0, 0

    for item in sorted(directory.rglob("*"), reverse=True):
        if item.name in KEEP_FILES:
            continue
        if item.is_file():
            removed_count += 1
            removed_size += item.stat().st_size
            if not dry_run:
                item.unlink()
        elif item.is_dir() and not dry_run:
            try:
                item.rmdir()
            except OSError:
                pass  # Not empty yet, skip

    return removed_count, removed_size


@app.command()
def clean(
    confirm: bool = typer.Option(
        False, "--confirm", help="Actually delete files (without this flag, only previews)"
    ),
    only: str = typer.Option(
        None, help="Clean only: reports, sprints, or context"
    ),
):
    """Clean generated files for project switch.

    Without --confirm, shows a preview of what would be deleted.
    """
    typer.secho("=" * 60, bold=True)
    if confirm:
        typer.secho("  CLEAN PROJECT (DELETING FILES)", bold=True, fg=typer.colors.RED)
    else:
        typer.secho("  CLEAN PROJECT (DRY RUN - preview only)", bold=True)
    typer.secho("=" * 60, bold=True)

    targets: dict[str, Path] = {}

    if only:
        if only == "reports":
            targets["reports"] = GEN_DIR / "reports"
        elif only == "sprints":
            targets["sprints"] = GEN_DIR / "sprints"
        elif only == "context":
            targets["context"] = GEN_DIR
        else:
            typer.secho(
                f"  [ERROR] Unknown target: {only}. Use: reports, sprints, context",
                fg=typer.colors.RED,
            )
            raise typer.Exit(1)
    else:
        targets = {
            "reports": GEN_DIR / "reports",
            "sprints": GEN_DIR / "sprints",
            "context": GEN_DIR,
        }

    total_files = 0
    total_size = 0

    for name, path in targets.items():
        if name == "context":
            # Only clean loose files in generated/ (ai_context.md, etc.)
            count = 0
            size = 0
            if path.exists():
                for f in path.iterdir():
                    if f.is_file() and f.name not in KEEP_FILES:
                        count += 1
                        size += f.stat().st_size
                        if confirm:
                            f.unlink()
            if count > 0:
                action = "Deleted" if confirm else "Would delete"
                typer.secho(
                    f"  [{action}] {name}: {count} files ({format_size(size)})",
                    fg=typer.colors.GREEN if confirm else typer.colors.YELLOW,
                )
            else:
                typer.secho(f"  [OK] {name}: already clean", fg=typer.colors.GREEN)
            total_files += count
            total_size += size
        else:
            if not path.exists():
                typer.secho(f"  [OK] {name}: does not exist", fg=typer.colors.GREEN)
                continue

            # List subdirectories
            subdirs = sorted(
                [d for d in path.iterdir() if d.is_dir()]
            )

            for subdir in subdirs:
                count, size = count_files(subdir)
                if count > 0:
                    action = "Deleted" if confirm else "Would delete"
                    typer.secho(
                        f"  [{action}] {name}/{subdir.name}: {count} files ({format_size(size)})",
                        fg=typer.colors.GREEN if confirm else typer.colors.YELLOW,
                    )
                    if confirm:
                        shutil.rmtree(subdir)
                    total_files += count
                    total_size += size

    typer.secho(f"\n  Total: {total_files} files ({format_size(total_size)})", bold=True)

    if not confirm and total_files > 0:
        typer.secho(
            "\n  This was a DRY RUN. To actually delete, run with --confirm",
            fg=typer.colors.YELLOW,
            bold=True,
        )


if __name__ == "__main__":
    app()
