#!/usr/bin/env python3
"""Create default restaurant products and assign POS categories.

Usage:
    uv run python business_units/hotel-trip-agency/restaurant/setup_products.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from defaults.categories import CATEGORIES
from defaults.i18n import t, write_translations, search_translatable
from restaurant.defaults.products import PRODUCTS

app = typer.Typer(help="Create default restaurant products")


@app.command()
def setup():
    """Create default products and assign POS categories."""
    client = OdooClient()
    client.connect()
    changes = 0

    typer.secho("=" * 60, bold=True)
    typer.secho("  RESTAURANT PRODUCTS CONFIGURATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # ---------------------------------------------------------------
    # 1. Show POS categories
    # ---------------------------------------------------------------
    typer.secho("\n1. POS categories...", bold=True)

    pos_categs = client.search_read('pos.category', domain=[],
        fields=['id', 'name'])
    for c in pos_categs:
        typer.secho(f"  {c['name']}: id={c['id']}", fg=typer.colors.CYAN)

    # ---------------------------------------------------------------
    # 2. Create/verify default products
    # ---------------------------------------------------------------
    typer.secho("\n2. Default products", bold=True)

    for prod_def in PRODUCTS:
        prod_name = t(prod_def['name'])

        existing = search_translatable(client, 'product.template', 'name',
            prod_def['name'], fields=['id', 'name', 'available_in_pos', 'pos_categ_ids'])

        if existing:
            tmpl_id = existing[0]['id']
            typer.secho(f"  [OK] {prod_name} (id={tmpl_id})", fg=typer.colors.GREEN)

            # Ensure available_in_pos and pos_categ_ids are set
            updates = {}
            if not existing[0].get('available_in_pos'):
                updates['available_in_pos'] = True
            pos_categ_name = prod_def.get('pos_categ')
            if pos_categ_name:
                found = client.search_read('pos.category',
                    domain=[['name', '=', pos_categ_name]], fields=['id'], limit=1)
                if found:
                    current_categs = existing[0].get('pos_categ_ids', [])
                    if found[0]['id'] not in current_categs:
                        updates['pos_categ_ids'] = [(4, found[0]['id'])]
            if updates:
                client.execute('product.template', 'write', [tmpl_id], updates)
                typer.secho(f"    [UPDATED] {list(updates.keys())}", fg=typer.colors.GREEN)
                changes += 1
        else:
            data = {
                'name': prod_name,
                'type': prod_def['type'],
                'list_price': prod_def['list_price'],
                'sale_ok': prod_def.get('sale_ok', True),
                'available_in_pos': prod_def.get('available_in_pos', True),
                'categ_id': CATEGORIES['restaurant'],
            }
            pos_categ_name = prod_def.get('pos_categ')
            if pos_categ_name:
                found = client.search_read('pos.category',
                    domain=[['name', '=', pos_categ_name]], fields=['id'], limit=1)
                if found:
                    data['pos_categ_ids'] = [(4, found[0]['id'])]

            result = client.execute('product.template', 'create', [data])
            tmpl_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] {prod_name} (id={tmpl_id}, price={prod_def['list_price']})",
                fg=typer.colors.GREEN)
            changes += 1

        # Write i18n translations (customer-facing via self-ordering)
        write_translations(client, 'product.template', tmpl_id, {
            'name': prod_def['name'],
        })
        typer.secho(f"    [i18n] Translations written", fg=typer.colors.CYAN)

    # ---------------------------------------------------------------
    # 3. List all POS products
    # ---------------------------------------------------------------
    typer.secho("\n3. All products available in POS", bold=True)

    pos_products = client.search_read('product.template',
        domain=[['available_in_pos', '=', True]],
        fields=['name', 'list_price', 'type', 'pos_categ_ids', 'categ_id'],
        order='name')

    for p in pos_products:
        categ = p.get('categ_id', [None, '-'])[1] if p.get('categ_id') else '-'
        pos_cats = p.get('pos_categ_ids', [])
        pos_cat_names = []
        if pos_cats:
            cats = client.search_read('pos.category',
                domain=[['id', 'in', pos_cats]],
                fields=['name'])
            pos_cat_names = [c['name'] for c in cats]
        pos_cat_str = ', '.join(pos_cat_names) if pos_cat_names else '(none)'
        typer.secho(
            f"  {p['name']} | S/{p['list_price']:.2f} | {p['type']} | "
            f"categ={categ} | pos_categ={pos_cat_str}",
            fg=typer.colors.CYAN)

    typer.secho(f"\nDone. {changes} changes made.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
