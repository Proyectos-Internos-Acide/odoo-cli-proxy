#!/usr/bin/env python3
"""Debug: ValueError 'Expected singleton: product.template()' on ecommerce product page.

The error `Expected singleton: product.template()` in `get_combination_info_website`
means Odoo is calling a method that expects a single record on an empty recordset.
This usually happens when:
  - A product has no variants (product_variant_ids is empty)
  - The product.template record is somehow corrupted
  - A QWeb view references `product` but the context resolves to empty recordset

This script investigates all tour products and the "Walking Tour Cusco" specifically.

Usage:
    uv run python business_units/hotel-trip-agency/agency/_debug_product_page.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from odoo_cli import OdooClient


def sep(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def main():
    client = OdooClient()
    client.connect()
    print(f"Connected as UID={client.uid}")

    # ══════════════════════════════════════════════════════════════════════
    # 1. Find ALL tour products
    # ══════════════════════════════════════════════════════════════════════
    sep("1. ALL TOUR PRODUCTS (categ_id.name = 'Tours y Paquetes turisticos')")

    tour_fields = [
        'id', 'name', 'type', 'website_published', 'website_url',
        'product_variant_ids', 'attribute_line_ids', 'categ_id',
        'list_price', 'sale_ok', 'active',
    ]

    # Search with accent (the actual category name)
    tours = client.search_read('product.template',
        domain=[['categ_id.name', '=', 'Tours y Paquetes turísticos']],
        fields=tour_fields)

    if not tours:
        # Try without accent
        print("  No results with accent, trying without...")
        tours = client.search_read('product.template',
            domain=[['categ_id.name', 'ilike', 'Tours y Paquetes']],
            fields=tour_fields)

    print(f"\n  Found {len(tours)} tour product(s):\n")

    walking_tour = None
    for t in tours:
        variant_ids = t.get('product_variant_ids', [])
        attr_lines = t.get('attribute_line_ids', [])
        print(f"  --- product.template id={t['id']} ---")
        print(f"    name:              {t['name']}")
        print(f"    type:              {t['type']}")
        print(f"    website_published: {t['website_published']}")
        print(f"    website_url:       {t.get('website_url')}")
        print(f"    list_price:        {t.get('list_price')}")
        print(f"    sale_ok:           {t.get('sale_ok')}")
        print(f"    active:            {t.get('active')}")
        print(f"    categ_id:          {t.get('categ_id')}")
        print(f"    product_variant_ids: {variant_ids} (count={len(variant_ids)})")
        print(f"    attribute_line_ids:  {attr_lines} (count={len(attr_lines)})")

        # Flag potential singleton issue
        if len(variant_ids) == 0:
            print(f"    *** WARNING: NO VARIANTS! This WILL cause singleton error ***")

        if 'walking' in t['name'].lower() or 'cusco' in t['name'].lower():
            walking_tour = t
        print()

    # ══════════════════════════════════════════════════════════════════════
    # 2. Deep-dive into "Walking Tour Cusco" specifically
    # ══════════════════════════════════════════════════════════════════════
    sep("2. WALKING TOUR CUSCO - DETAILED CHECK")

    if not walking_tour:
        # Search explicitly by name
        wt = client.search_read('product.template',
            domain=[['name', 'ilike', 'Walking Tour Cusco']],
            fields=tour_fields + ['product_variant_count', 'is_published'])
        if wt:
            walking_tour = wt[0]
        else:
            # Try broader search
            wt = client.search_read('product.template',
                domain=[['name', 'ilike', 'Walking Tour']],
                fields=tour_fields + ['product_variant_count', 'is_published'])
            if wt:
                walking_tour = wt[0]

    if walking_tour:
        wt_id = walking_tour['id']
        print(f"\n  Found: id={wt_id} name='{walking_tour['name']}'")

        # Re-read with extra fields
        wt_detail = client.search_read('product.template',
            domain=[['id', '=', wt_id]],
            fields=[
                'id', 'name', 'type', 'website_published', 'is_published',
                'website_url', 'product_variant_ids', 'product_variant_count',
                'attribute_line_ids', 'categ_id', 'list_price', 'sale_ok',
                'active', 'public_categ_ids', 'website_id',
            ])
        if wt_detail:
            wt = wt_detail[0]
            print(f"    type:                 {wt['type']}")
            print(f"    website_published:    {wt.get('website_published')}")
            print(f"    is_published:         {wt.get('is_published')}")
            print(f"    website_url:          {wt.get('website_url')}")
            print(f"    product_variant_ids:  {wt.get('product_variant_ids')}")
            print(f"    product_variant_count: {wt.get('product_variant_count')}")
            print(f"    attribute_line_ids:   {wt.get('attribute_line_ids')}")
            print(f"    list_price:           {wt.get('list_price')}")
            print(f"    sale_ok:              {wt.get('sale_ok')}")
            print(f"    active:               {wt.get('active')}")
            print(f"    public_categ_ids:     {wt.get('public_categ_ids')}")
            print(f"    website_id:           {wt.get('website_id')}")

            variant_ids = wt.get('product_variant_ids', [])
            if not variant_ids:
                print("\n    *** CRITICAL: NO PRODUCT VARIANTS ***")
                print("    This is the root cause of 'Expected singleton: product.template()'")
                print("    get_combination_info_website() calls self.product_variant_id")
                print("    which returns an empty recordset, then .ensure_one() fails")
            else:
                # Read variant details
                print(f"\n    Variant details:")
                variants = client.search_read('product.product',
                    domain=[['id', 'in', variant_ids]],
                    fields=['id', 'name', 'active', 'default_code', 'combination_indices',
                            'product_template_attribute_value_ids', 'lst_price'])
                for v in variants:
                    print(f"      id={v['id']} name={v['name']}")
                    print(f"        active={v['active']} default_code={v.get('default_code')}")
                    print(f"        combination_indices={v.get('combination_indices')}")
                    print(f"        ptav_ids={v.get('product_template_attribute_value_ids')}")
                    print(f"        lst_price={v.get('lst_price')}")

            # Check attribute lines detail
            attr_line_ids = wt.get('attribute_line_ids', [])
            if attr_line_ids:
                print(f"\n    Attribute line details:")
                attr_lines = client.search_read('product.template.attribute.line',
                    domain=[['id', 'in', attr_line_ids]],
                    fields=['id', 'attribute_id', 'value_ids', 'product_template_value_ids'])
                for al in attr_lines:
                    print(f"      id={al['id']} attribute={al.get('attribute_id')} "
                          f"values={al.get('value_ids')} ptav_ids={al.get('product_template_value_ids')}")
    else:
        print("  'Walking Tour Cusco' NOT FOUND - searching all products with 'Tour' in name...")
        all_tours = client.search_read('product.template',
            domain=[['name', 'ilike', 'Tour']],
            fields=['id', 'name', 'product_variant_ids', 'website_published'],
            limit=20)
        for t in all_tours:
            print(f"    id={t['id']} name={t['name']} "
                  f"variants={t.get('product_variant_ids')} "
                  f"published={t.get('website_published')}")

    # ══════════════════════════════════════════════════════════════════════
    # 3. Check website prevent_zero_price_sale setting
    # ══════════════════════════════════════════════════════════════════════
    sep("3. WEBSITE prevent_zero_price_sale SETTING")

    websites = client.search_read('website',
        domain=[],
        fields=['id', 'name', 'domain', 'prevent_zero_price_sale'])
    for w in websites:
        print(f"  id={w['id']} name={w['name']} domain={w.get('domain')}")
        print(f"    prevent_zero_price_sale: {w.get('prevent_zero_price_sale')}")

    if websites and websites[0].get('prevent_zero_price_sale'):
        print("\n  *** prevent_zero_price_sale is ENABLED ***")
        print("  Products with price=0 will have add_to_cart hidden via JS")
        print("  This interacts with get_combination_info_website() — could amplify the singleton bug")
    else:
        print("\n  prevent_zero_price_sale is disabled (default)")

    # ══════════════════════════════════════════════════════════════════════
    # 4. Check our 3 agency_ecommerce views (active status)
    # ══════════════════════════════════════════════════════════════════════
    sep("4. OUR 3 AGENCY ECOMMERCE VIEWS - ACTIVE STATUS")

    our_views = [
        'agency_ecommerce.cta_tour_quote',
        'agency_ecommerce.product_tour_modal',
        'agency_ecommerce.listing_tour_quote',
    ]

    view_check_fields = [
        'id', 'name', 'key', 'active', 'type', 'inherit_id',
        'mode', 'priority', 'website_id',
    ]

    view_records = {}
    for vname in our_views:
        views = client.search_read('ir.ui.view',
            domain=[['name', '=', vname]],
            fields=view_check_fields)
        if not views:
            views = client.search_read('ir.ui.view',
                domain=[['key', '=', vname]],
                fields=view_check_fields)
        if views:
            v = views[0]
            view_records[vname] = v
            print(f"\n  {vname}:")
            print(f"    id={v['id']} active={v['active']} type={v['type']}")
            print(f"    key={v.get('key')} mode={v.get('mode')} priority={v.get('priority')}")
            print(f"    inherit_id={v.get('inherit_id')} website_id={v.get('website_id')}")
        else:
            print(f"\n  {vname}: NOT FOUND!")

    # ══════════════════════════════════════════════════════════════════════
    # 5. Toggle CTA view (id=4786) to test if it causes the error
    # ══════════════════════════════════════════════════════════════════════
    sep("5. TOGGLE CTA VIEW (DEACTIVATE + REACTIVATE)")

    cta_view = view_records.get('agency_ecommerce.cta_tour_quote')
    if cta_view:
        cta_id = cta_view['id']
        print(f"\n  CTA view id={cta_id}, current active={cta_view['active']}")

        # Step A: Deactivate
        print(f"\n  [STEP A] Deactivating view id={cta_id}...")
        client.execute('ir.ui.view', 'write', [cta_id], {'active': False})
        check = client.search_read('ir.ui.view',
            domain=[['id', '=', cta_id]],
            fields=['id', 'active'])
        print(f"    After deactivation: active={check[0]['active'] if check else 'NOT FOUND'}")

        # Brief pause to let the change propagate
        print(f"    (pausing 2s to let cache invalidate...)")
        time.sleep(2)

        # Step B: Reactivate immediately
        print(f"\n  [STEP B] Reactivating view id={cta_id}...")
        client.execute('ir.ui.view', 'write', [cta_id], {'active': True})
        check2 = client.search_read('ir.ui.view',
            domain=[['id', '=', cta_id]],
            fields=['id', 'active'])
        print(f"    After reactivation: active={check2[0]['active'] if check2 else 'NOT FOUND'}")
        print(f"\n  CTA view has been restored to active=True")
    else:
        # Try by direct ID=4786
        print(f"\n  CTA view not found by name, trying id=4786 directly...")
        direct = client.search_read('ir.ui.view',
            domain=[['id', '=', 4786]],
            fields=['id', 'name', 'key', 'active'])
        if direct:
            v = direct[0]
            cta_id = v['id']
            print(f"    Found: id={cta_id} name={v['name']} key={v.get('key')} active={v['active']}")

            print(f"\n  [STEP A] Deactivating view id={cta_id}...")
            client.execute('ir.ui.view', 'write', [cta_id], {'active': False})
            check = client.search_read('ir.ui.view',
                domain=[['id', '=', cta_id]],
                fields=['id', 'active'])
            print(f"    After deactivation: active={check[0]['active'] if check else 'NOT FOUND'}")

            print(f"    (pausing 2s...)")
            time.sleep(2)

            print(f"\n  [STEP B] Reactivating view id={cta_id}...")
            client.execute('ir.ui.view', 'write', [cta_id], {'active': True})
            check2 = client.search_read('ir.ui.view',
                domain=[['id', '=', cta_id]],
                fields=['id', 'active'])
            print(f"    After reactivation: active={check2[0]['active'] if check2 else 'NOT FOUND'}")
            print(f"\n  CTA view has been restored to active=True")
        else:
            print("    View id=4786 NOT FOUND either!")

    # ══════════════════════════════════════════════════════════════════════
    # 6. Additional singleton-related checks
    # ══════════════════════════════════════════════════════════════════════
    sep("6. ADDITIONAL SINGLETON CHECKS")

    # product_variant_count is NOT stored in Odoo 19, cannot use in domain
    # Instead, find published products and check variant_ids in Python
    print("\n  Checking ALL published products for missing variants...")
    published_products = client.search_read('product.template',
        domain=[['website_published', '=', True]],
        fields=['id', 'name', 'type', 'categ_id', 'website_url', 'active',
                'product_variant_ids'],
        limit=100)
    zero_variant_products = [p for p in published_products
                             if not p.get('product_variant_ids')]
    if zero_variant_products:
        print(f"  Found {len(zero_variant_products)} published products with 0 variants:")
        for p in zero_variant_products:
            print(f"    id={p['id']} name={p['name']} type={p['type']} "
                  f"categ={p.get('categ_id')} url={p.get('website_url')}")
    else:
        print(f"  All {len(published_products)} published products have at least 1 variant.")

    # Check if any tour product has inactive variants
    print("\n  Checking tour products for inactive variants...")
    for t in tours:
        variant_ids = t.get('product_variant_ids', [])
        if variant_ids:
            # Check active status of variants
            variants = client.search_read('product.product',
                domain=[['id', 'in', variant_ids]],
                fields=['id', 'name', 'active'])
            inactive = [v for v in variants if not v['active']]
            if inactive:
                print(f"    product.template id={t['id']} ({t['name']}): "
                      f"{len(inactive)} INACTIVE variant(s)!")
                for v in inactive:
                    print(f"      variant id={v['id']} name={v['name']} active={v['active']}")
        else:
            print(f"    product.template id={t['id']} ({t['name']}): NO VARIANTS AT ALL")

    # Also search product.product directly for these templates
    print("\n  Cross-checking: search product.product by product_tmpl_id for tour templates...")
    for t in tours:
        variants_direct = client.search_read('product.product',
            domain=[['product_tmpl_id', '=', t['id']]],
            fields=['id', 'name', 'active', 'product_tmpl_id'])
        active_count = sum(1 for v in variants_direct if v['active'])
        inactive_count = sum(1 for v in variants_direct if not v['active'])
        print(f"    template id={t['id']} ({t['name']}): "
              f"{len(variants_direct)} total variants, "
              f"{active_count} active, {inactive_count} inactive")
        if not variants_direct:
            print(f"      *** NO product.product RECORDS for this template! ***")
            print(f"      This is the root cause of the singleton error!")

    # ══════════════════════════════════════════════════════════════════════
    # ANALYSIS
    # ══════════════════════════════════════════════════════════════════════
    sep("ANALYSIS")
    print("""
  ERROR: ValueError: Expected singleton: product.template()
  LOCATION: get_combination_info_website

  This error occurs when Odoo's website_sale controller calls
  get_combination_info_website() on a product.template record that
  resolves to an EMPTY recordset (product.template()).

  ROOT CAUSES (in order of likelihood):

  1. PRODUCT HAS NO VARIANTS (product.product records)
     - get_combination_info_website() internally accesses
       self._get_first_possible_combination() or product_variant_id
     - If product_variant_ids is empty, browsing returns empty recordset
     - ensure_one() on empty recordset raises ValueError

  2. PRODUCT HAS ONLY INACTIVE VARIANTS
     - Same effect as #1: the active recordset is empty
     - product_variant_ids only returns active=True records

  3. CTA VIEW MODIFYING add_to_cart_wrap CONTEXT
     - Our agency_ecommerce.cta_tour_quote adds t-if on add_to_cart_wrap
     - The JS `get_combination_info_website` RPC is triggered by the
       product configurator JS, NOT by our QWeb view
     - BUT: if our view introduces an error in the QWeb rendering pipeline,
       it could cause the product variable to be empty in a child template
     - Toggle test (step 5) can help rule this out

  FIX OPTIONS:
  - If variants are missing: create the default variant manually
    client.execute('product.template', 'create_variant_ids', [[template_id]])
  - If CTA view is the issue: fix the xpath or deactivate
  - If prevent_zero_price_sale is triggering JS that hits the RPC
    on a broken product: set a non-zero price
""")

    print("\nScript completed.")


if __name__ == '__main__':
    main()
