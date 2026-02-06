#!/usr/bin/env python3
"""Configure product attributes and create missing products for travel agency.

Usage:
    uv run python business_units/hotel-trip-agency/setup_products.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(__file__))

import typer
from odoo_cli import OdooClient
from defaults.categories import CATEGORIES
from hotel.defaults.attributes import (
    HOTEL_ATTR_IDS, HOTEL_ATTR_MODE, TOUR_ATTR_IDS,
)
from agency.defaults.products import TRANSPORT_PRODUCT

app = typer.Typer(help="Configure products and attributes for travel agency")


@app.command()
def setup():
    """Fix hotel attributes to no_variant and create missing products."""
    client = OdooClient()
    client.connect()
    changes = 0

    typer.secho("=" * 60, bold=True)
    typer.secho("  PRODUCTS & ATTRIBUTES CONFIGURATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # ---------------------------------------------------------------
    # 1. Fix hotel attributes: create_variant → no_variant
    # ---------------------------------------------------------------
    typer.secho(f"\n1. Hotel attributes → {HOTEL_ATTR_MODE}", bold=True)

    attrs = client.search_read('product.attribute',
        domain=[['id', 'in', HOTEL_ATTR_IDS]],
        fields=['name', 'create_variant'])

    to_fix = [a for a in attrs if a['create_variant'] != HOTEL_ATTR_MODE]
    if to_fix:
        for a in to_fix:
            try:
                client.execute('product.attribute', 'write', [a['id']],
                    {'create_variant': HOTEL_ATTR_MODE})
                typer.secho(f"  [FIXED] {a['name']}: {a['create_variant']} -> {HOTEL_ATTR_MODE}",
                    fg=typer.colors.GREEN)
                changes += 1
            except Exception as e:
                msg = str(e)
                if 'No puede cambiar' in msg or 'Cannot change' in msg:
                    typer.secho(f"  [SKIP] {a['name']}: already used on products with variants",
                        fg=typer.colors.YELLOW)
                else:
                    typer.secho(f"  [ERROR] {a['name']}: {msg[:80]}", fg=typer.colors.RED)
    else:
        typer.secho(f"  [OK] All hotel attributes already set to {HOTEL_ATTR_MODE}",
            fg=typer.colors.GREEN)

    # Show tour attributes (kept as always)
    typer.secho("\n  Tour attributes (kept as create_variant=always):", fg=typer.colors.CYAN)
    tour_attrs = client.search_read('product.attribute',
        domain=[['id', 'in', TOUR_ATTR_IDS]],
        fields=['name', 'create_variant'])
    for a in tour_attrs:
        typer.secho(f"    {a['name']}: {a['create_variant']}", fg=typer.colors.CYAN)

    # ---------------------------------------------------------------
    # 2. Create transport purchase product
    # ---------------------------------------------------------------
    prod_name = TRANSPORT_PRODUCT['name']
    typer.secho(f"\n2. Product: {prod_name}", bold=True)

    existing = client.search_read('product.template',
        domain=[['name', '=', prod_name]],
        fields=['id', 'name'])

    if existing:
        prod_tmpl_id = existing[0]['id']
        typer.secho(f"  [OK] Already exists (id={prod_tmpl_id})", fg=typer.colors.GREEN)
    else:
        prod_data = {
            'name': prod_name,
            'type': TRANSPORT_PRODUCT['type'],
            'purchase_ok': TRANSPORT_PRODUCT['purchase_ok'],
            'sale_ok': TRANSPORT_PRODUCT['sale_ok'],
            'list_price': TRANSPORT_PRODUCT['list_price'],
            'standard_price': TRANSPORT_PRODUCT['standard_price'],
            'categ_id': CATEGORIES['services'],
        }
        result = client.execute('product.template', 'create', [prod_data])
        prod_tmpl_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] id={prod_tmpl_id}", fg=typer.colors.GREEN)
        changes += 1

    # ---------------------------------------------------------------
    # 3. Verify tour products have correct service_tracking
    # ---------------------------------------------------------------
    typer.secho("\n3. Tour products: service_tracking check", bold=True)

    tour_products = client.search_read('product.template',
        domain=[['categ_id', '=', CATEGORIES['tours_packages']]],
        fields=['name', 'type', 'service_tracking', 'invoice_policy'])

    for p in tour_products:
        tracking = p.get('service_tracking', 'no')
        invoice = p.get('invoice_policy', '-')
        ok = tracking in ('task_in_project', 'project_only')
        status = 'OK' if ok else 'CHECK'
        color = typer.colors.GREEN if ok else typer.colors.YELLOW
        typer.secho(f"  [{status}] {p['name']}: tracking={tracking}, invoice={invoice}", fg=color)

    # ---------------------------------------------------------------
    # 4. Verify all hotel rooms are service + rental
    # ---------------------------------------------------------------
    typer.secho("\n4. Hotel rooms: type check", bold=True)

    rooms = client.search_read('product.template',
        domain=[['categ_id', '=', CATEGORIES['hotel_rooms']]],
        fields=['name', 'type', 'website_published', 'list_price'])

    for r in rooms:
        ok = r.get('type') == 'service'
        status = 'OK' if ok else 'CHECK'
        color = typer.colors.GREEN if ok else typer.colors.YELLOW
        pub = 'PUB' if r.get('website_published') else 'UNPUB'
        typer.secho(f"  [{status}] {r['name']}: type={r['type']}, price={r['list_price']}, {pub}", fg=color)

    typer.secho(f"\nDone. {changes} changes made.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
