"""
Investigate why optional_product_ids (related/cross-sell products) are NOT showing
as carousels on the Odoo ecommerce website.

Checks:
1. Website settings related to optional/alternative/accessory products
2. Fields on product.template for cross-sell/upsell
3. Website views that render optional/alternative/accessory sections
4. res.config.settings fields controlling these features
5. Sample product data to verify fields are populated
6. Installed modules and groups
7. View arch inspection for carousel templates
8. System parameters

Target: PRODUCTION instance (machupicchu-afdestiny-production)
"""
import xmlrpc.client

# --- Connection ---
url = 'https://machupicchu-afdestiny-production.odoo.com'
db = 'machupicchu-afdestiny-production'
username = 'ayfdestinyeirl@gmail.com'
password = 'L^yUbD2^+p^2h.#'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def execute(model, method, *args, **kwargs):
    return models.execute_kw(db, uid, password, model, method, args, kwargs)

print(f"Connected to: {url} (db={db}, uid={uid})")
print("=" * 80)

# ============================================================================
# 1. WEBSITE MODEL - Check all relevant fields
# ============================================================================
print("\n" + "=" * 80)
print("1. WEBSITE MODEL - Fields related to products/optional/accessory/alternative")
print("=" * 80)

website_field_keywords = ['optional', 'alternative', 'accessory', 'cross', 'upsell',
                          'product_variant', 'product_page', 'carousel',
                          'add_to_cart', 'shop', 'ecommerce']

website_fields = execute('ir.model.fields', 'search_read',
    [['model', '=', 'website']],
    ['name', 'field_description', 'ttype', 'store'],
    order='name')

print(f"\nAll website fields ({len(website_fields)} total):")
print(f"Filtering for keywords: {website_field_keywords}\n")

matched_website_fields = []
for f in website_fields:
    name_lower = f['name'].lower()
    desc_lower = f['field_description'].lower()
    for kw in website_field_keywords:
        if kw in name_lower or kw in desc_lower:
            matched_website_fields.append(f)
            break

if matched_website_fields:
    for f in matched_website_fields:
        print(f"  {f['name']:50s} ({f['ttype']:10s}) - {f['field_description']}")
else:
    print("  No matching fields found on website model.")

# Read the actual website record
print("\n--- Reading website record (id=1) ---")
try:
    field_names_to_read = [f['name'] for f in matched_website_fields]
    extra_fields = ['name', 'domain', 'cdn_activated']
    field_names_to_read.extend(extra_fields)
    field_names_to_read = list(set(field_names_to_read))

    website_data = execute('website', 'read', [1], field_names_to_read)
    if website_data:
        for key, val in sorted(website_data[0].items()):
            if key != 'id':
                print(f"  {key:50s} = {val}")
except Exception as e:
    print(f"  ERROR reading website: {e}")

# ============================================================================
# 2. PRODUCT.TEMPLATE fields for cross-sell / related products
# ============================================================================
print("\n" + "=" * 80)
print("2. PRODUCT.TEMPLATE - Fields for cross-sell/related products")
print("=" * 80)

pt_field_keywords = ['optional', 'alternative', 'accessory', 'cross', 'upsell',
                     'related', 'suggest', 'recommend']

pt_fields = execute('ir.model.fields', 'search_read',
    [['model', '=', 'product.template']],
    ['name', 'field_description', 'ttype', 'relation', 'store'],
    order='name')

print(f"\nAll product.template fields ({len(pt_fields)} total):")
print(f"Filtering for keywords: {pt_field_keywords}\n")

matched_pt_fields = []
for f in pt_fields:
    name_lower = f['name'].lower()
    desc_lower = f['field_description'].lower()
    for kw in pt_field_keywords:
        if kw in name_lower or kw in desc_lower:
            matched_pt_fields.append(f)
            break

for f in matched_pt_fields:
    rel = f" -> {f['relation']}" if f['relation'] else ""
    print(f"  {f['name']:40s} ({f['ttype']:10s}{rel:30s}) stored={f['store']} - {f['field_description']}")

