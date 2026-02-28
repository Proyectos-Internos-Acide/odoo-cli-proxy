#!/usr/bin/env python3
"""Setup language-based pricelist switching for ecommerce.

Configures:
- PEN pricelist (id=1): selectable, assigned to LATAM country group
- USD pricelist (id=2): selectable, global conversion rule
- Country groups: LATAM → PEN, International → USD (GeoIP fallback)
- QWeb view: JavaScript auto-switch language ↔ pricelist

When visiting in English → USD prices; in Spanish → PEN prices.
Products with manual USD prices in the pricelist override the automatic conversion.

Usage:
    uv run python business_units/hotel-trip-agency/e-commerce/pricelist/setup_pricelist_currency.py
    uv run python business_units/hotel-trip-agency/e-commerce/pricelist/setup_pricelist_currency.py --target prod
    uv run python business_units/hotel-trip-agency/e-commerce/pricelist/setup_pricelist_currency.py --target both
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import typer
from odoo_cli import OdooClient
from agency.defaults.views import ECOM_PRICELIST_LANG_SWITCH_ARCH

app = typer.Typer(help="Setup language-based pricelist switching (EN→USD, ES→PEN)")

# LATAM country codes for the PEN pricelist country group
LATAM_COUNTRY_CODES = [
    'PE', 'CO', 'EC', 'BO', 'CL', 'AR', 'BR', 'MX', 'VE', 'PY',
    'UY', 'CR', 'PA', 'GT', 'HN', 'SV', 'NI', 'CU', 'DO', 'PR',
]


# ── Helpers ───────────────────────────────────────────────────────────────

def _find_parent_view(client, key):
    """Find a QWeb view by its key. Returns (id, name) or (None, None)."""
    result = client.search_read('ir.ui.view',
        domain=[['key', '=', key]],
        fields=['id', 'name'], limit=1)
    if result:
        return result[0]['id'], result[0]['name']
    return None, None


def _upsert_qweb_view(client, name, arch_en, parent_key):
    """Create or update a QWeb inherited view. Returns view_id."""
    existing = client.search_read('ir.ui.view',
        domain=[['name', '=', name]],
        fields=['id', 'key'])
    if existing:
        view_id = existing[0]['id']
        vals = {'arch': arch_en}
        if existing[0].get('key') != name:
            vals['key'] = name
        client.execute('ir.ui.view', 'write', [view_id], vals,
                        context={'lang': 'en_US'})
        typer.secho(f"  [UPDATED] {name} (id={view_id})", fg=typer.colors.GREEN)
    else:
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
            'arch': arch_en,
            'priority': 99,
        }], context={'lang': 'en_US'})
        view_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] {name} (id={view_id})", fg=typer.colors.GREEN)

    return view_id


def _find_or_create_country_group(client, name, country_codes):
    """Find or create a res.country.group with the given countries. Returns id."""
    existing = client.search_read('res.country.group',
        domain=[['name', '=', name]],
        fields=['id'], limit=1)
    if existing:
        group_id = existing[0]['id']
        # Update country list
        country_ids = client.execute('res.country', 'search',
            [['code', 'in', country_codes]])
        if country_ids:
            client.execute('res.country.group', 'write', [group_id],
                {'country_ids': [(6, 0, country_ids)]})
        typer.secho(f"  [UPDATED] Country group '{name}' (id={group_id}, {len(country_ids)} countries)",
                    fg=typer.colors.GREEN)
        return group_id

    country_ids = client.execute('res.country', 'search',
        [['code', 'in', country_codes]])
    result = client.execute('res.country.group', 'create', [{
        'name': name,
        'country_ids': [(6, 0, country_ids)],
    }])
    group_id = result[0] if isinstance(result, list) else result
    typer.secho(f"  [CREATED] Country group '{name}' (id={group_id}, {len(country_ids)} countries)",
                fg=typer.colors.GREEN)
    return group_id


# ── Multi-instance support ────────────────────────────────────────────────

def _get_clients(target):
    """Return list of (label, client) tuples based on target."""
    clients = []
    if target in ('test', 'both'):
        clients.append(('TEST', OdooClient()))
    if target in ('prod', 'both'):
        from dotenv import load_dotenv
        load_dotenv()
        prod_url = os.environ.get('TARGET_MIGRATION_URL')
        prod_db = os.environ.get('TARGET_MIGRATION_DB')
        prod_user = os.environ.get('TARGET_MIGRATION_USERNAME')
        prod_pass = os.environ.get('TARGET_MIGRATION_PASSWORD')
        if not all([prod_url, prod_db, prod_user, prod_pass]):
            typer.secho("  [ERROR] Production credentials not found in .env", fg=typer.colors.RED)
            raise typer.Exit(1)
        clients.append(('PROD', OdooClient(url=prod_url, db=prod_db,
                                            username=prod_user, password=prod_pass)))
    return clients


# ── Main setup ────────────────────────────────────────────────────────────

@app.command()
def setup(target: str = typer.Option("test", help="Target instance: test, prod, or both")):
    """Configure language-based pricelist switching (EN→USD, ES→PEN)."""
    if target not in ('test', 'prod', 'both'):
        typer.secho(f"Invalid target: {target}. Use test, prod, or both.", fg=typer.colors.RED)
        raise typer.Exit(1)

    clients = _get_clients(target)

    for label, client in clients:
        client.connect()
        typer.secho(f"\n{'=' * 70}", bold=True)
        typer.secho(f"  PRICELIST CURRENCY SETUP — {label} ({client.db})", bold=True)
        typer.secho(f"{'=' * 70}", bold=True)
        _run_setup(client, label)

    typer.secho(f"\n{'=' * 70}", bold=True)
    typer.secho("  ALL INSTANCES COMPLETE", fg=typer.colors.BLUE, bold=True)
    typer.secho(f"{'=' * 70}", bold=True)


def _run_setup(client, label):
    """Run all setup steps on a single client instance."""

    # ── 1. Find currencies ────────────────────────────────────────────
    typer.secho("\n1. Find currencies (PEN, USD)", bold=True)

    pen_currencies = client.search_read('res.currency',
        domain=[['name', '=', 'PEN']],
        fields=['id', 'name', 'active'])
    usd_currencies = client.search_read('res.currency',
        domain=[['name', '=', 'USD']],
        fields=['id', 'name', 'active'])

    if not pen_currencies:
        typer.secho("  [ERROR] PEN currency not found!", fg=typer.colors.RED)
        return
    if not usd_currencies:
        typer.secho("  [ERROR] USD currency not found!", fg=typer.colors.RED)
        return

    pen_currency_id = pen_currencies[0]['id']
    usd_currency_id = usd_currencies[0]['id']
    typer.secho(f"  [OK] PEN (id={pen_currency_id}), USD (id={usd_currency_id})", fg=typer.colors.GREEN)

    # Ensure USD is active
    if not usd_currencies[0].get('active'):
        client.execute('res.currency', 'write', [usd_currency_id], {'active': True})
        typer.secho("  [OK] USD currency activated", fg=typer.colors.GREEN)

    # ── 2. Find/configure pricelists ──────────────────────────────────
    typer.secho("\n2. Configure pricelists (PEN + USD)", bold=True)

    # Find PEN pricelist (company default, usually id=1)
    pen_pls = client.search_read('product.pricelist',
        domain=[['currency_id', '=', pen_currency_id]],
        fields=['id', 'name', 'selectable'],
        limit=1)
    if not pen_pls:
        typer.secho("  [ERROR] No PEN pricelist found!", fg=typer.colors.RED)
        return

    pen_pl_id = pen_pls[0]['id']
    typer.secho(f"  [OK] PEN pricelist: {pen_pls[0]['name']} (id={pen_pl_id})", fg=typer.colors.GREEN)

    # Ensure selectable
    if not pen_pls[0].get('selectable'):
        client.execute('product.pricelist', 'write', [pen_pl_id], {'selectable': True})
        typer.secho(f"  [OK] PEN pricelist set selectable=True", fg=typer.colors.GREEN)

    # Find or create USD pricelist
    usd_pls = client.search_read('product.pricelist',
        domain=[['currency_id', '=', usd_currency_id]],
        fields=['id', 'name', 'selectable'],
        limit=1)

    if usd_pls:
        usd_pl_id = usd_pls[0]['id']
        typer.secho(f"  [OK] USD pricelist: {usd_pls[0]['name']} (id={usd_pl_id})", fg=typer.colors.GREEN)
        if not usd_pls[0].get('selectable'):
            client.execute('product.pricelist', 'write', [usd_pl_id], {'selectable': True})
            typer.secho(f"  [OK] USD pricelist set selectable=True", fg=typer.colors.GREEN)
    else:
        result = client.execute('product.pricelist', 'create', [{
            'name': 'USD',
            'currency_id': usd_currency_id,
            'selectable': True,
        }])
        usd_pl_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] USD pricelist (id={usd_pl_id})", fg=typer.colors.GREEN)

    # ── 3. Global conversion rule on USD pricelist ────────────────────
    typer.secho("\n3. Global conversion rule on USD pricelist", bold=True)

    # Check if a global formula rule already exists
    existing_items = client.search_read('product.pricelist.item',
        domain=[
            ['pricelist_id', '=', usd_pl_id],
            ['applied_on', '=', '3_global'],
            ['compute_price', '=', 'formula'],
            ['base', '=', 'list_price'],
        ],
        fields=['id'])

    if existing_items:
        item_id = existing_items[0]['id']
        client.execute('product.pricelist.item', 'write', [item_id], {
            'price_discount': 0,
            'price_surcharge': 0,
        })
        typer.secho(f"  [UPDATED] Global conversion rule (id={item_id})", fg=typer.colors.GREEN)
    else:
        result = client.execute('product.pricelist.item', 'create', [{
            'pricelist_id': usd_pl_id,
            'applied_on': '3_global',
            'compute_price': 'formula',
            'base': 'list_price',
            'price_discount': 0,
            'price_surcharge': 0,
        }])
        item_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] Global conversion rule (id={item_id})", fg=typer.colors.GREEN)

    typer.secho("  Conversion uses res.currency.rate (automatic PEN→USD)", fg=typer.colors.CYAN)

    # Clean up any default fixed-price $0 rules (Odoo creates these automatically)
    bad_items = client.search_read('product.pricelist.item',
        domain=[
            ['pricelist_id', '=', usd_pl_id],
            ['compute_price', '=', 'fixed'],
            ['fixed_price', '=', 0.0],
            ['applied_on', '=', '3_global'],
        ],
        fields=['id'])
    for bad in bad_items:
        client.execute('product.pricelist.item', 'unlink', [bad['id']])
        typer.secho(f"  [DELETED] Default fixed-price $0 rule (id={bad['id']})", fg=typer.colors.YELLOW)

    # ── 4. Country groups for GeoIP pricelist resolution ──────────────
    # CRITICAL: Odoo's _get_pl_partner_order first checks GeoIP country groups.
    # If ANY pricelist matches via country group, the fallback (all website pricelists)
    # is SKIPPED. So BOTH pricelists MUST have country groups, otherwise the one
    # without groups will never be "available" for GeoIP visitors.
    typer.secho("\n4. Country groups (GeoIP pricelist resolution)", bold=True)

    latam_group_id = _find_or_create_country_group(client, 'LATAM', LATAM_COUNTRY_CODES)

    # International group: ALL countries → USD pricelist is available everywhere
    all_countries = client.search_read('res.country',
        domain=[['id', '>', 0]], fields=['id'], limit=500)
    all_codes = [c['id'] for c in all_countries]
    # We pass IDs directly instead of codes for the "International" group
    existing_intl = client.search_read('res.country.group',
        domain=[['name', '=', 'International']],
        fields=['id'], limit=1)
    if existing_intl:
        intl_group_id = existing_intl[0]['id']
        client.execute('res.country.group', 'write', [intl_group_id],
            {'country_ids': [(6, 0, all_codes)]})
        typer.secho(f"  [UPDATED] International group (id={intl_group_id}, {len(all_codes)} countries)",
                    fg=typer.colors.GREEN)
    else:
        result = client.execute('res.country.group', 'create', [{
            'name': 'International',
            'country_ids': [(6, 0, all_codes)],
        }])
        intl_group_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] International group (id={intl_group_id}, {len(all_codes)} countries)",
                    fg=typer.colors.GREEN)

    # Assign country groups to pricelists
    client.execute('product.pricelist', 'write', [pen_pl_id],
        {'country_group_ids': [(6, 0, [latam_group_id])]})
    typer.secho(f"  [OK] PEN pricelist → LATAM country group", fg=typer.colors.GREEN)

    client.execute('product.pricelist', 'write', [usd_pl_id],
        {'country_group_ids': [(6, 0, [intl_group_id])]})
    typer.secho(f"  [OK] USD pricelist → International country group (all countries)", fg=typer.colors.GREEN)

    # ── 5. QWeb view: JavaScript language→pricelist switch ────────────
    typer.secho("\n5. QWeb view: language → pricelist auto-switch", bold=True)

    # Replace placeholders with real IDs
    arch = ECOM_PRICELIST_LANG_SWITCH_ARCH.format(
        pen_pricelist_id=pen_pl_id,
        usd_pricelist_id=usd_pl_id,
    )

    _upsert_qweb_view(client,
        name='agency_ecommerce.pricelist_lang_switch',
        arch_en=arch,
        parent_key='website.layout',
    )

    # ── Summary ───────────────────────────────────────────────────────
    typer.secho(f"\n{'=' * 70}", bold=True)
    typer.secho(f"  PRICELIST CURRENCY SETUP COMPLETE — {label}", fg=typer.colors.BLUE, bold=True)
    typer.secho(f"{'=' * 70}", bold=True)
    typer.secho(f"\n  PEN pricelist: id={pen_pl_id} (LATAM countries)", fg=typer.colors.CYAN)
    typer.secho(f"  USD pricelist: id={usd_pl_id} (International — all countries)", fg=typer.colors.CYAN)
    typer.secho(f"  LATAM group: id={latam_group_id} ({len(LATAM_COUNTRY_CODES)} countries)", fg=typer.colors.CYAN)
    typer.secho(f"  International group: id={intl_group_id} ({len(all_codes)} countries)", fg=typer.colors.CYAN)
    typer.secho(f"  QWeb view: agency_ecommerce.pricelist_lang_switch", fg=typer.colors.CYAN)
    typer.secho("\nVerificacion:", fg=typer.colors.YELLOW)
    typer.secho("  - /es/shop → precios en S/ (PEN)", fg=typer.colors.YELLOW)
    typer.secho("  - Cambiar idioma a English → precios en $ (USD)", fg=typer.colors.YELLOW)
    typer.secho("  - Producto con precio USD manual → muestra ese precio", fg=typer.colors.YELLOW)
    typer.secho("  - Producto sin precio manual → conversion automatica PEN→USD", fg=typer.colors.YELLOW)
    typer.secho("  - Sin doble recarga al navegar paginas del mismo idioma", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
