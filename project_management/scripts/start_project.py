#!/usr/bin/env python3
"""Interactive project setup and report generation wizard.

Main entry point for generating implementation reports. Detects existing
project state and guides the user through setup or continuation.

Usage:
    uv run python project_management/scripts/start_project.py
"""

import shutil
import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path

import typer

from defaults.config import GENERATED_DIR

app = typer.Typer(help="Interactive project setup for implementation reports")

PM_ROOT = Path(__file__).resolve().parent.parent
GEN_DIR = PM_ROOT / GENERATED_DIR
REPORT_DIR = GEN_DIR / "reports" / "implementation"
SCRIPTS_DIR = PM_ROOT / "scripts"
CONFIG_PATH = PM_ROOT / "defaults" / "config.py"


# =========================================================================
# Project state detection
# =========================================================================

def detect_project_state() -> dict:
    """Detect what exists in the current generated/ folder."""
    state = {
        "has_report": False,
        "has_tex": False,
        "has_pdf": False,
        "has_cover": False,
        "has_logo": False,
        "has_diagrams": False,
        "has_screenshots": False,
        "has_context": False,
        "missing_images": [],
        "todo_count": 0,
        "company_name": "",
    }

    # Check report directory
    if REPORT_DIR.exists():
        state["has_report"] = True
        tex_file = REPORT_DIR / "implementation.tex"
        if tex_file.exists():
            state["has_tex"] = True
            content = tex_file.read_text(encoding="utf-8")
            state["todo_count"] = content.count("% TODO")
        if (REPORT_DIR / "implementation.pdf").exists():
            state["has_pdf"] = True

        # Check images
        img_dir = REPORT_DIR / "img"
        if img_dir.exists():
            images = [f.name for f in img_dir.iterdir() if f.is_file()]
            state["has_cover"] = any(
                f.lower().startswith("visepro") or "portada" in f.lower()
                for f in images
            )
            state["has_logo"] = any(
                "logo" in f.lower() for f in images
            )
            state["has_screenshots"] = len([
                f for f in images
                if f.endswith(".png") and "logo" not in f.lower()
                and "portada" not in f.lower()
            ]) > 3

        # Check diagrams
        diag_dir = REPORT_DIR / "diagrams"
        if diag_dir.exists():
            pumls = list(diag_dir.glob("*.puml"))
            state["has_diagrams"] = len(pumls) >= 2

    # Check context
    context_file = GEN_DIR / "ai_context.md"
    state["has_context"] = context_file.exists()

    # Read company name from config
    try:
        from defaults.config import COMPANY_NAME
        state["company_name"] = COMPANY_NAME.replace(r"\&", "&")
    except Exception:
        pass

    return state


def print_status(state: dict):
    """Print a summary of the current project state."""
    check = lambda v: typer.style("OK", fg=typer.colors.GREEN) if v else typer.style("FALTA", fg=typer.colors.RED)

    typer.secho(f"\n  Proyecto: {state['company_name']}", bold=True)
    typer.secho(f"  {'─' * 50}")
    typer.echo(f"  Archivo .tex         : {check(state['has_tex'])}")
    typer.echo(f"  PDF compilado        : {check(state['has_pdf'])}")
    typer.echo(f"  Imagen de portada    : {check(state['has_cover'])}")
    typer.echo(f"  Logo de empresa      : {check(state['has_logo'])}")
    typer.echo(f"  Capturas de pantalla : {check(state['has_screenshots'])}")
    typer.echo(f"  Diagramas PlantUML   : {check(state['has_diagrams'])}")
    typer.echo(f"  Contexto IA          : {check(state['has_context'])}")

    if state["has_tex"]:
        todo_color = typer.colors.RED if state["todo_count"] > 0 else typer.colors.GREEN
        typer.secho(
            f"  Secciones pendientes : {state['todo_count']} TODOs",
            fg=todo_color,
        )
    typer.echo()


# =========================================================================
# Interactive prompts
# =========================================================================

def prompt_existing_project(state: dict) -> str:
    """Ask user what to do with an existing project."""
    typer.secho(
        "  Ya existe un proyecto en generated/reports/implementation/",
        fg=typer.colors.YELLOW,
        bold=True,
    )
    print_status(state)

    typer.echo("  Opciones:")
    typer.echo("    1. Continuar con el proyecto actual")
    typer.echo("    2. Limpiar todo y empezar un proyecto nuevo")
    typer.echo("    3. Salir")

    choice = typer.prompt("  Selecciona", default="1")
    return choice.strip()