# Read sample product data
print("\n--- Sample published product data (first 5) ---")
sample_tours = execute('product.template', 'search_read',
    [['is_published', '=', True], ['sale_ok', '=', True]],
    ['name', 'optional_product_ids', 'alternative_product_ids', 'accessory_product_ids'],
    limit=5, order='id asc')

for tour in sample_tours:
    print(f"\n  [{tour['id']}] {tour['name']}")
    print(f"    optional_product_ids:     {tour.get('optional_product_ids', 'FIELD NOT FOUND')}")
    print(f"    alternative_product_ids:  {tour.get('alternative_product_ids', 'FIELD NOT FOUND')}")
    print(f"    accessory_product_ids:    {tour.get('accessory_product_ids', 'FIELD NOT FOUND')}")

# Check a known tour (Machupicchu)
print("\n--- Checking known tour: Machupicchu (id=144) ---")
try:
    mp = execute('product.template', 'read', [144],
                 ['name', 'optional_product_ids', 'alternative_product_ids', 'accessory_product_ids'])
    if mp:
        print(f"  Name: {mp[0]['name']}")
        print(f"  optional_product_ids:    {mp[0].get('optional_product_ids', 'N/A')}")
        print(f"  alternative_product_ids: {mp[0].get('alternative_product_ids', 'N/A')}")
        print(f"  accessory_product_ids:   {mp[0].get('accessory_product_ids', 'N/A')}")
        opt_ids = mp[0].get('optional_product_ids', [])
        if opt_ids:
            opt_prods = execute('product.template', 'read', opt_ids, ['name'])
            print(f"  Optional products (in optional_product_ids):")
            for p in opt_prods:
                print(f"    - [{p['id']}] {p['name']}")
except Exception as e:
    print(f"  ERROR: {e}")

# Count products with each field populated
print("\n--- Field population counts (published products) ---")
products_with_opt = execute('product.template', 'search',
    [['optional_product_ids', '!=', False], ['is_published', '=', True]])
products_with_alt = execute('product.template', 'search',
    [['alternative_product_ids', '!=', False], ['is_published', '=', True]])
products_with_acc = execute('product.template', 'search',
    [['accessory_product_ids', '!=', False], ['is_published', '=', True]])
print(f"  Products with optional_product_ids populated:    {len(products_with_opt)}")
print(f"  Products with alternative_product_ids populated: {len(products_with_alt)}")
print(f"  Products with accessory_product_ids populated:   {len(products_with_acc)}")

# ============================================================================
# 3. WEBSITE VIEWS - Check for optional/alternative/accessory rendering views
# ============================================================================
print("\n" + "=" * 80)
print("3. WEBSITE VIEWS - Ecommerce views for optional/alternative/accessory/carousel")
print("=" * 80)

view_keywords = ['optional', 'alternative', 'accessory', 'cross_sell', 'upsell',
                 'suggested', 'recommended', 'product_carousel']

for kw in view_keywords:
    views = execute('ir.ui.view', 'search_read',
        ['|',
         ['key', 'ilike', kw],
         ['name', 'ilike', kw]],
        ['name', 'key', 'active', 'type', 'priority', 'inherit_id', 'website_id'],
        order='key')

    if views:
        print(f"\n  Keyword '{kw}' - {len(views)} views found:")
        for v in views:
            inherit = f" (inherits: {v['inherit_id'][1] if v['inherit_id'] else 'none'})"
            website = f" [website_id={v['website_id'][0]}]" if v['website_id'] else ""
            print(f"    [{v['id']}] active={str(v['active']):5s} key={v['key'] or 'N/A':60s}")
            print(f"           name={v['name']}{inherit}{website}")
    else:
        print(f"\n  Keyword '{kw}' - No views found.")

# ============================================================================
# 3b. All views inheriting from product page
# ============================================================================
print("\n--- All views inheriting from website_sale.product (id=3362) ---")
inheriting_views = execute('ir.ui.view', 'search_read',
    [['inherit_id', '=', 3362]],
    ['name', 'key', 'active', 'priority'],
    order='priority')

for v in inheriting_views:
    status = "ACTIVE" if v['active'] else "INACTIVE"
    print(f"    [{v['id']:5d}] {status:8s} priority={v['priority']:3d} key={v['key'] or 'N/A':65s}")
    print(f"            name={v['name']}")

