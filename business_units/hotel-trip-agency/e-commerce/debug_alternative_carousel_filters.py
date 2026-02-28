#!/usr/bin/env python3
"""
Debug why the "Alternative Products" carousel does NOT show on Odoo 19 ecommerce,
even though alternative_product_ids IS populated on products.

Previous investigation confirmed:
- alternative_product_ids is populated on 55 products
- View website_sale.alternative_products (id=3376) is ACTIVE
- The view uses a dynamic snippet with data-filter-id

This script investigates:
1. website.snippet.filter records (the dynamic snippet filter mechanism)
2. oe_structure user-saved views that might override the carousel block
3. COW (Copy-on-Write) views inheriting from alternative_products view
4. The actual filter method on product.template
5. All snippet filters with model product.product

Target: PRODUCTION instance (machupicchu-afdestiny-production)
"""
import xmlrpc.client

# --- Connection (PRODUCTION) ---
url = 'https://machupicchu-afdestiny-production.odoo.com'
db = 'machupicchu-afdestiny-production'
username = 'ayfdestinyeirl@gmail.com'
password = 'L^yUbD2^+p^2h.#'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')


def execute(model, method, *args, **kwargs):
    return models.execute_kw(db, uid, password, model, method, args, kwargs)


print(f"Connected to PRODUCTION: {url} (db={db}, uid={uid})")


# ============================================================================
# 1. CHECK ALL website.snippet.filter RECORDS
# ============================================================================
print("\n" + "=" * 80)
print("1. ALL website.snippet.filter RECORDS")
print("=" * 80)

try:
    # First check if the model exists
    model_exists = execute('ir.model', 'search_count',
                           [['model', '=', 'website.snippet.filter']])
    if not model_exists:
        print("\n  MODEL 'website.snippet.filter' DOES NOT EXIST!")
        print("  This means dynamic snippets are not available.")
    else:
        print(f"\n  Model exists. Reading all records...")

        # Get available fields first
        filter_fields_info = execute('website.snippet.filter', 'fields_get', [],
                                     attributes=['string', 'type'])
        print(f"\n  Available fields on website.snippet.filter:")
        for fname, finfo in sorted(filter_fields_info.items()):
            print(f"    {fname:40s} ({finfo['type']:12s}) - {finfo['string']}")

        # Read all snippet filters
        desired = ['id', 'name', 'model_name', 'action_server_id', 'filter_id',
                   'website_id', 'limit', 'model_id']
        read_fields = [f for f in desired if f in filter_fields_info]
        print(f"\n  Reading fields: {read_fields}")

        all_filters = execute('website.snippet.filter', 'search_read', [],
                              read_fields, order='id')
        print(f"\n  Total snippet filters: {len(all_filters)}")
        print()
        for sf in all_filters:
            print(f"  --- Filter ID: {sf['id']} ---")
            for k, v in sf.items():
                if k != 'id':
                    print(f"    {k:30s} = {v}")
            print()

        # Specifically look for 'alternative' in name
        alt_filters = [sf for sf in all_filters
                       if 'alternative' in str(sf.get('name', '')).lower()]
        if alt_filters:
            print(f"\n  FOUND {len(alt_filters)} filter(s) with 'alternative' in name:")
            for sf in alt_filters:
                print(f"    ID={sf['id']}, name={sf['name']}")
        else:
            print(f"\n  NO filters found with 'alternative' in name.")
            print(f"  Searching by model_name='product.product'...")
            pp_filters = [sf for sf in all_filters
                          if sf.get('model_name') == 'product.product']
            if pp_filters:
                print(f"  Found {len(pp_filters)} filter(s) with model_name='product.product':")
                for sf in pp_filters:
                    print(f"    ID={sf['id']}, name={sf['name']}")
            else:
                print(f"  NO filters with model_name='product.product' either.")

except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 2. CHECK IF oe_structure WAS OVERRIDDEN (user-saved views)
# ============================================================================
print("\n" + "=" * 80)
print("2. CHECK IF oe_structure WAS OVERRIDDEN (user-saved blocks)")
print("=" * 80)

