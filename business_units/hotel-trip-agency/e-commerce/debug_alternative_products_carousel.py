#!/usr/bin/env python3
"""
Debug why the "Alternative Products" carousel is NOT showing on ecommerce
product pages, even though alternative_product_ids has been set on products.

Target: PRODUCTION instance (machupicchu-afdestiny-production)

Checks:
1. Verify alternative_product_ids data is saved on a sample product
2. Read the QWeb view website_sale.alternative_products (arch, active, customize_show)
3. Check if the view is a customization toggle
4. Search for ALL views related to alternative/optional/accessory products
5. Check website record for relevant settings
6. Check res.config.settings for product recommendation toggles
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
# 1. VERIFY alternative_product_ids DATA IS SAVED
# ============================================================================
print("\n" + "=" * 80)
print("1. VERIFY alternative_product_ids DATA IS SAVED")
print("=" * 80)

# Check Machupicchu (ID 144) as the sample
print("\n--- Product ID 144 (Machupicchu) ---")
try:
    mp = execute('product.template', 'read', [144],
                 ['name', 'alternative_product_ids', 'optional_product_ids',
                  'accessory_product_ids', 'is_published', 'website_published',
                  'sale_ok', 'type'])
    if mp:
        p = mp[0]
        print(f"  Name:                    {p['name']}")
        print(f"  type:                    {p['type']}")
        print(f"  is_published:            {p.get('is_published')}")
        print(f"  website_published:       {p.get('website_published')}")
        print(f"  sale_ok:                 {p.get('sale_ok')}")
        print(f"  alternative_product_ids: {p.get('alternative_product_ids')} "
              f"({len(p.get('alternative_product_ids', []))} items)")
        print(f"  optional_product_ids:    {p.get('optional_product_ids')} "
              f"({len(p.get('optional_product_ids', []))} items)")
        print(f"  accessory_product_ids:   {p.get('accessory_product_ids')} "
              f"({len(p.get('accessory_product_ids', []))} items)")

        # Resolve alternative product names
        alt_ids = p.get('alternative_product_ids', [])
        if alt_ids:
            alt_prods = execute('product.template', 'read', alt_ids,
                                ['name', 'is_published'])
            print(f"\n  Alternative products detail:")
            for ap in alt_prods:
                pub = "PUBLISHED" if ap.get('is_published') else "NOT published"
                print(f"    [{ap['id']}] {ap['name']} ({pub})")
        else:
            print(f"\n  WARNING: alternative_product_ids is EMPTY!")
except Exception as e:
    print(f"  ERROR: {e}")

# Count how many published products have alternative_product_ids set
print("\n--- Population counts across all published products ---")
try:
    total_published = execute('product.template', 'search_count',
                              [['is_published', '=', True]])
    with_alt = execute('product.template', 'search_count',
                       [['alternative_product_ids', '!=', False],
                        ['is_published', '=', True]])
    with_opt = execute('product.template', 'search_count',
                       [['optional_product_ids', '!=', False],
                        ['is_published', '=', True]])
    with_acc = execute('product.template', 'search_count',
                       [['accessory_product_ids', '!=', False],
                        ['is_published', '=', True]])
    print(f"  Total published products:                        {total_published}")
    print(f"  With alternative_product_ids (carousel):         {with_alt}")
    print(f"  With optional_product_ids (add-to-cart dialog):  {with_opt}")
    print(f"  With accessory_product_ids (cart suggestions):   {with_acc}")
except Exception as e:
    print(f"  ERROR: {e}")

# Also check a few more products
print("\n--- First 5 published products with alternative_product_ids ---")
try:
    sample = execute('product.template', 'search_read',
                     [['alternative_product_ids', '!=', False],
                      ['is_published', '=', True]],
                     ['name', 'alternative_product_ids'],
                     limit=5, order='id asc')
    for s in sample:
        print(f"  [{s['id']}] {s['name']} -> {len(s['alternative_product_ids'])} alternatives")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 2. CHECK THE QWEB VIEW: website_sale.alternative_products
# ============================================================================
print("\n" + "=" * 80)
print("2. CHECK THE QWEB VIEW: website_sale.alternative_products")
print("=" * 80)

# Get all available fields on ir.ui.view first
view_fields_info = execute('ir.ui.view', 'fields_get', [],
                           attributes=['string', 'type'])
all_view_field_names = list(view_fields_info.keys())

# Fields we want to read
desired_fields = ['id', 'name', 'key', 'active', 'website_id', 'arch_db',
                  'customize_show', 'type', 'priority', 'inherit_id', 'mode',
                  'visibility']
# Filter to only fields that actually exist
read_fields = [f for f in desired_fields if f in all_view_field_names]
missing_fields = [f for f in desired_fields if f not in all_view_field_names]
if missing_fields:
    print(f"  NOTE: These fields do NOT exist on ir.ui.view: {missing_fields}")

# Also check for website_published
if 'website_published' in all_view_field_names:
    read_fields.append('website_published')
    print(f"  website_published field EXISTS on ir.ui.view")
else:
    print(f"  website_published field does NOT exist on ir.ui.view")

# Search by key
alt_views = execute('ir.ui.view', 'search_read',
                    [['key', '=', 'website_sale.alternative_products']],
                    read_fields)

if not alt_views:
    print("\n  NOT FOUND by key! Trying name search...")
    alt_views = execute('ir.ui.view', 'search_read',
                        [['name', 'ilike', 'alternative_products']],
                        read_fields)

if not alt_views:
    print("  NOT FOUND by name either! Trying arch_db search...")
    alt_views = execute('ir.ui.view', 'search_read',
                        [['arch_db', 'ilike', 'alternative_product']],
                        read_fields, limit=10)

if alt_views:
    for v in alt_views:
        print(f"\n  === View ID: {v['id']} ===")
        for field in read_fields:
            if field == 'arch_db':
                arch = v.get('arch_db', '')
                print(f"  {field}:")
                if arch:
                    for line in str(arch).split('\n'):
                        print(f"    {line}")
                else:
                    print(f"    (empty)")
            elif field == 'inherit_id' and v.get(field):
                print(f"  {field}: {v[field][0]} ({v[field][1]})")
            elif field == 'website_id' and v.get(field):
                print(f"  {field}: {v[field][0]} ({v[field][1]})")
            else:
                print(f"  {field}: {v.get(field)}")
else:
    print("\n  NO VIEW FOUND matching 'alternative_products'!")
    print("  This could mean the template doesn't exist or uses a different key.")


# ============================================================================
# 3. CHECK IF THE VIEW IS A CUSTOMIZATION TOGGLE
# ============================================================================
print("\n" + "=" * 80)
print("3. CHECK IF THE VIEW IS A CUSTOMIZATION TOGGLE")
print("=" * 80)

if alt_views:
    v = alt_views[0]
    customize = v.get('customize_show', 'N/A')
    active = v.get('active', 'N/A')
    visibility = v.get('visibility', 'N/A')

    print(f"  View ID:        {v['id']}")
    print(f"  active:         {active}")
    print(f"  customize_show: {customize}")
    print(f"  visibility:     {visibility}")
    print(f"  mode:           {v.get('mode', 'N/A')}")
    print(f"  inherit_id:     {v.get('inherit_id', 'N/A')}")

    if customize:
        print(f"\n  This IS a customization toggle view.")
        print(f"  In Odoo 19, customize_show=True means this view appears as")
        print(f"  a toggle option in 'Customize' menu when editing the page.")
        if not active:
            print(f"\n  >>> DIAGNOSIS: View is INACTIVE (active=False)!")
            print(f"  >>> This means the customization toggle is OFF.")
            print(f"  >>> To fix: activate it in Website > Customize menu,")
            print(f"  >>> or set active=True via XML-RPC.")
    else:
        print(f"\n  This is NOT a customization toggle (customize_show=False).")
        print(f"  The view should always render when its parent renders.")
else:
    print("  Skipped: no view found in step 2.")


# ============================================================================
# 4. SEARCH FOR ALL RELATED VIEWS
# ============================================================================
print("\n" + "=" * 80)
print("4. SEARCH FOR ALL VIEWS RELATED TO ALTERNATIVE/OPTIONAL/ACCESSORY PRODUCTS")
print("=" * 80)

search_keywords = ['alternative', 'optional', 'accessory', 'cross_sell',
                    'upsell', 'suggested', 'recommend']

all_related_views = []

for kw in search_keywords:
    views = execute('ir.ui.view', 'search_read',
                    ['|',
                     ['key', 'ilike', kw],
                     ['name', 'ilike', kw]],
                    ['id', 'name', 'key', 'active', 'type', 'inherit_id',
                     'customize_show', 'website_id', 'priority'],
                    order='key')
    if views:
        print(f"\n  --- Keyword: '{kw}' ({len(views)} views) ---")
        for v in views:
            inherit = f" inherits={v['inherit_id'][1]}" if v.get('inherit_id') else ""
            website = f" website={v['website_id'][0]}" if v.get('website_id') else ""
            active_str = "ACTIVE" if v['active'] else "INACTIVE"
            custom = " [CUSTOMIZE]" if v.get('customize_show') else ""
            print(f"    [{v['id']:5d}] {active_str:8s}{custom}")
            print(f"           key={v.get('key', 'N/A')}")
            print(f"           name={v['name']}{inherit}{website}")
            all_related_views.append(v)

# Also search views with key containing "website_sale.product" to catch product
# page layout views
print(f"\n  --- Views with key matching 'website_sale.product' ---")
product_page_views = execute('ir.ui.view', 'search_read',
                             [['key', 'ilike', 'website_sale.product']],
                             ['id', 'name', 'key', 'active', 'type',
                              'inherit_id', 'customize_show', 'priority'],
                             order='key')
print(f"  Found {len(product_page_views)} views:")
for v in product_page_views:
    inherit = f" inherits={v['inherit_id'][1]}" if v.get('inherit_id') else ""
    active_str = "ACTIVE" if v['active'] else "INACTIVE"
    custom = " [CUSTOMIZE]" if v.get('customize_show') else ""
    print(f"    [{v['id']:5d}] {active_str:8s}{custom} p={v['priority']:3d} "
          f"key={v.get('key', 'N/A')}")
    print(f"           name={v['name']}{inherit}")

# Check INACTIVE views in website_sale namespace
print(f"\n  --- INACTIVE views in website_sale namespace ---")
inactive_views = execute('ir.ui.view', 'search_read',
                         [['key', 'ilike', 'website_sale'],
                          ['active', '=', False]],
                         ['id', 'name', 'key', 'customize_show'],
                         order='key')
print(f"  Found {len(inactive_views)} inactive website_sale views:")
for v in inactive_views:
    custom = " [CUSTOMIZE TOGGLE]" if v.get('customize_show') else ""
    print(f"    [{v['id']:5d}] key={v.get('key', 'N/A'):65s}{custom}")
    print(f"           name={v['name']}")


# ============================================================================
# 5. CHECK WEBSITE SETTINGS
# ============================================================================
print("\n" + "=" * 80)
print("5. CHECK WEBSITE SETTINGS (website record id=1)")
print("=" * 80)

# Search for relevant fields on the website model
field_keywords = ['product', 'alternative', 'optional', 'accessory',
                  'recommend', 'cross', 'upsell', 'carousel',
                  'add_to_cart', 'ecommerce']

website_fields = execute('ir.model.fields', 'search_read',
                         [['model', '=', 'website']],
                         ['name', 'field_description', 'ttype', 'store'],
                         order='name')

matched_fields = []
for f in website_fields:
    name_lower = f['name'].lower()
    desc_lower = f['field_description'].lower()
    for kw in field_keywords:
        if kw in name_lower or kw in desc_lower:
            matched_fields.append(f)
            break

print(f"\n  Matching fields on 'website' model ({len(matched_fields)} of {len(website_fields)} total):")
for f in matched_fields:
    print(f"    {f['name']:50s} ({f['ttype']:10s}) - {f['field_description']}")

# Read the website record with those fields + basic fields
if matched_fields:
    field_names = [f['name'] for f in matched_fields]
    field_names.extend(['name', 'domain'])
    field_names = list(set(field_names))

    print(f"\n  --- Website record id=1 values ---")
    try:
        website = execute('website', 'read', [1], field_names)
        if website:
            for key, val in sorted(website[0].items()):
                if key != 'id':
                    print(f"    {key:50s} = {val}")
    except Exception as e:
        print(f"    ERROR: {e}")


# ============================================================================
# 6. CHECK res.config.settings
# ============================================================================
print("\n" + "=" * 80)
print("6. CHECK res.config.settings FOR PRODUCT RECOMMENDATION SETTINGS")
print("=" * 80)

settings_keywords = ['optional', 'alternative', 'accessory', 'cross', 'upsell',
                      'product_page', 'ecommerce', 'website_sale',
                      'group_product', 'module_website', 'carousel',
                      'recommend', 'suggest']

settings_fields = execute('ir.model.fields', 'search_read',
                          [['model', '=', 'res.config.settings']],
                          ['name', 'field_description', 'ttype', 'store'],
                          order='name')

matched_settings = []
for f in settings_fields:
    name_lower = f['name'].lower()
    desc_lower = f['field_description'].lower()
    for kw in settings_keywords:
        if kw in name_lower or kw in desc_lower:
            matched_settings.append(f)
            break

print(f"\n  Matching fields on 'res.config.settings' ({len(matched_settings)}):")
for f in matched_settings:
    print(f"    {f['name']:60s} ({f['ttype']:10s}) - {f['field_description']}")

# Read the latest settings record
print(f"\n  --- Latest res.config.settings values ---")
try:
    latest_ids = execute('res.config.settings', 'search', [],
                         limit=1, order='id desc')
    if latest_ids:
        settings_field_names = [f['name'] for f in matched_settings]
        settings_data = execute('res.config.settings', 'read',
                                latest_ids, settings_field_names)
        if settings_data:
            print(f"  Settings record id={settings_data[0]['id']}:")
            for key, val in sorted(settings_data[0].items()):
                if key != 'id':
                    print(f"    {key:60s} = {val}")
    else:
        print(f"  No res.config.settings records found.")
except Exception as e:
    print(f"  ERROR reading settings: {e}")


# ============================================================================
# 7. EXTRA: Check the product page parent view and its children
# ============================================================================
print("\n" + "=" * 80)
print("7. PRODUCT PAGE VIEW HIERARCHY")
print("=" * 80)

# Find the main product page view
print("\n--- Main product page view: website_sale.product ---")
product_view = execute('ir.ui.view', 'search_read',
                       [['key', '=', 'website_sale.product']],
                       ['id', 'name', 'key', 'active', 'type'],
                       limit=1)
if product_view:
    pv = product_view[0]
    print(f"  ID: {pv['id']}")
    print(f"  Name: {pv['name']}")
    print(f"  Active: {pv['active']}")

    # List ALL views that inherit from this product page view
    print(f"\n--- All views inheriting from website_sale.product (id={pv['id']}) ---")
    children = execute('ir.ui.view', 'search_read',
                       [['inherit_id', '=', pv['id']]],
                       ['id', 'name', 'key', 'active', 'customize_show',
                        'priority'],
                       order='priority')
    print(f"  Found {len(children)} child views:")
    for c in children:
        active_str = "ACTIVE" if c['active'] else "INACTIVE"
        custom = " [CUSTOMIZE]" if c.get('customize_show') else ""
        print(f"    [{c['id']:5d}] {active_str:8s}{custom} p={c['priority']:3d} "
              f"key={c.get('key', 'N/A')}")
        print(f"           name={c['name']}")
else:
    print("  NOT FOUND!")


# ============================================================================
# 8. EXTRA: Read arch_db of the alternative_products view to see the template
# ============================================================================
print("\n" + "=" * 80)
print("8. ARCH INSPECTION: ALTERNATIVE PRODUCTS + RELATED VIEWS")
print("=" * 80)

# Read arch of all views whose key contains 'alternative'
alt_arch_views = execute('ir.ui.view', 'search_read',
                         [['key', 'ilike', 'alternative']],
                         ['id', 'name', 'key', 'active', 'arch_db',
                          'customize_show', 'inherit_id'],
                         order='key')

if alt_arch_views:
    for v in alt_arch_views:
        print(f"\n  === [{v['id']}] key={v.get('key')} ===")
        print(f"  name={v['name']}")
        print(f"  active={v['active']}")
        print(f"  customize_show={v.get('customize_show')}")
        print(f"  inherit_id={v.get('inherit_id')}")
        arch = v.get('arch_db', '')
        if arch:
            print(f"  arch_db:")
            for line in str(arch).split('\n'):
                print(f"    {line}")
        else:
            print(f"  arch_db: (empty)")
else:
    print("  No views with 'alternative' in key found.")

# Also check for "suggested_products" views
print(f"\n  --- Views with 'suggested' in key ---")
sug_views = execute('ir.ui.view', 'search_read',
                    [['key', 'ilike', 'suggested']],
                    ['id', 'name', 'key', 'active', 'arch_db',
                     'customize_show', 'inherit_id'],
                    order='key')
if sug_views:
    for v in sug_views:
        print(f"\n  === [{v['id']}] key={v.get('key')} ===")
        print(f"  name={v['name']}")
        print(f"  active={v['active']}")
        print(f"  customize_show={v.get('customize_show')}")
        arch = v.get('arch_db', '')
        if arch:
            print(f"  arch_db:")
            for line in str(arch).split('\n'):
                print(f"    {line}")
else:
    print("  No views with 'suggested' in key found.")


# ============================================================================
# 9. CHECK INSTALLED MODULES
# ============================================================================
print("\n" + "=" * 80)
print("9. INSTALLED MODULES RELATED TO WEBSITE SALE")
print("=" * 80)

ws_modules = execute('ir.module.module', 'search_read',
                     [['name', 'ilike', 'website_sale'],
                      ['state', '=', 'installed']],
                     ['name', 'shortdesc'],
                     order='name')
print(f"\n  Installed website_sale modules ({len(ws_modules)}):")
for m in ws_modules:
    print(f"    {m['name']:45s} - {m['shortdesc']}")

# Check sale_product_configurator
spc = execute('ir.module.module', 'search_read',
              [['name', '=', 'sale_product_configurator']],
              ['name', 'state', 'shortdesc'])
if spc:
    print(f"\n  sale_product_configurator: state={spc[0]['state']}")
else:
    print(f"\n  sale_product_configurator: NOT FOUND")

# Check website_sale_comparison (sometimes needed for alternative products)
wsc = execute('ir.module.module', 'search_read',
              [['name', 'ilike', 'comparison']],
              ['name', 'state', 'shortdesc'])
if wsc:
    for m in wsc:
        print(f"  {m['name']}: state={m['state']} - {m['shortdesc']}")
else:
    print(f"  No comparison modules found")


# ============================================================================
# 10. SEARCH arch_db FOR t-if CONDITIONS ON alternative
# ============================================================================
print("\n" + "=" * 80)
print("10. SEARCH arch_db FOR t-if CONDITIONS REFERENCING 'alternative'")
print("=" * 80)

try:
    tif_views = execute('ir.ui.view', 'search_read',
                        [['arch_db', 'ilike', 'alternative_product']],
                        ['id', 'name', 'key', 'active', 'arch_db',
                         'customize_show'],
                        limit=20)
    print(f"\n  Views with 'alternative_product' in arch_db: {len(tif_views)}")
    for v in tif_views:
        print(f"\n  [{v['id']}] key={v.get('key')} active={v['active']} "
              f"customize_show={v.get('customize_show')}")
        print(f"  name={v['name']}")
        arch = v.get('arch_db', '')
        if arch:
            # Show just lines containing 'alternative'
            lines = str(arch).split('\n')
            relevant_lines = [(i, l) for i, l in enumerate(lines)
                              if 'alternative' in l.lower()]
            if relevant_lines:
                for i, l in relevant_lines:
                    print(f"    L{i}: {l.strip()}")
            else:
                # Show first 5 lines
                for l in lines[:5]:
                    print(f"    {l}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 11. CHECK add_to_cart_action ON WEBSITE
# ============================================================================
print("\n" + "=" * 80)
print("11. WEBSITE add_to_cart_action SETTING")
print("=" * 80)

try:
    # Check if add_to_cart_action field exists
    atc_field = execute('ir.model.fields', 'search_read',
                        [['model', '=', 'website'],
                         ['name', '=', 'add_to_cart_action']],
                        ['name', 'field_description', 'ttype', 'selection_ids'])
    if atc_field:
        print(f"  Field exists: {atc_field[0]['field_description']} "
              f"(type={atc_field[0]['ttype']})")

        # Read the value
        ws = execute('website', 'read', [1], ['add_to_cart_action'])
        if ws:
            print(f"  Current value: {ws[0].get('add_to_cart_action')}")
            print(f"\n  NOTE: If add_to_cart_action='go_to_cart', the optional")
            print(f"  products dialog is skipped. But this should NOT affect")
            print(f"  alternative_product_ids (carousel on product page).")
    else:
        print(f"  Field 'add_to_cart_action' does NOT exist on website model.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 12. DIAGNOSIS SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("12. DIAGNOSIS SUMMARY")
print("=" * 80)

# Summarize findings
print("""
ANALYSIS OF POSSIBLE ROOT CAUSES:

1. DATA CHECK:
   - If alternative_product_ids is empty on products -> data wasn't saved
   - If populated -> data is OK, problem is in view rendering

2. VIEW ACTIVATION:
   - If website_sale.alternative_products has active=False -> the view is
     disabled as a "Customize" option. Fix: activate it.
   - If customize_show=True -> it's a toggle in Customize menu.
     Go to Website > Edit page > Customize > enable "Alternative Products"

3. VISIBILITY / WEBSITE_ID:
   - If the view has website_id set to a different website -> it won't
     render on your website (id=1)

4. MODULES:
   - website_sale_comparison module sometimes provides the alternative
     products carousel. Check if it's installed.

5. PARENT VIEW:
   - If the parent view is inactive or broken, child views won't render

COMMON FIX IN ODOO 19:
   Go to your product page in the website editor.
   Click "Customize" (paintbrush icon).
   Look for "Alternative Products" toggle and enable it.
   Save the page.
""")

print("=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
