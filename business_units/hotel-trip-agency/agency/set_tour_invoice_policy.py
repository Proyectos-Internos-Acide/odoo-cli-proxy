#!/usr/bin/env python3
"""Configure tour products to project-only tracking.

Sets all tour products (category "Tours y Paquetes turísticos") to:
- service_tracking = 'project_only'  → creates project on SO confirm, NO tasks

Usage:
    uv run python business_units/hotel-trip-agency/agency/set_tour_invoice_policy.py
    uv run python business_units/hotel-trip-agency/agency/set_tour_invoice_policy.py --target prod
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import typer
from odoo_cli import OdooClient

app = typer.Typer(help="Set tour products to project-only tracking")

TOUR_CATEGORY_ID = 8  # "Tours y Paquetes turísticos"


def get_client(target: str) -> OdooClient:
    if target == "prod":
        url = os.getenv("TARGET_MIGRATION_URL")
        db = os.getenv("TARGET_MIGRATION_DB")
        user = os.getenv("TARGET_MIGRATION_USERNAME")
        pwd = os.getenv("TARGET_MIGRATION_PASSWORD")
        if not all([url, db, user, pwd]):
            typer.echo("Missing TARGET_MIGRATION_* env vars")
            raise typer.Exit(1)
        return OdooClient(url=url, db=db, username=user, password=pwd)
    return OdooClient()


@app.command()
def setup(
    target: str = typer.Option("test", help="Target: 'test' or 'prod'"),
    dry_run: bool = typer.Option(False, help="Only show what would change"),
):
    """Set all tour products to project_only tracking (no tasks)."""
    typer.echo(f"\nConfigurando productos de tour ({target})\n")

    client = get_client(target)
    client.connect()

    tours = client.search_read(
        'product.template',
        [['categ_id', '=', TOUR_CATEGORY_ID]],
        fields=['id', 'name', 'service_tracking'],
    )

    typer.echo(f"  Productos de tour encontrados: {len(tours)}\n")

    needs_update = []
    for t in tours:
        if t['service_tracking'] != 'project_only':
            needs_update.append(t['id'])
            typer.echo(f"  {'[DRY]' if dry_run else '  →  '} {t['name']}: {t['service_tracking']} → project_only")

    already_ok = len(tours) - len(needs_update)
    if already_ok:
        typer.echo(f"\n  ✓ {already_ok} productos ya están en project_only")

    if not needs_update:
        typer.echo("  ✓ Nada que cambiar")
        return

    if dry_run:
        typer.echo(f"\n  {len(needs_update)} productos por actualizar (dry run)")
        return

    client.execute('product.template', 'write', needs_update, {
        'service_tracking': 'project_only',
    })

    typer.echo(f"\n  ✓ {len(needs_update)} productos actualizados a project_only")


if __name__ == "__main__":
    app()