# Search for views related to the oe_structure block for recommended products
oe_patterns = [
    'oe_structure_website_sale_recommended',
    'oe_structure_website_sale',
]

for pattern in oe_patterns:
    print(f"\n  --- Searching key ILIKE '{pattern}' ---")
    try:
        oe_views = execute('ir.ui.view', 'search_read',
                           [['key', 'ilike', pattern]],
                           ['id', 'key', 'active', 'arch_db', 'website_id',
                            'inherit_id', 'name', 'type'],
                           order='key')
        if oe_views:
            print(f"  Found {len(oe_views)} views:")
            for v in oe_views:
                print(f"\n    === View ID: {v['id']} ===")
                print(f"    key:        {v.get('key')}")
                print(f"    name:       {v.get('name')}")
                print(f"    active:     {v.get('active')}")
                print(f"    type:       {v.get('type')}")
                print(f"    website_id: {v.get('website_id')}")
                print(f"    inherit_id: {v.get('inherit_id')}")
                arch = v.get('arch_db', '')
                if arch:
                    print(f"    arch_db (FULL):")
                    for line in str(arch).split('\n'):
                        print(f"      {line}")
                else:
                    print(f"    arch_db: (empty)")
        else:
            print(f"  No views found.")
    except Exception as e:
        print(f"  ERROR: {e}")

