#!/usr/bin/env python3
"""Create Kit/BoM for tour packages (requires mrp module installed).

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_kits.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from defaults.categories import CATEGORIES
from agency.defaults.kits import KITS
from defaults.i18n import t, write_translations, search_translatable

app = typer.Typer(help="Create Kit/BoM for tour packages")


@app.command()
def setup():
    """Create Kit products with BoM from defaults configuration."""
    client = OdooClient()
    client.connect()
    changes = 0

    typer.secho("=" * 60, bold=True)
    typer.secho("  KIT / BOM CONFIGURATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # ---------------------------------------------------------------
    # 1. Verify mrp is installed
    # ---------------------------------------------------------------
    typer.secho("\n1. Checking mrp module...", bold=True)
    mrp = client.search_read('ir.module.module',
        domain=[['name', '=', 'mrp']],
        fields=['state'])
    if not mrp or mrp[0]['state'] != 'installed':
        typer.secho("  [FAIL] mrp is not installed. Install it first from Settings > Apps.",
            fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.secho("  [OK] mrp is installed", fg=typer.colors.GREEN)

    for kit_def in KITS:
        kit_name = t(kit_def['name'])

        # ---------------------------------------------------------------
        # 2. Create Kit product
        # ---------------------------------------------------------------
        typer.secho(f"\n2. Kit product: {kit_name}", bold=True)

        existing = search_translatable(client, 'product.template', 'name',
            kit_def['name'], fields=['id', 'name'])

        if existing:
            kit_tmpl_id = existing[0]['id']
            typer.secho(f"  [OK] Already exists (template id={kit_tmpl_id})", fg=typer.colors.GREEN)
        else:
            result = client.execute('product.template', 'create', [{
                'name': kit_name,
                'type': kit_def.get('type', 'consu'),
                'categ_id': CATEGORIES['tours_packages'],
                'sale_ok': kit_def.get('sale_ok', True),
                'purchase_ok': kit_def.get('purchase_ok', False),
                'list_price': kit_def.get('list_price', 0.0),
                'standard_price': kit_def.get('standard_price', 0.0),
            }])
            kit_tmpl_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] template id={kit_tmpl_id}, sale_price=${kit_def.get('list_price', 0)}",
                fg=typer.colors.GREEN)
            changes += 1

        # Write translations for kit product name (customer-facing)
        write_translations(client, 'product.template', kit_tmpl_id, {
            'name': kit_def['name'],
        })
        typer.secho("  [i18n] Translations written", fg=typer.colors.CYAN)

        # Get the product.product variant for this template
        kit_variants = client.search_read('product.product',
            domain=[['product_tmpl_id', '=', kit_tmpl_id]],
            fields=['id'])
        if not kit_variants:
            typer.secho("  [ERROR] Could not find product variant", fg=typer.colors.RED)
            continue
        kit_product_id = kit_variants[0]['id']

        # ---------------------------------------------------------------
        # 3. Resolve component product.product IDs
        # ---------------------------------------------------------------
        typer.secho("\n3. Resolving components...", bold=True)

        components = []
        for spec in kit_def.get('components', []):
            label = spec['label']
            variants = client.search_read('product.product',
                domain=[['name', '=', spec['template_name']]],
                fields=['id', 'name', 'standard_price'],
                limit=1)
            if variants:
                components.append({
                    'product_id': variants[0]['id'],
                    'qty': spec['qty'],
                    'label': label,
                    'name': variants[0]['name'],
                    'cost': variants[0].get('standard_price', 0),
                })
                typer.secho(
                    f"  [OK] {label}: {variants[0]['name']} (id={variants[0]['id']}, cost={variants[0].get('standard_price', 0)})",
                    fg=typer.colors.GREEN)
            else:
                typer.secho(f"  [WARN] {label}: product '{spec['template_name']}' not found",
                    fg=typer.colors.YELLOW)

        # ---------------------------------------------------------------
        # 4. Create BoM (Kit type)
        # ---------------------------------------------------------------
        typer.secho(f"\n4. Bill of Materials (Kit)", bold=True)

        existing_bom = client.search_read('mrp.bom',
            domain=[['product_tmpl_id', '=', kit_tmpl_id]],
            fields=['id', 'type', 'bom_line_ids'])

        if existing_bom:
            bom_id = existing_bom[0]['id']
            typer.secho(
                f"  [OK] BoM already exists (id={bom_id}, type={existing_bom[0].get('type')}, "
                f"lines={len(existing_bom[0].get('bom_line_ids', []))})",
                fg=typer.colors.GREEN)
        else:
            if not components:
                typer.secho("  [ERROR] No components found, cannot create BoM", fg=typer.colors.RED)
                continue

            bom_lines = []
            for i, comp in enumerate(components):
                bom_lines.append((0, 0, {
                    'product_id': comp['product_id'],
                    'product_qty': comp['qty'],
                    'sequence': (i + 1) * 10,
                }))

            result = client.execute('mrp.bom', 'create', [{
                'product_tmpl_id': kit_tmpl_id,
                'type': 'phantom',
                'product_qty': 1.0,
                'bom_line_ids': bom_lines,
            }])
            bom_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] BoM id={bom_id} (type=Kit/phantom, {len(components)} components)",
                fg=typer.colors.GREEN)
            changes += 1

        # ---------------------------------------------------------------
        # 5. Show BoM summary
        # ---------------------------------------------------------------
        typer.secho(f"\n5. BoM Summary", bold=True)

        bom_lines = client.search_read('mrp.bom.line',
            domain=[['bom_id', '=', bom_id]],
            fields=['product_id', 'product_qty', 'sequence'],
            order='sequence')

        total_cost = 0
        for line in bom_lines:
            prod = line.get('product_id', [None, ''])[1] if line.get('product_id') else '-'
            prod_id = line['product_id'][0] if line.get('product_id') else None
            cost = 0
            if prod_id:
                pdata = client.search_read('product.product',
                    domain=[['id', '=', prod_id]],
                    fields=['standard_price'])
                cost = pdata[0].get('standard_price', 0) if pdata else 0
            line_cost = cost * line.get('product_qty', 1)
            total_cost += line_cost
            typer.secho(
                f"  {line.get('product_qty', 1)}x {prod} | unit_cost={cost} | line_cost={line_cost}",
                fg=typer.colors.CYAN)

        kit_price = client.search_read('product.template',
            domain=[['id', '=', kit_tmpl_id]],
            fields=['list_price'])
        sale_price = kit_price[0]['list_price'] if kit_price else 0

        typer.secho(f"\n  Kit cost (from components): ${total_cost:.2f}", fg=typer.colors.CYAN)
        typer.secho(f"  Kit sale price: ${sale_price:.2f}", fg=typer.colors.CYAN)
        if total_cost > 0:
            margin = sale_price - total_cost
            margin_pct = (margin / sale_price * 100) if sale_price > 0 else 0
            typer.secho(f"  Margin: ${margin:.2f} ({margin_pct:.1f}%)", fg=typer.colors.CYAN)
        else:
            typer.secho("  Note: Set component costs (standard_price) to calculate real margins",
                fg=typer.colors.YELLOW)

    typer.secho(f"\nDone. {changes} changes made.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
