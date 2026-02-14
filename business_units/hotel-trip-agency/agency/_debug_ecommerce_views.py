#!/usr/bin/env python3
"""Debug ecommerce QWeb views for tours.

Investigates why 3 QWeb inherited views created via XML-RPC are not taking
effect on the Odoo 19 SaaS ecommerce.

Checks:
1. Our 3 views: active, key, inherit_id, type, website_id
2. Parent views: website_sale.cta_wrapper, website_sale.product,
   website_sale.shop_product_buttons — keys and IDs
3. Arch of website_sale.shop_product_buttons (the add-to-cart button structure)
4. Product configurator / modal templates
5. Whether key attribute is required for QWeb website templates

Usage:
    uv run python business_units/hotel-trip-agency/agency/_debug_ecommerce_views.py
"""
import sys
import os
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from odoo_cli import OdooClient


def sep(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def print_view(v, fields=None):
    """Pretty-print a view record."""
    fields = fields or list(v.keys())
    for f in fields:
        val = v.get(f)
        if f == 'arch' and val:
            # Truncate long arch for readability
            print(f"  {f}:")
            for line in str(val).split('\n'):
                print(f"    {line}")
        elif isinstance(val, (list, tuple)) and len(val) == 2:
            print(f"  {f}: {val[0]} ({val[1]})")
        else:
            print(f"  {f}: {val}")


def main():
    client = OdooClient()
    client.connect()
    print(f"Connected as UID={client.uid}")

    # ── 1. Read our 3 created views ──────────────────────────────────────
    sep("1. OUR 3 ECOMMERCE VIEWS")
    our_view_names = [
        'agency_ecommerce.cta_tour_quote',
        'agency_ecommerce.product_tour_modal',
        'agency_ecommerce.listing_tour_quote',
    ]
    check_fields = [
        'id', 'name', 'key', 'active', 'type', 'priority',
        'inherit_id', 'website_id', 'mode', 'arch',
        'customize_show',
    ]
    for vname in our_view_names:
        print(f"\n--- Searching for name='{vname}' ---")
        views = client.search_read('ir.ui.view',
            domain=[['name', '=', vname]],
            fields=check_fields)
        if not views:
            # Also try searching by key
            views = client.search_read('ir.ui.view',
                domain=[['key', '=', vname]],
                fields=check_fields)
            if views:
                print(f"  (Found by key, not name)")
        if not views:
            print(f"  NOT FOUND!")
        for v in views:
            print_view(v, check_fields)

    # ── 2. Read the parent views ─────────────────────────────────────────
    sep("2. PARENT VIEWS")
    parent_keys = [
        'website_sale.cta_wrapper',
        'website_sale.product',
        'website_sale.shop_product_buttons',
    ]
    parent_fields = [
        'id', 'name', 'key', 'active', 'type', 'priority',
        'inherit_id', 'website_id', 'mode',
    ]
    parent_ids = {}
    for pkey in parent_keys:
        print(f"\n--- key='{pkey}' ---")
        views = client.search_read('ir.ui.view',
            domain=[['key', '=', pkey]],
            fields=parent_fields)
        if not views:
            # Try by name
            views = client.search_read('ir.ui.view',
                domain=[['name', 'ilike', pkey.split('.')[-1]]],
                fields=parent_fields, limit=5)
            if views:
                print(f"  (Found by name search, not key)")
        if not views:
            print(f"  NOT FOUND!")
        for v in views:
            print_view(v, parent_fields)
            parent_ids[pkey] = v['id']

    # ── 3. Read arch of shop_product_buttons ─────────────────────────────
    sep("3. ARCH OF website_sale.shop_product_buttons")
    target_id = parent_ids.get('website_sale.shop_product_buttons')
    if target_id:
        views = client.search_read('ir.ui.view',
            domain=[['id', '=', target_id]],
            fields=['id', 'name', 'arch'])
        if views:
            print_view(views[0], ['id', 'name', 'arch'])
    else:
        print("  Could not find shop_product_buttons parent view")

    # Also read cta_wrapper arch
    sep("3b. ARCH OF website_sale.cta_wrapper")
    cta_id = parent_ids.get('website_sale.cta_wrapper')
    if cta_id:
        views = client.search_read('ir.ui.view',
            domain=[['id', '=', cta_id]],
            fields=['id', 'name', 'arch'])
        if views:
            print_view(views[0], ['id', 'name', 'arch'])
    else:
        print("  Could not find cta_wrapper parent view")

    # Also read product arch (just the first 100 lines or so for xpath targets)
    sep("3c. ARCH OF website_sale.product (first portion)")
    prod_id = parent_ids.get('website_sale.product')
    if prod_id:
        views = client.search_read('ir.ui.view',
            domain=[['id', '=', prod_id]],
            fields=['id', 'name', 'arch'])
        if views:
            arch = views[0].get('arch', '')
            # Print just a summary since it's likely very long
            lines = arch.split('\n')
            print(f"  Total arch lines: {len(lines)}")
            # Look for section id="product_detail"
            for i, line in enumerate(lines):
                if 'product_detail' in line:
                    print(f"  Line {i}: {line.strip()}")
            # Print first/last 20 lines
            print("\n  --- First 30 lines ---")
            for line in lines[:30]:
                print(f"    {line}")
            print(f"\n  --- Last 20 lines ---")
            for line in lines[-20:]:
                print(f"    {line}")
    else:
        print("  Could not find product parent view")

    # ── 4. Product configurator views ────────────────────────────────────
    sep("4. PRODUCT CONFIGURATOR / MODAL VIEWS")
    config_views = client.search_read('ir.ui.view',
        domain=[['key', 'ilike', 'product_configurator']],
        fields=['id', 'name', 'key', 'type', 'active', 'inherit_id'],
        limit=20)
    if not config_views:
        print("  No views found with key containing 'product_configurator'")
    for v in config_views:
        print_view(v, ['id', 'name', 'key', 'type', 'active', 'inherit_id'])
        print()

    # NOTE: arch field is NOT stored in Odoo 19 - cannot search by arch content
    # Instead, search by key/name patterns for configurator-related views
    print("\n--- Views with 'configurar' or 'configure' in name ---")
    config_views2 = client.search_read('ir.ui.view',
        domain=[['name', 'ilike', 'configur'], ['type', '=', 'qweb']],
        fields=['id', 'name', 'key', 'type', 'active', 'inherit_id'],
        limit=10)
    for v in config_views2:
        print_view(v, ['id', 'name', 'key', 'type', 'active', 'inherit_id'])
        print()

    # Search for add_to_cart related QWeb views by key/name
    print("\n--- QWeb views with 'add_to_cart' or 'cart' in key ---")
    atc_views = client.search_read('ir.ui.view',
        domain=[['key', 'ilike', 'cart'], ['type', '=', 'qweb']],
        fields=['id', 'name', 'key', 'type', 'active', 'inherit_id'],
        limit=20)
    for v in atc_views:
        print_view(v, ['id', 'name', 'key', 'type', 'active', 'inherit_id'])
        print()

    print("\n--- QWeb views with 'add_to_cart' in name ---")
    atc_views2 = client.search_read('ir.ui.view',
        domain=[['name', 'ilike', 'add_to_cart'], ['type', '=', 'qweb']],
        fields=['id', 'name', 'key', 'type', 'active', 'inherit_id'],
        limit=20)
    for v in atc_views2:
        print_view(v, ['id', 'name', 'key', 'type', 'active', 'inherit_id'])
        print()

    # ── 5. Check if key is required for website QWeb views ───────────────
    sep("5. CHECK KEY PATTERN FOR WEBSITE QWEB VIEWS")

    # Check some known website_sale inherited views for their key pattern
    ws_views = client.search_read('ir.ui.view',
        domain=[
            ['key', 'ilike', 'website_sale.'],
            ['type', '=', 'qweb'],
            ['inherit_id', '!=', False],
        ],
        fields=['id', 'name', 'key', 'active', 'mode', 'inherit_id', 'website_id'],
        limit=15)
    print(f"\n  Found {len(ws_views)} website_sale QWeb inherited views:")
    for v in ws_views:
        print(f"  id={v['id']} key={v['key']} name={v['name']} mode={v.get('mode')} "
              f"active={v['active']} inherit={v['inherit_id']} "
              f"website_id={v.get('website_id')}")

    # ── 6. Check all views that inherit from our parent views ────────────
    sep("6. ALL VIEWS INHERITING FROM OUR PARENT VIEWS")
    for pkey, pid in parent_ids.items():
        print(f"\n--- Children of {pkey} (id={pid}) ---")
        children = client.search_read('ir.ui.view',
            domain=[['inherit_id', '=', pid]],
            fields=['id', 'name', 'key', 'active', 'type', 'mode', 'priority', 'website_id'],
            limit=30)
        if not children:
            print("  No children found")
        for c in children:
            print(f"  id={c['id']} name={c['name']} key={c.get('key')} "
                  f"active={c['active']} type={c['type']} mode={c.get('mode')} "
                  f"priority={c.get('priority')} website_id={c.get('website_id')}")

    # ── 7. Check the website record ──────────────────────────────────────
    sep("7. WEBSITE RECORDS")
    websites = client.search_read('website',
        domain=[],
        fields=['id', 'name', 'domain'],
        limit=5)
    for w in websites:
        print(f"  id={w['id']} name={w['name']} domain={w.get('domain')}")

    # ── 8. Check views related to add-to-cart by name/key ──────────────
    sep("8. QWeb VIEWS WITH 'cta' OR 'add_to_cart' IN NAME/KEY")
    for search_term in ['cta', 'add_to_cart']:
        print(f"\n--- name ilike '{search_term}' ---")
        atcw_views = client.search_read('ir.ui.view',
            domain=[['name', 'ilike', search_term], ['type', '=', 'qweb']],
            fields=['id', 'name', 'key', 'type', 'active', 'inherit_id'],
            limit=20)
        if not atcw_views:
            print(f"  No views found")
        for v in atcw_views:
            print_view(v, ['id', 'name', 'key', 'type', 'active', 'inherit_id'])
            print()

    # ── 9. Check the ir.ui.view fields_get for 'key' ────────────────────
    sep("9. IR.UI.VIEW FIELDS: key, website_id, customize_show")
    fg = client.execute('ir.ui.view', 'fields_get', [],
                        attributes=['string', 'type', 'help'])
    for fname in ['key', 'website_id', 'customize_show', 'mode', 'active']:
        info = fg.get(fname, {})
        print(f"  {fname}: type={info.get('type')} string={info.get('string')} "
              f"help={info.get('help', 'N/A')}")

    # ── 10. Attempt to read the combined/rendered arch ───────────────────
    sep("10. CHECK IF OUR VIEWS HAVE CORRECT INHERIT_ID LINKING")
    for vname in our_view_names:
        views = client.search_read('ir.ui.view',
            domain=[['name', '=', vname]],
            fields=['id', 'name', 'inherit_id', 'mode', 'key', 'active', 'type'])
        if views:
            v = views[0]
            inherit = v.get('inherit_id')
            print(f"\n  {vname}:")
            print(f"    id={v['id']} inherit_id={inherit} mode={v.get('mode')} "
                  f"key={v.get('key')} active={v['active']} type={v['type']}")
            if inherit:
                # Check if the inherit_id view exists and is the right one
                parent = client.search_read('ir.ui.view',
                    domain=[['id', '=', inherit[0]]],
                    fields=['id', 'name', 'key', 'type'])
                if parent:
                    print(f"    -> parent: id={parent[0]['id']} name={parent[0]['name']} "
                          f"key={parent[0].get('key')} type={parent[0]['type']}")
                else:
                    print(f"    -> PARENT NOT FOUND (id={inherit[0]})!")

    # ── 11. Check arch_db field (stored version of arch) ────────────────
    sep("11. CHECK arch_db FIELD ON OUR VIEWS")
    fg = client.execute('ir.ui.view', 'fields_get', [],
                        attributes=['string', 'type', 'store'])
    arch_db_info = fg.get('arch_db', {})
    arch_info = fg.get('arch', {})
    print(f"  arch: type={arch_info.get('type')} store={arch_info.get('store')}")
    print(f"  arch_db: type={arch_db_info.get('type')} store={arch_db_info.get('store')}")

    # Try to read arch_db for our views
    for vname in our_view_names:
        views = client.search_read('ir.ui.view',
            domain=[['name', '=', vname]],
            fields=['id', 'name', 'arch_db'])
        if views:
            v = views[0]
            arch_db = v.get('arch_db', '')
            print(f"\n  {vname} (id={v['id']}) arch_db present: {bool(arch_db)}")
            if arch_db:
                lines = str(arch_db).split('\n')
                for line in lines[:5]:
                    print(f"    {line}")
                if len(lines) > 5:
                    print(f"    ... ({len(lines)} lines total)")

    # ── 12. Search for website_sale.product_configurator specifically ────
    sep("12. PRODUCT CONFIGURATOR TEMPLATE")
    pc_views = client.search_read('ir.ui.view',
        domain=[['key', 'ilike', 'website_sale.product_configurator']],
        fields=['id', 'name', 'key', 'type', 'active', 'inherit_id', 'arch'],
        limit=5)
    if not pc_views:
        print("  No view found with key 'website_sale.product_configurator'")
    for v in pc_views:
        print_view(v, ['id', 'name', 'key', 'type', 'active', 'inherit_id', 'arch'])

    # Also check sale_product_configurator
    pc_views2 = client.search_read('ir.ui.view',
        domain=[['key', 'ilike', 'sale_product_configurator']],
        fields=['id', 'name', 'key', 'type', 'active', 'inherit_id', 'arch'],
        limit=5)
    if pc_views2:
        print("\n--- sale_product_configurator views ---")
    for v in pc_views2:
        print_view(v, ['id', 'name', 'key', 'type', 'active', 'inherit_id', 'arch'])

    # ── 13. Check the 'Tours y Paquetes turisticos' category ─────────────
    sep("13. TOUR CATEGORY CHECK")
    cats = client.search_read('product.category',
        domain=[['name', 'ilike', 'Tours']],
        fields=['id', 'name', 'complete_name'])
    if not cats:
        print("  NO category found with 'Tours' in name!")
    for c in cats:
        print(f"  id={c['id']} name='{c['name']}' complete_name='{c.get('complete_name')}'")

    # Check exact match with accent
    cats2 = client.search_read('product.category',
        domain=[['name', '=', 'Tours y Paquetes turísticos']],
        fields=['id', 'name'])
    print(f"\n  Exact match 'Tours y Paquetes turisticos' (with accent): {len(cats2)} found")
    cats3 = client.search_read('product.category',
        domain=[['name', '=', 'Tours y Paquetes turisticos']],
        fields=['id', 'name'])
    print(f"  Exact match 'Tours y Paquetes turisticos' (no accent): {len(cats3)} found")

    # ── 14. Read arch_db for add_to_cart_wrap searches ───────────────────
    sep("14. SEARCH arch_db FOR add_to_cart_wrap")
    # arch_db IS stored, so we can search on it
    if arch_db_info.get('store'):
        atcw_views = client.search_read('ir.ui.view',
            domain=[['arch_db', 'ilike', 'add_to_cart_wrap'], ['type', '=', 'qweb']],
            fields=['id', 'name', 'key', 'type', 'active', 'inherit_id'],
            limit=20)
        print(f"  Found {len(atcw_views)} views with 'add_to_cart_wrap' in arch_db")
        for v in atcw_views:
            print(f"    id={v['id']} name={v['name']} key={v.get('key')} "
                  f"active={v['active']} inherit={v.get('inherit_id')}")
    else:
        print("  arch_db is NOT stored, cannot search")

    # ── 15. Check for 'add_to_cart' button name in arch_db ──────────────
    sep("15. SEARCH arch_db FOR button name='add_to_cart'")
    if arch_db_info.get('store'):
        btn_views = client.search_read('ir.ui.view',
            domain=[['arch_db', 'ilike', "name=\"add_to_cart\""], ['type', '=', 'qweb']],
            fields=['id', 'name', 'key', 'type', 'active', 'inherit_id', 'arch'],
            limit=20)
        print(f"  Found {len(btn_views)} views with button name='add_to_cart' in arch_db")
        for v in btn_views:
            print(f"\n    id={v['id']} name={v['name']} key={v.get('key')}")
            # Show add_to_cart lines from arch
            arch = v.get('arch', '')
            for i, line in enumerate(arch.split('\n')):
                if 'add_to_cart' in line.lower():
                    print(f"      L{i}: {line.strip()}")
    else:
        print("  arch_db is NOT stored, cannot search")

    # ── 16. CRITICAL: Check booking_engine replacement conflict ─────────
    sep("16. BOOKING_ENGINE CONFLICT ANALYSIS")
    be_view = client.search_read('ir.ui.view',
        domain=[['key', '=', 'booking_engine.custom_add_cart_name']],
        fields=['id', 'name', 'key', 'arch', 'priority', 'active', 'inherit_id'])
    if be_view:
        v = be_view[0]
        print(f"  booking_engine.custom_add_cart_name (id={v['id']})")
        print(f"    priority={v['priority']} inherits={v['inherit_id']}")
        print(f"    This view REPLACES the add-to-cart button with 'Book' text")
        print(f"    Priority {v['priority']} < our priority 99")
        print(f"    -> It runs BEFORE our view")
        print(f"    -> The button still has name='add_to_cart' after replacement")
        print(f"    -> Our xpath on div#add_to_cart_wrap should still work")
        print(f"    RESULT: Not a conflict for cta_wrapper view")

    # ── 17. Check _website_show_quick_add for service products ───────────
    sep("17. SERVICE PRODUCTS & _website_show_quick_add()")
    tour_prods = client.search_read('product.template',
        domain=[['categ_id.name', '=', 'Tours y Paquetes turísticos']],
        fields=['id', 'name', 'type', 'website_published', 'sale_ok', 'public_categ_ids'],
        limit=10)
    print(f"  Tour products found: {len(tour_prods)}")
    for p in tour_prods:
        print(f"    id={p['id']} name={p['name']} type={p['type']} "
              f"published={p['website_published']} public_categ_ids={p['public_categ_ids']}")
    print()
    print("  CRITICAL: In shop_product_buttons (listing), the button is wrapped in:")
    print("    <t t-if=\"product._website_show_quick_add()\">")
    print("  For service products, _website_show_quick_add() likely returns False")
    print("  -> The whole block is skipped, our button replacement never renders")
    print("  -> Our 'after' positioned element is ALSO inside the skipped scope")

    # ── 18. FINAL ANALYSIS ───────────────────────────────────────────────
    sep("FINAL ANALYSIS - ROOT CAUSES")
    print("""
ISSUE 1: LISTING VIEW (agency_ecommerce.listing_tour_quote)
===========================================================
  Parent: website_sale.shop_product_buttons (id=3358)
  The add-to-cart button in the listing is wrapped inside:
    <t t-if="product._website_show_quick_add()" t-call="...">

  Tour products have type='service'. For service products,
  _website_show_quick_add() returns False, so the ENTIRE block
  (including the button we're targeting with xpath) is NEVER rendered.

  Our xpath successfully modifies the XML, but the parent t-if
  prevents the whole block from rendering for service products.

  FIX: Instead of targeting the button INSIDE the t-if, we need to
  add our "Cotizar" button OUTSIDE the t-if block. Target the
  <div class="o_wsale_product_action_row"> or the parent
  <t name="buttons_container"> element.

ISSUE 2: PRODUCT DETAIL CTA (agency_ecommerce.cta_tour_quote)
==============================================================
  Parent: website_sale.cta_wrapper (id=3367)
  The xpath on div#add_to_cart_wrap should work correctly since
  it's not inside a t-if block. However:

  a) booking_engine.custom_add_cart_name (priority=16) REPLACES
     the button text with "Book". Our view (priority=99) then adds
     t-if on the div wrapper. This should still work.

  b) BUT: the div#add_to_cart_wrap has a dynamic t-attf-class that
     includes d-none when combination_info['prevent_zero_price_sale']
     is True. If tour products have price=0, the div is already hidden.

  c) POTENTIAL ISSUE: We're adding t-if attribute to add_to_cart_wrap
     via xpath attributes. If the div already has a t-attf-class
     condition, adding t-if should still work. But if the condition
     evaluates before rendering, it may conflict.

  d) The modal references product.categ_id.name which is the INTERNAL
     category. This IS a valid field on product.template and should work
     in QWeb context. Verified: category name matches with accent.

ISSUE 3: MISSING PUBLIC CATEGORIES ON TOUR PRODUCTS
====================================================
  Tour products public_categ_ids status:
  - City Tour Cusco: public_categ_ids=[] (empty!) + published=False
  - Cusco 3D/2N: public_categ_ids=[] (empty!) + published=False
  - Palcoyo: public_categ_ids=[11] (Adventure) + published=True

  Only Palcoyo is published and visible in the shop.
  Other tour products are NOT published and NOT visible.

ISSUE 4: KEY ATTRIBUTE
======================
  Our views have auto-generated keys (gen_key.xxxxx) instead of
  meaningful keys like 'agency_ecommerce.cta_tour_quote'.
  While this doesn't prevent the views from working, proper keys
  make them easier to manage and reference.

RECOMMENDED FIXES:
==================
1. For listing: Restructure the xpath to target OUTSIDE the
   _website_show_quick_add() t-if block. Use:
   <xpath expr="//div[@class='o_wsale_product_action_row']" position="inside">
     <div t-if="product.categ_id.name == 'Tours y Paquetes turisticos'" ...>
   or better: target the t-call and add our button after the whole t-call block.

2. For product detail: The current approach should work if the product
   has a non-zero price. Verify on the live website.

3. Publish the other tour products and assign public categories.

4. Update keys to meaningful values:
   client.execute('ir.ui.view', 'write', [4786], {'key': 'agency_ecommerce.cta_tour_quote'})
""")
    print("\nScript completed successfully.")


if __name__ == '__main__':
    main()