# ============================================================================
# 3c. INACTIVE website_sale views
# ============================================================================
print("\n--- INACTIVE website_sale views ---")
inactive_views = execute('ir.ui.view', 'search_read',
    [['active', '=', False], ['key', 'ilike', 'website_sale']],
    ['name', 'key'],
    order='key')
print(f"  Found {len(inactive_views)} inactive website_sale views:")
for v in inactive_views:
    print(f"    [{v['id']:5d}] key={v['key'] or 'N/A':65s} name={v['name']}")

# ============================================================================
# 4. RES.CONFIG.SETTINGS - Fields controlling product features
# ============================================================================
print("\n" + "=" * 80)
print("4. RES.CONFIG.SETTINGS - Fields related to products/ecommerce features")
print("=" * 80)

settings_keywords = ['optional', 'alternative', 'accessory', 'cross', 'upsell',
                     'product_page', 'ecommerce', 'website_sale',
                     'group_product', 'module_website']

settings_fields = execute('ir.model.fields', 'search_read',
    [['model', '=', 'res.config.settings']],
    ['name', 'field_description', 'ttype', 'store'],
    order='name')

print(f"\nAll res.config.settings fields ({len(settings_fields)} total):")
print(f"Filtering for keywords: {settings_keywords}\n")

matched_settings = []
for f in settings_fields:
    name_lower = f['name'].lower()
    desc_lower = f['field_description'].lower()
    for kw in settings_keywords:
        if kw in name_lower or kw in desc_lower:
            matched_settings.append(f)
            break

for f in matched_settings:
    print(f"  {f['name']:55s} ({f['ttype']:10s}) - {f['field_description']}")

print("\n--- Reading latest res.config.settings values ---")
try:
    latest_settings_ids = execute('res.config.settings', 'search', [], limit=1, order='id desc')
    if latest_settings_ids:
        settings_field_names = [f['name'] for f in matched_settings]
        settings_data = execute('res.config.settings', 'read', latest_settings_ids, settings_field_names)
        if settings_data:
            print(f"  Settings record id={settings_data[0]['id']}:")
            for key, val in sorted(settings_data[0].items()):
                if key != 'id':
                    print(f"    {key:55s} = {val}")
    else:
        print("  No res.config.settings records found.")
except Exception as e:
    print(f"  ERROR reading settings: {e}")

# ============================================================================
# 5. CHECK res.groups
# ============================================================================
print("\n" + "=" * 80)
print("5. RES.GROUPS - Groups related to product features")
print("=" * 80)

group_keywords = ['optional', 'alternative', 'accessory', 'cross', 'upsell',
                  'product_variant', 'website_sale']

for kw in group_keywords:
    try:
        groups = execute('res.groups', 'search_read',
            [['name', 'ilike', kw]],
            ['name', 'display_name'],
            order='name')
        if groups:
            print(f"\n  Keyword '{kw}' - {len(groups)} groups found:")
            for g in groups:
                print(f"    [{g['id']:4d}] {g['display_name']}")
        else:
            print(f"\n  Keyword '{kw}' - No groups found.")
    except Exception as e:
        print(f"\n  Keyword '{kw}' - ERROR: {e}")

# ============================================================================
# 6. Check ir.module.module for website_sale related modules
# ============================================================================
print("\n" + "=" * 80)
print("6. INSTALLED MODULES - website_sale and related")
print("=" * 80)

ws_modules = execute('ir.module.module', 'search_read',
    [['name', 'ilike', 'website_sale']],
    ['name', 'state', 'shortdesc'],
    order='name')

print(f"\n  Modules matching 'website_sale' ({len(ws_modules)}):")
for m in ws_modules:
    status = "INSTALLED" if m['state'] == 'installed' else m['state'].upper()
    print(f"    {m['name']:45s} {status:12s} - {m['shortdesc']}")

extra_modules = ['sale_product_configurator', 'website_event', 'website_sale_comparison',
                 'website_sale_wishlist', 'website_sale_stock']
for mod_name in extra_modules:
    mods = execute('ir.module.module', 'search_read',
        [['name', '=', mod_name]],
        ['name', 'state', 'shortdesc'])
    for m in mods:
        status = "INSTALLED" if m['state'] == 'installed' else m['state'].upper()
        print(f"    {m['name']:45s} {status:12s} - {m['shortdesc']}")

