#!/usr/bin/env python3
"""Add autoplay to the product image carousel in ecommerce.

Creates a QWeb inherited view that makes the product detail page carousel
auto-cycle through images every N seconds, pausing on hover.

Usage:
    uv run python business_units/hotel-trip-agency/e-commerce/setup_carousel_autoplay.py
    uv run python business_units/hotel-trip-agency/e-commerce/setup_carousel_autoplay.py --target
    uv run python business_units/hotel-trip-agency/e-commerce/setup_carousel_autoplay.py --target --interval 3000
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient

app = typer.Typer(help="Add autoplay to the ecommerce product image carousel")

target_option = typer.Option(False, "--target", help="Run against TARGET_MIGRATION (production) instance")
interval_option = typer.Option(5000, "--interval", help="Milliseconds between slides (default: 5000)")

VIEW_NAME = 'agency_ecommerce.product_carousel_autoplay'


# ── Helpers ───────────────────────────────────────────────────────────────

def _find_parent_view(client, key):
    """Find a QWeb view by its key. Returns (id, name) or (None, None)."""
    result = client.search_read('ir.ui.view',
        domain=[['key', '=', key]],
        fields=['id', 'name'], limit=1)
    if result:
        return result[0]['id'], result[0]['name']
    return None, None


def _find_carousel_parent_key(client):
    """Find the QWeb template that defines the #o-carousel-product element."""
    # Search for id="o-carousel-product" (the element definition),
    # NOT data-bs-target="#o-carousel-product" (just a reference).
    views = client.search_read('ir.ui.view',
        domain=[
            ['arch_db', 'like', 'id="o-carousel-product"'],
            ['inherit_id', '=', False],
            ['type', '=', 'qweb'],
        ],
        fields=['id', 'name', 'key'],
        limit=5)

    if not views:
        return None

    for v in views:
        typer.secho(f"  Found carousel in: {v['key']} — {v['name']} (id={v['id']})", fg=typer.colors.CYAN)

    return views[0]['key']


def _upsert_qweb_view(client, name, arch, parent_key):
    """Create or update a QWeb inherited view. Returns view_id."""
    existing = client.search_read('ir.ui.view',
        domain=[['name', '=', name]],
        fields=['id', 'key'])

    if existing:
        view_id = existing[0]['id']
        vals = {'arch': arch}
        if existing[0].get('key') != name:
            vals['key'] = name
        client.execute('ir.ui.view', 'write', [view_id], vals,
                        context={'lang': 'en_US'})
        typer.secho(f"  [UPDATED] {name} (id={view_id})", fg=typer.colors.GREEN)
        return view_id

    parent_id, parent_name = _find_parent_view(client, parent_key)
    if not parent_id:
        typer.secho(f"  [ERROR] Parent view '{parent_key}' not found!", fg=typer.colors.RED)
        return None

    typer.secho(f"  Parent: {parent_name} (id={parent_id})", fg=typer.colors.CYAN)
    result = client.execute('ir.ui.view', 'create', [{
        'name': name,
        'key': name,
        'inherit_id': parent_id,
        'type': 'qweb',
        'arch': arch,
        'priority': 99,
    }], context={'lang': 'en_US'})
    view_id = result[0] if isinstance(result, list) else result
    typer.secho(f"  [CREATED] {name} (id={view_id})", fg=typer.colors.GREEN)
    return view_id


def _build_arch(interval_ms):
    """Build the QWeb arch XML with the given interval."""
    return f'''<data>
    <!-- Auto-cycle product images carousel -->
    <xpath expr="//div[@id='o-carousel-product']" position="attributes">
        <attribute name="data-bs-ride">carousel</attribute>
        <attribute name="data-bs-interval">{interval_ms}</attribute>
        <attribute name="data-bs-wrap">true</attribute>
        <attribute name="data-bs-pause">hover</attribute>
    </xpath>
</data>'''


# ── Main ──────────────────────────────────────────────────────────────────

@app.command()
def setup(
    target: bool = target_option,
    interval: int = interval_option,
):
    """Add autoplay to the product image carousel."""
    if target:
        from odoo_cli.target import get_target_client
        client = get_target_client()
        if not client:
            typer.secho("[ERROR] TARGET_MIGRATION_* variables not configured", fg=typer.colors.RED)
            raise typer.Exit(1)
        client.connect()
        typer.secho(f"Connected to TARGET (production) as uid={client.uid}",
                    fg=typer.colors.YELLOW, bold=True)
    else:
        client = OdooClient()
        client.connect()

    typer.secho("=" * 60, bold=True)
    typer.secho("  PRODUCT CAROUSEL AUTOPLAY", bold=True)
    typer.secho("=" * 60, bold=True)

    # 1. Find the parent template that contains #o-carousel-product
    typer.secho("\nSearching for carousel parent template...", bold=True)
    parent_key = _find_carousel_parent_key(client)
    if not parent_key:
        typer.secho("[ERROR] Could not find a QWeb view containing 'o-carousel-product'",
                    fg=typer.colors.RED)
        raise typer.Exit(1)

    # 2. Create/update the inherited view
    typer.secho(f"\nCreating autoplay view (interval={interval}ms, pause on hover)...", bold=True)
    arch = _build_arch(interval)
    view_id = _upsert_qweb_view(client, VIEW_NAME, arch, parent_key)

    if view_id:
        typer.secho(f"\nDone! Product carousel will auto-slide every {interval / 1000:.0f}s.",
                    fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("\nFailed to create the view.", fg=typer.colors.RED)
        raise typer.Exit(1)


if __name__ == '__main__':
    app()