def prompt_missing_data(state: dict):
    """Guide user through missing data for the current project."""
    missing = []

    if not state["has_cover"]:
        missing.append(
            "Imagen de portada: copiar archivo JPG/PNG a img/ "
            "(nombre configurado en config.py como COVER_IMAGE)"
        )
    if not state["has_logo"]:
        missing.append(
            "Logo de la empresa: copiar archivo PNG a img/ "
            "(nombre configurado en config.py como LOGO_IMAGE)"
        )
    if not state["has_screenshots"]:
        missing.append(
            "Capturas de pantalla del sistema: copiar PNGs de cada modulo a img/ "
            "(planning.png, modulo_agencia.png, etc.)"
        )
    if not state["has_diagrams"]:
        missing.append(
            "Diagramas PlantUML: crear archivos .puml en diagrams/ "
            "(use_case.puml, sequence_tour.puml, data_model.puml)"
        )
    if state["todo_count"] > 0:
        missing.append(
            f"Contenido del informe: {state['todo_count']} secciones TODO pendientes. "
            "Genera contexto IA para completarlas automaticamente."
        )

    if not missing:
        typer.secho(
            "  El proyecto esta completo. Solo queda compilar.",
            fg=typer.colors.GREEN,
            bold=True,
        )
        return

    typer.secho("  Datos faltantes:", fg=typer.colors.YELLOW, bold=True)
    for i, item in enumerate(missing, 1):
        typer.echo(f"    {i}. {item}")
    typer.echo()


def prompt_config_data() -> dict:
    """Interactively collect project configuration from the user."""
    typer.secho("\n  Datos del nuevo proyecto:", bold=True)
    typer.secho("  (Enter para mantener el valor actual)\n")

    from defaults.config import (
        CITY,
        CO_CONSULTANT_NAME,
        COMPANY_NAME,
        CONSULTANT_NAME,
        COORDINATOR_NAME,
        COUNTRY,
        COVER_IMAGE,
        LOGO_IMAGE,
        PROJECT_CODE,
        PROJECT_DESCRIPTION,
        PROJECT_RUC,
        REPORT_DATE_END,
        REPORT_DATE_START,
        YEAR,
    )

    data = {}
    data["COMPANY_NAME"] = typer.prompt(
        "  Razon social (LaTeX)", default=COMPANY_NAME
    )
    data["PROJECT_RUC"] = typer.prompt("  RUC", default=PROJECT_RUC)
    data["PROJECT_CODE"] = typer.prompt(
        "  Codigo de proyecto (LaTeX)", default=PROJECT_CODE
    )
    data["PROJECT_DESCRIPTION"] = typer.prompt(
        "  Descripcion del proyecto (LaTeX)", default=PROJECT_DESCRIPTION
    )
    data["COORDINATOR_NAME"] = typer.prompt(
        "  Coordinador General", default=COORDINATOR_NAME
    )
    data["CONSULTANT_NAME"] = typer.prompt(
        "  Consultor", default=CONSULTANT_NAME
    )
    data["CO_CONSULTANT_NAME"] = typer.prompt(
        "  Co-Consultor (LaTeX)", default=CO_CONSULTANT_NAME
    )
    data["CITY"] = typer.prompt("  Ciudad", default=CITY)
    data["COUNTRY"] = typer.prompt("  Pais (LaTeX)", default=COUNTRY)
    data["YEAR"] = typer.prompt("  Ano", default=YEAR)
    data["REPORT_DATE_START"] = typer.prompt(
        "  Fecha inicio (dd/mm/yyyy)", default=REPORT_DATE_START
    )
    data["REPORT_DATE_END"] = typer.prompt(
        "  Fecha fin (dd/mm/yyyy)", default=REPORT_DATE_END
    )
    data["COVER_IMAGE"] = typer.prompt(
        "  Nombre archivo portada (en img/)", default=COVER_IMAGE
    )
    data["LOGO_IMAGE"] = typer.prompt(
        "  Nombre archivo logo (en img/)", default=LOGO_IMAGE
    )

    return data


def update_config(data: dict):
    """Update config.py with new values."""
    content = CONFIG_PATH.read_text(encoding="utf-8")

    for key, value in data.items():
        # Handle multiline PROJECT_DESCRIPTION
        if key == "PROJECT_DESCRIPTION":
            # Find and replace the multi-line assignment
            import re
            pattern = r'PROJECT_DESCRIPTION\s*=\s*\(.*?\)'
            replacement = f'PROJECT_DESCRIPTION = (\n    r"{value}"\n)'
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            # Single-line assignments
            import re
            # Match: KEY = "value" or KEY = r"value"
            pattern = rf'^({key}\s*=\s*r?")[^"]*(")'
            replacement = rf'\g<1>{value}\2'
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    CONFIG_PATH.write_text(content, encoding="utf-8")
    typer.secho("  [OK] config.py actualizado", fg=typer.colors.GREEN)


def run_clean():
    """Run the clean_project script with --confirm."""
    typer.secho("\n  Limpiando proyecto anterior...", fg=typer.colors.BLUE)
    subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "clean_project.py"), "--confirm"],
        cwd=str(PM_ROOT.parent),
    )


def run_create_report():
    """Run create_report.py to generate the template."""
    typer.secho("\n  Generando reporte desde plantilla...", fg=typer.colors.BLUE)
    subprocess.run(
        [
            sys.executable,
            str(SCRIPTS_DIR / "create_report.py"),
            "implementation",
            "--format", "latex",
        ],
        cwd=str(PM_ROOT.parent),
    )