# Also search for oe_structure with 'product' in the key
print(f"\n  --- Searching key ILIKE 'oe_structure%product' ---")
try:
    oe_prod_views = execute('ir.ui.view', 'search_read',
                            [['key', 'ilike', 'oe_structure'],
                             ['key', 'ilike', 'product']],
                            ['id', 'key', 'active', 'arch_db', 'website_id',
                             'name'],
                            order='key')
    if oe_prod_views:
        print(f"  Found {len(oe_prod_views)} views:")
        for v in oe_prod_views:
            print(f"\n    [{v['id']}] key={v.get('key')}")
            print(f"    name={v.get('name')} active={v.get('active')} "
                  f"website_id={v.get('website_id')}")
            arch = v.get('arch_db', '')
            if arch:
                print(f"    arch_db (FULL):")
                for line in str(arch).split('\n'):
                    print(f"      {line}")
    else:
        print(f"  No views found.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 3. CHECK FOR COW (Copy on Write) VIEWS inheriting from alternative_products
# ============================================================================
print("\n" + "=" * 80)
print("3. COW (Copy on Write) VIEWS inheriting from alternative_products (id=3376)")
print("=" * 80)

try:
    cow_views = execute('ir.ui.view', 'search_read',
                        [['inherit_id', '=', 3376]],
                        ['id', 'key', 'active', 'arch_db', 'website_id',
                         'name', 'type', 'customize_show', 'priority'],
                        order='id')
    if cow_views:
        print(f"\n  Found {len(cow_views)} views inheriting from id=3376:")
        for v in cow_views:
            print(f"\n    === View ID: {v['id']} ===")
            print(f"    key:            {v.get('key')}")
            print(f"    name:           {v.get('name')}")
            print(f"    active:         {v.get('active')}")
            print(f"    type:           {v.get('type')}")
            print(f"    website_id:     {v.get('website_id')}")
            print(f"    customize_show: {v.get('customize_show')}")
            print(f"    priority:       {v.get('priority')}")
            arch = v.get('arch_db', '')
            if arch:
                print(f"    arch_db (FULL):")
                for line in str(arch).split('\n'):
                    print(f"      {line}")
    else:
        print(f"\n  No COW views found inheriting from id=3376.")
except Exception as e:
    print(f"  ERROR: {e}")

# Also check if there's a COW copy OF 3376 itself (different id, same key)
print(f"\n  --- Checking for COW copies of 3376 (same key, different ID) ---")
try:
    same_key_views = execute('ir.ui.view', 'search_read',
                             [['key', '=', 'website_sale.alternative_products']],
                             ['id', 'key', 'active', 'website_id', 'name',
                              'inherit_id', 'arch_db'],
                             order='id')
    print(f"  Found {len(same_key_views)} views with key='website_sale.alternative_products':")
    for v in same_key_views:
        inherit = f" inherit_id={v['inherit_id'][0]}({v['inherit_id'][1]})" if v.get('inherit_id') else ""
        print(f"    [{v['id']}] active={v['active']} website_id={v.get('website_id')}{inherit}")
        arch = v.get('arch_db', '')
        if arch:
            print(f"    arch_db (FULL):")
            for line in str(arch).split('\n'):
                print(f"      {line}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 4. CHECK PRODUCT DATA AND TRY CALLING THE FILTER METHOD
# ============================================================================
print("\n" + "=" * 80)
print("4. PRODUCT DATA AND FILTER METHOD CHECK")
print("=" * 80)

# Read product 144's alternative_product_ids
print("\n  --- Product ID 144 (Machupicchu) ---")
try:
    result = execute('product.template', 'read', [144],
                     ['name', 'alternative_product_ids', 'product_variant_ids',
                      'is_published'])
    if result:
        p = result[0]
        print(f"  Name:                    {p['name']}")
        print(f"  is_published:            {p.get('is_published')}")
        print(f"  alternative_product_ids: {p.get('alternative_product_ids')} "
              f"({len(p.get('alternative_product_ids', []))} items)")
        print(f"  product_variant_ids:     {p.get('product_variant_ids')}")

        # Read variant details
        variant_ids = p.get('product_variant_ids', [])
        if variant_ids:
            print(f"\n  Variant ID(s): {variant_ids}")
            variant = execute('product.product', 'read', [variant_ids[0]],
                              ['name', 'alternative_product_ids', 'product_tmpl_id'])
            if variant:
                vv = variant[0]
                print(f"  Variant [{vv['id']}]: name={vv['name']}")
                print(f"  Variant alternative_product_ids: {vv.get('alternative_product_ids')}")
                print(f"  Variant product_tmpl_id: {vv.get('product_tmpl_id')}")

        # Read the alternative products themselves
        alt_ids = p.get('alternative_product_ids', [])
        if alt_ids:
            alt_prods = execute('product.template', 'read', alt_ids,
                                ['name', 'is_published', 'website_published',
                                 'product_variant_ids'])
            print(f"\n  Alternative products detail:")
            for ap in alt_prods:
                pub = "PUBLISHED" if ap.get('is_published') else "NOT published"
                wpub = "web_published" if ap.get('website_published') else "NOT web_published"
                variants = ap.get('product_variant_ids', [])
                print(f"    [{ap['id']}] {ap['name']} ({pub}, {wpub}) variants={variants}")
except Exception as e:
    print(f"  ERROR: {e}")

# Try calling _get_alternative_product_filter
print("\n  --- Trying to call _get_alternative_product_filter() ---")
try:
    # This is a model method, not a record method, so we try different approaches
    # Approach 1: call on the model directly
    filter_result = models.execute_kw(
        db, uid, password,
        'product.template', '_get_alternative_product_filter', [])
    print(f"  _get_alternative_product_filter() result: {filter_result}")
except Exception as e:
    print(f"  Direct call failed (expected for private method): {e}")

# Try to find the server action that might implement this filter
print("\n  --- Looking for server actions related to 'alternative' ---")
try:
    alt_actions = execute('ir.actions.server', 'search_read',
                          [['name', 'ilike', 'alternative']],
                          ['id', 'name', 'model_name', 'state', 'code'],
                          order='id')
    if alt_actions:
        for a in alt_actions:
            print(f"  [{a['id']}] name={a['name']} model={a.get('model_name')} "
                  f"state={a.get('state')}")
            if a.get('code'):
                print(f"  code:")
                for line in str(a['code']).split('\n'):
                    print(f"    {line}")
    else:
        print(f"  No server actions with 'alternative' in name.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 5. ALL SNIPPET FILTERS WITH model product.product
# ============================================================================
print("\n" + "=" * 80)
print("5. ALL SNIPPET FILTERS WITH model_name = 'product.product'")
print("=" * 80)

try:
    model_exists = execute('ir.model', 'search_count',
                           [['model', '=', 'website.snippet.filter']])
    if model_exists:
        pp_filters = execute('website.snippet.filter', 'search_read',
                             [['model_name', '=', 'product.product']],
                             ['id', 'name', 'action_server_id', 'limit',
                              'website_id'],
                             order='id')
        if pp_filters:
            print(f"\n  Found {len(pp_filters)} filter(s):")
            for sf in pp_filters:
                print(f"    [{sf['id']}] name={sf['name']}")
                print(f"       action_server_id={sf.get('action_server_id')}")
                print(f"       limit={sf.get('limit')}")
                print(f"       website_id={sf.get('website_id')}")
        else:
            print(f"\n  No filters with model_name='product.product'.")

        # Also check product.template
        print(f"\n  --- Also checking model_name='product.template' ---")
        pt_filters = execute('website.snippet.filter', 'search_read',
                             [['model_name', '=', 'product.template']],
                             ['id', 'name', 'action_server_id', 'limit',
                              'website_id'],
                             order='id')
        if pt_filters:
            print(f"  Found {len(pt_filters)} filter(s):")
            for sf in pt_filters:
                print(f"    [{sf['id']}] name={sf['name']}")
                print(f"       action_server_id={sf.get('action_server_id')}")
                print(f"       limit={sf.get('limit')}")
                print(f"       website_id={sf.get('website_id')}")
        else:
            print(f"  No filters with model_name='product.template'.")
    else:
        print(f"\n  Model website.snippet.filter does not exist.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 6. RE-READ THE FULL ARCH of view 3376 and its parent view
# ============================================================================
print("\n" + "=" * 80)
print("6. FULL ARCH OF VIEW 3376 (alternative_products) AND PARENT")
print("=" * 80)

try:
    alt_view = execute('ir.ui.view', 'read', [3376],
                       ['name', 'key', 'active', 'arch_db', 'inherit_id',
                        'website_id', 'customize_show', 'priority', 'type',
                        'mode'])
    if alt_view:
        v = alt_view[0]
        print(f"\n  === View {v['id']}: {v.get('key')} ===")
        print(f"  name:           {v['name']}")
        print(f"  active:         {v['active']}")
        print(f"  type:           {v.get('type')}")
        print(f"  mode:           {v.get('mode')}")
        print(f"  website_id:     {v.get('website_id')}")
        print(f"  customize_show: {v.get('customize_show')}")
        print(f"  priority:       {v.get('priority')}")
        print(f"  inherit_id:     {v.get('inherit_id')}")

        arch = v.get('arch_db', '')
        if arch:
            print(f"\n  arch_db (FULL):")
            for line in str(arch).split('\n'):
                print(f"    {line}")

        # Read parent view arch too
        parent_id = v.get('inherit_id')
        if parent_id:
            parent_view_id = parent_id[0]
            print(f"\n  --- Parent view (id={parent_view_id}) ---")
            parent = execute('ir.ui.view', 'read', [parent_view_id],
                             ['name', 'key', 'active', 'arch_db'])
            if parent:
                pv = parent[0]
                print(f"  key:    {pv.get('key')}")
                print(f"  name:   {pv['name']}")
                print(f"  active: {pv['active']}")
                # Show only the section around 'alternative' or 'oe_structure' or 'recommended'
                arch = pv.get('arch_db', '')
                if arch:
                    lines = str(arch).split('\n')
                    print(f"  arch_db ({len(lines)} lines total):")
                    # Show lines containing relevant keywords
                    relevant_keywords = ['alternative', 'oe_structure', 'recommend',
                                         'snippet', 'carousel', 'dynamic_snippet',
                                         'data-filter', 'optional']
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        if any(kw in line_lower for kw in relevant_keywords):
                            # Show context: 2 lines before, the match, 2 lines after
                            start = max(0, i - 2)
                            end = min(len(lines), i + 3)
                            for j in range(start, end):
                                marker = " >>>" if j == i else "    "
                                print(f"  {marker} L{j}: {lines[j]}")
                            print()
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 7. SEARCH FOR ANY VIEW CONTAINING 'data-filter' or 'dynamic_snippet'
# ============================================================================
print("\n" + "=" * 80)
print("7. VIEWS CONTAINING 'data-filter' OR 'dynamic_snippet' IN ARCH")
print("=" * 80)

for search_term in ['data-filter-id', 'dynamic_snippet', 'data_filter_id',
                     'snippet_filter']:
    print(f"\n  --- arch_db ILIKE '%{search_term}%' ---")
    try:
        dyn_views = execute('ir.ui.view', 'search_read',
                            [['arch_db', 'ilike', search_term]],
                            ['id', 'name', 'key', 'active', 'website_id'],
                            limit=30, order='key')
        if dyn_views:
            print(f"  Found {len(dyn_views)} views:")
            for v in dyn_views:
                website = f" [website={v['website_id'][0]}]" if v.get('website_id') else ""
                active = "ACTIVE" if v['active'] else "INACTIVE"
                print(f"    [{v['id']:5d}] {active:8s} key={v.get('key', 'N/A')}{website}")
                print(f"            name={v['name']}")
        else:
            print(f"  No views found.")
    except Exception as e:
        print(f"  ERROR: {e}")


# ============================================================================
# 8. CHECK ALL oe_structure VIEWS (user-saved page content blocks)
# ============================================================================
print("\n" + "=" * 80)
print("8. ALL oe_structure VIEWS (user-saved content blocks)")
print("=" * 80)

try:
    oe_views = execute('ir.ui.view', 'search_read',
                       [['key', 'ilike', 'oe_structure']],
                       ['id', 'key', 'active', 'website_id', 'name',
                        'inherit_id'],
                       order='key')
    if oe_views:
        print(f"\n  Found {len(oe_views)} oe_structure views:")
        for v in oe_views:
            inherit = f" inherit={v['inherit_id'][1]}" if v.get('inherit_id') else ""
            website = f" [website={v['website_id'][0]}]" if v.get('website_id') else ""
            active = "ACTIVE" if v['active'] else "INACTIVE"
            print(f"    [{v['id']:5d}] {active:8s} key={v.get('key')}{website}{inherit}")

        # Now for any that look product-page related, dump full arch
        product_oe = [v for v in oe_views
                      if 'product' in str(v.get('key', '')).lower()
                      or 'sale' in str(v.get('key', '')).lower()]
        if product_oe:
            print(f"\n  --- Product/sale related oe_structure views (full arch): ---")
            for v in product_oe:
                full = execute('ir.ui.view', 'read', [v['id']], ['arch_db'])
                if full:
                    print(f"\n    === [{v['id']}] key={v.get('key')} ===")
                    arch = full[0].get('arch_db', '')
                    for line in str(arch).split('\n'):
                        print(f"      {line}")
    else:
        print(f"\n  No oe_structure views found.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 9. CHECK VIEWS WITH key CONTAINING 'recommended' OR 'carousel'
# ============================================================================
print("\n" + "=" * 80)
print("9. VIEWS WITH 'recommended' OR 'carousel' IN KEY/NAME/ARCH")
print("=" * 80)

for kw in ['recommended', 'carousel', 'cross_selling']:
    print(f"\n  --- Keyword: '{kw}' ---")
    try:
        views = execute('ir.ui.view', 'search_read',
                        ['|', '|',
                         ['key', 'ilike', kw],
                         ['name', 'ilike', kw],
                         ['arch_db', 'ilike', kw]],
                        ['id', 'name', 'key', 'active', 'website_id',
                         'inherit_id', 'arch_db'],
                        limit=20, order='key')
        if views:
            print(f"  Found {len(views)} views:")
            for v in views:
                inherit = f" inherit={v['inherit_id'][1]}" if v.get('inherit_id') else ""
                website = f" [website={v['website_id'][0]}]" if v.get('website_id') else ""
                active = "ACTIVE" if v['active'] else "INACTIVE"
                print(f"    [{v['id']:5d}] {active:8s} key={v.get('key', 'N/A')}{website}{inherit}")
                print(f"            name={v['name']}")
                # Show arch excerpt (first 500 chars)
                arch = v.get('arch_db', '')
                if arch and kw in str(arch).lower():
                    # Show lines containing the keyword
                    lines = str(arch).split('\n')
                    for i, line in enumerate(lines):
                        if kw in line.lower():
                            print(f"            L{i}: {line.strip()[:200]}")
        else:
            print(f"  No views found.")
    except Exception as e:
        print(f"  ERROR: {e}")


# ============================================================================
# 10. CHECK THE PRODUCT PAGE RENDERING CONTEXT
# ============================================================================
print("\n" + "=" * 80)
print("10. PRODUCT PAGE RENDERING - Check view 3362 (website_sale.product) arch")
print("=" * 80)

try:
    pv = execute('ir.ui.view', 'read', [3362],
                 ['name', 'key', 'active', 'arch_db'])
    if pv:
        arch = pv[0].get('arch_db', '')
        lines = str(arch).split('\n')
        print(f"\n  View 3362: key={pv[0].get('key')} active={pv[0]['active']}")
        print(f"  Total lines: {len(lines)}")

        # Show lines containing: alternative, oe_structure, recommended,
        # snippet, carousel, suggested
        keywords = ['alternative', 'oe_structure', 'recommend', 'snippet',
                    'carousel', 'suggested', 'accessory', 'optional',
                    'cross_sell']
        print(f"\n  Lines containing relevant keywords:")
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                # Show context
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                for j in range(start, end):
                    marker = " >>>" if j == i else "    "
                    print(f"  {marker} L{j}: {lines[j]}")
                print()

        # Also dump the LAST 50 lines which likely contain the bottom sections
        print(f"\n  --- Last 50 lines of arch (product page bottom sections) ---")
        for i in range(max(0, len(lines) - 50), len(lines)):
            print(f"    L{i}: {lines[i]}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 11. CHECK THE website_sale.product_item VIEW (used by carousels)
# ============================================================================
print("\n" + "=" * 80)
print("11. CHECK website_sale.product_item VIEW")
print("=" * 80)

try:
    pi_views = execute('ir.ui.view', 'search_read',
                       [['key', 'ilike', 'website_sale.product_item']],
                       ['id', 'key', 'active', 'name', 'arch_db'],
                       order='key')
    if pi_views:
        for v in pi_views:
            print(f"\n  [{v['id']}] key={v.get('key')} active={v['active']}")
            print(f"  name={v['name']}")
            arch = v.get('arch_db', '')
            if arch:
                print(f"  arch_db (first 1000 chars):")
                print(f"    {str(arch)[:1000]}")
    else:
        print(f"  Not found.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 12. DIAGNOSIS SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("12. DIAGNOSIS SUMMARY")
print("=" * 80)

print("""
INVESTIGATION FOCUSES:

1. SNIPPET FILTERS:
   The alternative products carousel in Odoo 19 uses a "dynamic snippet"
   mechanism. The arch of view 3376 contains:
     <div data-snippet="s_dynamic_snippet_products"
          data-filter-id="..."
          .../>
   This filter-id points to a website.snippet.filter record that defines
   how to fetch the alternative products dynamically.

2. OE_STRUCTURE OVERRIDE:
   When a user edits the product page in the website editor and saves,
   Odoo creates an oe_structure view that can REPLACE the original
   content of an <section class="oe_structure"> block. If someone
   saved an empty block or a different block where the carousel was,
   it would override the alternative products section.

3. COW VIEWS:
   In multi-website setups, Odoo creates Copy-on-Write variants of views
   for specific websites. A COW copy with active=False or different
   content could hide the carousel on a specific website.

4. FILTER METHOD:
   product.template._get_alternative_product_filter() returns the
   snippet filter ID. If this filter doesn't exist or is misconfigured,
   the carousel has no data source.

CHECK THE OUTPUT ABOVE TO IDENTIFY THE ROOT CAUSE.
""")

print("=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