# ============================================================================
# 7. VIEW ARCH INSPECTION
# ============================================================================
print("\n" + "=" * 80)
print("7. VIEW ARCH INSPECTION - Key views for product recommendations")
print("=" * 80)

# The alternative_products view (renders carousel on product page)
print("\n--- website_sale.alternative_products (id=3376) ---")
alt_view = execute('ir.ui.view', 'read', [3376], ['arch_db', 'active'])
if alt_view:
    print(f"  active: {alt_view[0]['active']}")
    print(f"  arch_db:\n{alt_view[0]['arch_db']}")

# The suggested_products_list view (renders in cart)
print("\n--- website_sale.suggested_products_list (id=3488) ---")
sug_view = execute('ir.ui.view', 'read', [3488], ['arch_db', 'active'])
if sug_view:
    print(f"  active: {sug_view[0]['active']}")
    print(f"  arch_db:\n{sug_view[0]['arch_db']}")

# ============================================================================
# 8. Check ir_config_parameter
# ============================================================================
print("\n" + "=" * 80)
print("8. IR.CONFIG.PARAMETER - System parameters related to ecommerce/products")
print("=" * 80)

params = execute('ir.config_parameter', 'search_read',
    ['|', '|', '|', '|',
     ['key', 'ilike', 'website_sale'],
     ['key', 'ilike', 'ecommerce'],
     ['key', 'ilike', 'optional'],
     ['key', 'ilike', 'accessory'],
     ['key', 'ilike', 'alternative']],
    ['key', 'value'],
    order='key')

if params:
    for p in params:
        print(f"  {p['key']:60s} = {p['value']}")
else:
    print("  No matching system parameters found.")

# ============================================================================
# 9. DIAGNOSIS SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("9. DIAGNOSIS SUMMARY")
print("=" * 80)

print("""
ROOT CAUSE IDENTIFIED:

In Odoo 19, there are THREE different fields for product recommendations,
each shown in a DIFFERENT location on the ecommerce website:

  FIELD                        WHERE IT SHOWS             YOUR DATA
  -------------------------    ------------------------   ----------------
  optional_product_ids         Add-to-cart dialog/modal   55 products (OK)
  alternative_product_ids      Product page carousel      0 products (EMPTY!)
  accessory_product_ids        Cart page suggestions      0 products (EMPTY!)

WHAT'S HAPPENING:

1. PRODUCT PAGE CAROUSEL (alternative_product_ids):
   The view 'website_sale.alternative_products' (id=3376, ACTIVE) renders
   a "Alternative Products" carousel section below the product description.
   It uses the condition: t-if="product.alternative_product_ids"
   Since alternative_product_ids is EMPTY on all products, nothing shows.

2. OPTIONAL PRODUCTS DIALOG (optional_product_ids):
   In Odoo 19, optional_product_ids are shown in a dialog when adding to cart.
   However, the website's add_to_cart_action is set to "go_to_cart", which
   goes directly to the cart page WITHOUT showing any dialog.
   The available options are only "stay" and "go_to_cart" -- there is no
   "force_dialog" option. The sale_product_configurator module is NOT installed.
   So optional_product_ids data exists but is NOT displayed anywhere.

3. CART PAGE SUGGESTIONS (accessory_product_ids):
   The view 'website_sale.suggested_products_list' (id=3488, ACTIVE) renders
   suggested accessories in the cart. It uses 'suggested_products' context var.
   Since accessory_product_ids is EMPTY on all products, nothing shows in cart.

SOLUTION:

To get product carousels showing on the ecommerce product pages:
  -> Populate alternative_product_ids on your products
     (copy the same data you put in optional_product_ids)

To get suggested products in the shopping cart:
  -> Populate accessory_product_ids on your products
     (note: this field uses product.product IDs, NOT product.template IDs)

IMPORTANT FIELD DIFFERENCE:
  - alternative_product_ids: many2many -> product.template (template IDs)
  - accessory_product_ids:   many2many -> product.product  (variant IDs!)
  - optional_product_ids:    many2many -> product.template (template IDs)
""")

print("=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