def run_prepare_context(
    start_date: str | None = None,
    end_date: str | None = None,
    diagnostico: str | None = None,
    plan: str | None = None,
):
    """Run prepare_report_context.py to generate AI context."""
    typer.secho("\n  Generando contexto para IA...", fg=typer.colors.BLUE)
    cmd = [sys.executable, str(SCRIPTS_DIR / "prepare_report_context.py")]
    if start_date and end_date:
        cmd.extend(["--start-date", start_date, "--end-date", end_date])
    if diagnostico:
        cmd.extend(["--diagnostico", diagnostico])
    if plan:
        cmd.extend(["--plan", plan])
    subprocess.run(cmd, cwd=str(PM_ROOT.parent))


# =========================================================================
# Main command
# =========================================================================

@app.command()
def start():
    """Interactive project setup and report generation wizard."""
    typer.secho("=" * 60, bold=True)
    typer.secho("  INFORME DE IMPLEMENTACION - SETUP", bold=True)
    typer.secho("=" * 60, bold=True)

    state = detect_project_state()

    if state["has_report"]:
        # ── Existing project ──
        choice = prompt_existing_project(state)

        if choice == "1":
            # Continue with current project
            typer.secho("\n  Continuando con el proyecto actual...\n", bold=True)
            prompt_missing_data(state)

            # Offer to generate context if there are TODOs
            if state["todo_count"] > 0 and not state["has_context"]:
                if typer.confirm("  Generar contexto IA para completar TODOs?", default=True):
                    _prompt_and_generate_context()

            # Offer to compile if tex exists
            if state["has_tex"]:
                if typer.confirm("  Compilar el PDF?", default=False):
                    _compile_report()

        elif choice == "2":
            # Clean and start fresh
            run_clean()
            _new_project_flow()

        else:
            typer.secho("  Saliendo.", fg=typer.colors.BLUE)
            raise typer.Exit(0)
    else:
        # ── No existing project ──
        typer.secho(
            "\n  No se encontro ningun proyecto existente.",
            fg=typer.colors.BLUE,
        )
        _new_project_flow()

    typer.secho("\n" + "=" * 60, bold=True)
    typer.secho("  Proceso completado", fg=typer.colors.GREEN, bold=True)
    typer.secho("=" * 60, bold=True)


def _new_project_flow():
    """Flow for setting up a new project from scratch."""
    typer.secho("\n  Configuracion del nuevo proyecto", bold=True)
    typer.secho("  ─" * 25)

    # Collect config data
    data = prompt_config_data()

    # Confirm
    typer.echo()
    if not typer.confirm("  Guardar estos datos en config.py?", default=True):
        typer.secho("  Cancelado.", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    update_config(data)

    # Generate report from template
    run_create_report()

    # Remind about images
    typer.secho("\n  Recuerda copiar a la carpeta img/:", fg=typer.colors.YELLOW)
    typer.secho(f"    - Portada: {data['COVER_IMAGE']}")
    typer.secho(f"    - Logo: {data['LOGO_IMAGE']}")
    typer.secho("    - Capturas de pantalla de cada modulo")
    typer.echo()

    # Offer context generation
    if typer.confirm("  Generar contexto IA ahora?", default=True):
        _prompt_and_generate_context()


def _prompt_and_generate_context():
    """Ask for optional inputs and generate AI context."""
    typer.echo()
    start_date = typer.prompt(
        "  Fecha inicio Odoo (YYYY-MM-DD, Enter para omitir)", default=""
    )
    end_date = ""
    if start_date:
        end_date = typer.prompt("  Fecha fin Odoo (YYYY-MM-DD)", default="")

    diagnostico = typer.prompt(
        "  Ruta al informe de diagnostico (.txt/.md, Enter para omitir)",
        default="",
    )
    plan = typer.prompt(
        "  Ruta al plan de implementacion (.txt/.md, Enter para omitir)",
        default="",
    )

    run_prepare_context(
        start_date=start_date or None,
        end_date=end_date or None,
        diagnostico=diagnostico or None,
        plan=plan or None,
    )


def _compile_report():
    """Compile the LaTeX report (2 passes)."""
    typer.secho("\n  Compilando PDF (2 pasadas)...", fg=typer.colors.BLUE)
    for i in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "implementation.tex"],
            cwd=str(REPORT_DIR),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and "no output PDF" in result.stdout:
            typer.secho(
                f"  [ERROR] Pasada {i+1} fallo. Revisa implementation.log",
                fg=typer.colors.RED,
            )
            return

    # Check overflows
    log_path = REPORT_DIR / "implementation.log"
    if log_path.exists():
        log_content = log_path.read_text(encoding="utf-8", errors="ignore")
        overflows = log_content.count("Overfull")
        typer.secho(f"  [OK] PDF generado ({overflows} overflows)", fg=typer.colors.GREEN)
    else:
        typer.secho("  [OK] PDF generado", fg=typer.colors.GREEN)


if __name__ == "__main__":
    app()
