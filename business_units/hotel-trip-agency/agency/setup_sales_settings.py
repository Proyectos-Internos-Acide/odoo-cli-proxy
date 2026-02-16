#!/usr/bin/env python3
"""Configure sales settings: margins, quotation templates, optional products.

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_sales_settings.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from defaults.modules import REQUIRED_MODULES

app = typer.Typer(help="Configure sales settings for travel agency")


@app.command()
def setup():
    """Activate margins, quotation templates, and verify sales settings."""
    client = OdooClient()
    uid = client.connect()
    changes = 0

    typer.secho("=" * 60, bold=True)
    typer.secho("  SALES SETTINGS CONFIGURATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # 1. Verify sale_margin module is installed
    typer.secho("\n1. Checking sale_margin module...", bold=True)
    margin_mod = client.search_read('ir.module.module',
        domain=[['name', '=', 'sale_margin']],
        fields=['state'])
    if margin_mod and margin_mod[0]['state'] == 'installed':
        typer.secho("  [OK] sale_margin is installed", fg=typer.colors.GREEN)
    else:
        typer.secho("  [WARN] sale_margin is NOT installed", fg=typer.colors.YELLOW)

    # 2. Check/Enable quotation templates
    typer.secho("\n2. Checking quotation templates...", bold=True)
    try:
        params = client.search_read('ir.config_parameter',
            domain=[['key', '=', 'sale.use_quotation_template']],
            fields=['value'])
        if params and params[0].get('value') == 'True':
            typer.secho("  [OK] Quotation templates already enabled", fg=typer.colors.GREEN)
        else:
            typer.secho("  Enabling quotation templates...", fg=typer.colors.YELLOW)
            if params:
                client.execute('ir.config_parameter', 'write',
                    [params[0]['id']], {'value': 'True'})
            else:
                client.execute('ir.config_parameter', 'create',
                    [{'key': 'sale.use_quotation_template', 'value': 'True'}])
            typer.secho("  [OK] Quotation templates enabled", fg=typer.colors.GREEN)
            changes += 1
    except Exception as e:
        typer.secho(f"  [INFO] Could not set via ir.config_parameter: {e}", fg=typer.colors.YELLOW)
        typer.secho("  Manual: Go to Settings > Sales > Quotations & Orders > enable 'Quotation Templates'", fg=typer.colors.CYAN)

    # 3. Check existing quotation templates
    typer.secho("\n3. Existing quotation templates...", bold=True)
    templates = client.search_read('sale.order.template',
        domain=[], fields=['name', 'number_of_days', 'sale_order_template_line_ids'])
    if templates:
        for t in templates:
            lines = len(t.get('sale_order_template_line_ids', []))
            typer.secho(f"  [{t['id']}] {t['name']} | validity={t.get('number_of_days')} days | {lines} lines",
                fg=typer.colors.GREEN)
    else:
        typer.secho("  (none) - You should create at least one template", fg=typer.colors.YELLOW)

    # 4. Check mrp module
    typer.secho("\n4. Checking Manufacturing (mrp) module...", bold=True)
    mrp_mod = client.search_read('ir.module.module',
        domain=[['name', '=', 'mrp']],
        fields=['state'])
    if mrp_mod and mrp_mod[0]['state'] == 'installed':
        typer.secho("  [OK] mrp is installed (Kit/BoM available)", fg=typer.colors.GREEN)
    else:
        typer.secho("  [PENDING] mrp is NOT installed", fg=typer.colors.YELLOW)
        typer.secho("  Action: Go to Settings > Apps > search 'Manufacturing' > Install", fg=typer.colors.CYAN)

    # 5. Verify key modules
    typer.secho("\n5. Module checklist...", bold=True)
    modules = client.search_read('ir.module.module',
        domain=[['name', 'in', list(REQUIRED_MODULES.keys())]],
        fields=['name', 'state'])
    mod_states = {m['name']: m['state'] for m in modules}
    for name, desc in REQUIRED_MODULES.items():
        state = mod_states.get(name, 'not found')
        ok = state == 'installed'
        color = typer.colors.GREEN if ok else typer.colors.RED
        status = 'OK' if ok else state.upper()
        typer.secho(f"  [{status}] {name} ({desc})", fg=color)

    typer.secho(f"\nDone. {changes} settings changed.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
