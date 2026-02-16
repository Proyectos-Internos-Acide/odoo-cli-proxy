#!/usr/bin/env python3
"""Setup ecommerce customizations for tours.

Creates QWeb inherited views to:
- Replace "Add to Cart" with "Solicitar Cotizacion" button on tour product pages
- Show a modal form that creates a CRM lead (crm.lead)
- Replace listing button with "Cotizar" link for tour products

Detection: products with categ_id.name == 'Tours y Paquetes turisticos'

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_ecommerce.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from agency.defaults.views import (
    ECOM_CTA_TOUR_ARCH,
    ECOM_PRODUCT_MODAL_ARCH,
    ECOM_LISTING_TOUR_ARCH,
    ECOM_WISHLIST_TOUR_ARCH,
    ECOM_DYNAMIC_SNIPPET_TOUR_ARCH,
    ECOM_PRICE_PREFIX_TOUR_ARCH,
    ECOM_PRICE_PREFIX_LISTING_ARCH,
    ECOM_PRICE_PREFIX_WISHLIST_ARCH,
    ECOM_PRICE_PREFIX_DYNAMIC_ARCH,
    ECOM_TRANSLATIONS_ES,
)

app = typer.Typer(help="Setup ecommerce tour quote button (replaces add-to-cart for tours)")


# ── Helpers ───────────────────────────────────────────────────────────────

def _find_parent_view(client, key):
    """Find a QWeb view by its key. Returns (id, name) or (None, None)."""
    result = client.search_read('ir.ui.view',
        domain=[['key', '=', key]],
        fields=['id', 'name'], limit=1)
    if result:
        return result[0]['id'], result[0]['name']
    return None, None


def _upsert_qweb_view(client, name, arch_en, parent_key, translations=None):
    """Create or update a QWeb inherited view with proper key and translations.

    Uses update_field_translations() for es_419 — the proper Odoo API for
    xml-translated fields like arch_db on ir.ui.view.

    Args:
        arch_en: English arch XML (base/source language).
        translations: Optional dict {en_term: es_term} for es_419 translations.
    Returns view_id.
    """
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

    # Apply es_419 translations via update_field_translations
    if translations:
        client.execute('ir.ui.view', 'update_field_translations',
                        [view_id], 'arch_db', {'es_419': translations})
        typer.secho(f"    [i18n] es_419 translations applied ({len(translations)} terms)",
                    fg=typer.colors.CYAN)

    return view_id


# ── Main setup ────────────────────────────────────────────────────────────

@app.command()
def setup():
    """Create ecommerce QWeb views for tour quote button."""
    client = OdooClient()
    client.connect()

    typer.secho("=" * 70, bold=True)
    typer.secho("  ECOMMERCE TOUR QUOTE SETUP", bold=True)
    typer.secho("=" * 70, bold=True)

    es_translations = dict(ECOM_TRANSLATIONS_ES)

    # ── 1. CTA wrapper: replace add-to-cart on product page ────────
    typer.secho("\n1. CTA: Replace add-to-cart for tours (product page)", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.cta_tour_quote',
        arch_en=ECOM_CTA_TOUR_ARCH,
        parent_key='website_sale.cta_wrapper',
        translations=es_translations,
    )

    # ── 2. Modal form on product page ──────────────────────────────
    typer.secho("\n2. Modal: Quote request form (product page)", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.product_tour_modal',
        arch_en=ECOM_PRODUCT_MODAL_ARCH,
        parent_key='website_sale.product',
        translations=es_translations,
    )

    # ── 3. Listing button: replace in product grid ─────────────────
    typer.secho("\n3. Listing: Replace add-to-cart button for tours", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.listing_tour_quote',
        arch_en=ECOM_LISTING_TOUR_ARCH,
        parent_key='website_sale.shop_product_buttons',
        translations=es_translations,
    )

    # ── 4. Wishlist: replace add-to-cart for tours ─────────────────
    typer.secho("\n4. Wishlist: Hide add-to-cart for tours", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.wishlist_tour_quote',
        arch_en=ECOM_WISHLIST_TOUR_ARCH,
        parent_key='website_sale_wishlist.product_wishlist',
        translations=es_translations,
    )

    # ── 5. Dynamic snippets: replace add-to-cart for tours ───────
    typer.secho("\n5. Dynamic snippets: Hide add-to-cart for tours", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.dynamic_snippet_tour_quote',
        arch_en=ECOM_DYNAMIC_SNIPPET_TOUR_ARCH,
        parent_key='website_sale.dynamic_filter_template_product_product_products_item',
        translations=es_translations,
    )

    # ── 6. Price prefix: "estimated" / "aprox." for tours ──────
    typer.secho("\n6. Price prefix: 'estimated' / 'aprox.' for tour prices", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.price_prefix_tour',
        arch_en=ECOM_PRICE_PREFIX_TOUR_ARCH,
        parent_key='website_sale.product_price',
        translations=es_translations,
    )

    # ── 7. Price prefix: listing cards ──────────────────────────
    typer.secho("\n7. Price prefix: listing cards", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.price_prefix_listing',
        arch_en=ECOM_PRICE_PREFIX_LISTING_ARCH,
        parent_key='website_sale.products_item',
        translations=es_translations,
    )

    # ── 8. Price prefix: wishlist cards ──────────────────────────
    typer.secho("\n8. Price prefix: wishlist cards", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.price_prefix_wishlist',
        arch_en=ECOM_PRICE_PREFIX_WISHLIST_ARCH,
        parent_key='website_sale_wishlist.product_wishlist',
        translations=es_translations,
    )

    # ── 9. Price prefix: dynamic snippet cards ───────────────────
    typer.secho("\n9. Price prefix: dynamic snippet cards", bold=True)
    _upsert_qweb_view(client,
        name='agency_ecommerce.price_prefix_dynamic',
        arch_en=ECOM_PRICE_PREFIX_DYNAMIC_ARCH,
        parent_key='website_sale.price_dynamic_filter_template_product_product',
        translations=es_translations,
    )

    # ── Summary ───────────────────────────────────────────────────
    typer.secho("\n" + "=" * 70, bold=True)
    typer.secho("  ECOMMERCE TOUR QUOTE SETUP COMPLETE", fg=typer.colors.BLUE, bold=True)
    typer.secho("=" * 70, bold=True)
    typer.secho("\nCreated 9 QWeb inherited views:", fg=typer.colors.CYAN)
    typer.secho("  1. agency_ecommerce.cta_tour_quote — hides add-to-cart, shows 'Solicitar Cotizacion'", fg=typer.colors.CYAN)
    typer.secho("  2. agency_ecommerce.product_tour_modal — modal form → crm.lead", fg=typer.colors.CYAN)
    typer.secho("  3. agency_ecommerce.listing_tour_quote — listing button → 'Cotizar'", fg=typer.colors.CYAN)
    typer.secho("  4. agency_ecommerce.wishlist_tour_quote — wishlist cards → 'Cotizar'", fg=typer.colors.CYAN)
    typer.secho("  5. agency_ecommerce.dynamic_snippet_tour_quote — dynamic catalog → 'Cotizar'", fg=typer.colors.CYAN)
    typer.secho("  6. agency_ecommerce.price_prefix_tour — 'estimated' / 'aprox.' (product page)", fg=typer.colors.CYAN)
    typer.secho("  7. agency_ecommerce.price_prefix_listing — 'estimated' / 'aprox.' (listing)", fg=typer.colors.CYAN)
    typer.secho("  8. agency_ecommerce.price_prefix_wishlist — 'estimated' / 'aprox.' (wishlist)", fg=typer.colors.CYAN)
    typer.secho("  9. agency_ecommerce.price_prefix_dynamic — 'estimated' / 'aprox.' (dynamic snippets)", fg=typer.colors.CYAN)
    typer.secho("\nVerificacion:", fg=typer.colors.YELLOW)
    typer.secho("  - Ir a /shop — tours muestran 'Cotizar' + precio con prefijo 'aprox.'", fg=typer.colors.YELLOW)
    typer.secho("  - Click en tour → 'Solicitar Cotizacion' + precio con prefijo 'aprox.'", fg=typer.colors.YELLOW)
    typer.secho("  - Lista de deseos y bloques dinamicos — idem", fg=typer.colors.YELLOW)
    typer.secho("  - Formulario → verificar lead en CRM > Pipeline", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
