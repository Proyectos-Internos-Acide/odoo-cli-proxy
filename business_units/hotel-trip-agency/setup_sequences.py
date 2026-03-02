#!/usr/bin/env python3
"""
Configure sale order and purchase order sequences with date-based prefixes.

Format:
  - Sales:     AYF-VT-{YYYY}-{MM}-0001  (resets monthly)
  - Purchases: AYF-COMP-{YYYY}-{MM}-0001 (resets monthly)

Usage:
    python setup_sequences.py              # Show current + configure
    python setup_sequences.py --dry-run    # Preview only, no changes
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import typer
from odoo_cli import OdooClient
from odoo_cli.target import get_target_client

app = typer.Typer(help="Configure sale/purchase order sequences")

# ── Sequence definitions ───────────────────────────────────────
SEQUENCES = [
    {
        'code': 'sale.order',
        'label': 'Ventas (Sale Order)',
        'prefix': 'AYF-VT-%(year)s-%(month)s-',
    },
    {
        'code': 'purchase.order',
        'label': 'Compras (Purchase Order)',
        'prefix': 'AYF-COMP-%(year)s-%(month)s-',
    },
]

PADDING = 4  # 0001, 0002, ...


def configure_sequences(client: OdooClient, instance_name: str, dry_run: bool):
    """Configure sequences on a given Odoo instance."""
    typer.secho(f"\n{'=' * 60}", bold=True)
    typer.secho(f"  CONFIGURACIÓN DE SECUENCIAS — {instance_name}", bold=True)
    typer.secho(f"  {client.url}", dim=True)
    typer.secho(f"{'=' * 60}", bold=True)

    for seq_def in SEQUENCES:
        typer.secho(f"\n{'─' * 60}", dim=True)
        typer.secho(f"  {seq_def['label']}  (code={seq_def['code']})", bold=True)

        records = client.search_read(
            'ir.sequence',
            domain=[['code', '=', seq_def['code']]],
            fields=[
                'id', 'name', 'prefix', 'suffix', 'padding',
                'number_next_actual', 'use_date_range',
            ],
        )

        if not records:
            typer.secho(f"  [WARN] No sequence found for code '{seq_def['code']}'",
                        fg=typer.colors.YELLOW)
            continue

        rec = records[0]
        typer.secho(f"  Actual: prefix={rec.get('prefix')!r}  "
                    f"padding={rec.get('padding')}  "
                    f"use_date_range={rec.get('use_date_range')}  "
                    f"next={rec.get('number_next_actual')}")

        new_prefix = seq_def['prefix']
        typer.secho(f"  Nuevo:  prefix={new_prefix!r}  "
                    f"padding={PADDING}  "
                    f"use_date_range=True",
                    fg=typer.colors.CYAN)

        if dry_run:
            typer.secho("  [DRY RUN] No se aplican cambios", fg=typer.colors.YELLOW)
            continue

        try:
            client.execute('ir.sequence', 'write', [rec['id']], {
                'prefix': new_prefix,
                'suffix': '',
                'padding': PADDING,
                'use_date_range': True,
            })
            typer.secho(f"  [OK] Secuencia actualizada (id={rec['id']})",
                        fg=typer.colors.GREEN)
        except Exception as e:
            typer.secho(f"  [ERROR] {str(e)[:120]}", fg=typer.colors.RED)


@app.command()
def setup(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview only"),
    production: bool = typer.Option(False, "--production", help="Also apply to production"),
):
    """Configure sale and purchase order sequences."""
    # ── Test instance ──────────────────────────────────────────
    client = OdooClient()
    client.connect()

    configure_sequences(client, "PRUEBAS", dry_run)

    # ── Production instance ────────────────────────────────────
    if production:
        prod_client = get_target_client()
        if prod_client is None:
            typer.secho("\n  [ERROR] TARGET_MIGRATION_* env vars not configured",
                        fg=typer.colors.RED)
            raise typer.Exit(1)
        prod_client.connect()
        configure_sequences(prod_client, "PRODUCCIÓN", dry_run)

    # ── Summary ────────────────────────────────────────────────
    typer.secho(f"\n{'=' * 60}", bold=True)
    if dry_run:
        typer.secho("  DRY RUN completado. Usa sin --dry-run para aplicar.", bold=True)
    else:
        typer.secho("  Secuencias configuradas.", bold=True)
        typer.secho("  Ejemplo próxima venta:  AYF-VT-2026-03-0001", fg=typer.colors.GREEN)
        typer.secho("  Ejemplo próxima compra: AYF-COMP-2026-03-0001", fg=typer.colors.GREEN)
        typer.secho("\n  NOTA: El contador se reiniciará automáticamente cada mes.",
                    fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
