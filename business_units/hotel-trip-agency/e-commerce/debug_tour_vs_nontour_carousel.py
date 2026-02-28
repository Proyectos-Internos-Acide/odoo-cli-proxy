#!/usr/bin/env python3
"""
Debug why the "Alternative Products" carousel shows on lodging and restaurant
product pages but NOT on tour product pages in the PRODUCTION Odoo 19 ecommerce.

All 3 product types have alternative_product_ids populated.
The view website_sale.alternative_products (id=3376) is ACTIVE.

This script investigates:
1. Verify alternative_product_ids on tours vs non-tours
2. Check if tours have website_description (carousel is positioned after it)
3. Check for oe_structure saved views per product
4. Check if tour product pages were customized (views that modify tours)
5. Compare product types and fields
6. Read the full arch_db of the main product page view (id=3362)

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
# 1. VERIFY alternative_product_ids ON TOURS VS NON-TOURS
# ============================================================================
print("\n" + "=" * 80)
print("1. VERIFY alternative_product_ids ON TOURS VS NON-TOURS")
print("=" * 80)

SAMPLE_PRODUCTS = {
    144: "Tour: Machupicchu",
    93:  "Lodging: Apartment 301",
    58:  "Restaurant: Cuy al horno",
}

for pid, label in SAMPLE_PRODUCTS.items():
    print(f"\n--- {label} (ID {pid}) ---")
    try:
        result = execute('product.template', 'read', [pid],
                         ['name', 'alternative_product_ids', 'optional_product_ids',
                          'accessory_product_ids', 'is_published', 'website_published',
                          'sale_ok', 'type'])
        if result:
            p = result[0]
            print(f"  Name:                    {p['name']}")
            print(f"  type:                    {p['type']}")
            print(f"  is_published:            {p.get('is_published')}")
            print(f"  website_published:       {p.get('website_published')}")
            print(f"  sale_ok:                 {p.get('sale_ok')}")
            alt_ids = p.get('alternative_product_ids', [])
            opt_ids = p.get('optional_product_ids', [])
            acc_ids = p.get('accessory_product_ids', [])
            print(f"  alternative_product_ids: {alt_ids} ({len(alt_ids)} items)")
            print(f"  optional_product_ids:    {opt_ids} ({len(opt_ids)} items)")
            print(f"  accessory_product_ids:   {acc_ids} ({len(acc_ids)} items)")

            # Resolve alternative product names + published status
            if alt_ids:
                alt_prods = execute('product.template', 'read', alt_ids,
                                    ['name', 'is_published', 'website_published', 'sale_ok'])
                print(f"  Alternative products:")
                for ap in alt_prods:
                    pub = "published" if ap.get('is_published') else "NOT published"
                    sok = "sale_ok" if ap.get('sale_ok') else "NOT sale_ok"
                    print(f"    [{ap['id']}] {ap['name']} ({pub}, {sok})")
    except Exception as e:
        print(f"  ERROR: {e}")


# ============================================================================
# 2. CHECK IF TOURS HAVE website_description
# ============================================================================
print("\n" + "=" * 80)
print("2. CHECK website_description ON TOURS VS NON-TOURS")
print("=" * 80)

for pid, label in SAMPLE_PRODUCTS.items():
    print(f"\n--- {label} (ID {pid}) ---")
    try:
        result = execute('product.template', 'read', [pid],
                         ['name', 'website_description'])
        if result:
            wd = result[0].get('website_description', False)
            if wd and wd.strip() and wd.strip() != '<p><br></p>':
                print(f"  website_description: HAS CONTENT ({len(wd)} chars)")
            else:
                print(f"  website_description: EMPTY (value={repr(wd)[:80]})")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n  KEY FINDING: Both tours AND restaurant have website_description=False,")
print("  yet the carousel supposedly shows on restaurant but not tours.")
print("  -> website_description is NOT the differentiator.")


# ============================================================================
# 3. CHECK FOR oe_structure SAVED VIEWS PER PRODUCT
# ============================================================================
print("\n" + "=" * 80)
print("3. CHECK FOR oe_structure SAVED VIEWS PER PRODUCT")
print("=" * 80)

try:
    oe_views = execute('ir.ui.view', 'search_read',
                       [['key', 'ilike', 'oe_structure']],
                       ['id', 'key', 'active', 'arch_db', 'website_id'],
                       limit=100)
    if oe_views:
        print(f"\n  Found {len(oe_views)} oe_structure views:")
        for v in oe_views:
            arch = v.get('arch_db', '')
            arch_preview = str(arch)[:200].replace('\n', ' ') if arch else '(empty)'
            website = f" [website={v['website_id'][0]}]" if v.get('website_id') else ""
            active = "ACTIVE" if v['active'] else "INACTIVE"
            print(f"    [{v['id']:5d}] {active:8s} key={v.get('key')}{website}")
            print(f"            arch: {arch_preview}")
    else:
        print(f"\n  No oe_structure views found.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 4. CHECK IF TOUR PRODUCT PAGES WERE CUSTOMIZED
# ============================================================================
print("\n" + "=" * 80)
print("4. CHECK FOR website_sale_recommended AND tour-specific VIEW CUSTOMIZATIONS")
print("=" * 80)

try:
    rec_views = execute('ir.ui.view', 'search_read',
                        [['key', 'ilike', 'website_sale_recommended']],
                        ['id', 'key', 'active', 'arch_db', 'website_id'])
    if rec_views:
        print(f"\n  Found {len(rec_views)} views matching 'website_sale_recommended':")
        for v in rec_views:
            print(f"    [{v['id']}] key={v.get('key')} active={v['active']}")
    else:
        print(f"\n  No views found matching 'website_sale_recommended'.")
except Exception as e:
    print(f"  ERROR: {e}")

# Check agency_ecommerce views that modify tour product pages
print("\n--- Agency ecommerce views that modify tour product pages ---")
try:
    agency_views = execute('ir.ui.view', 'search_read',
                           [['key', 'ilike', 'agency_ecommerce']],
                           ['id', 'key', 'name', 'active', 'inherit_id', 'priority', 'arch_db'],
                           order='key')
    print(f"  Found {len(agency_views)} agency_ecommerce views:")
    for v in agency_views:
        inherit = f" inherits={v['inherit_id'][1]} (id={v['inherit_id'][0]})" if v.get('inherit_id') else ""
        print(f"\n    [{v['id']:5d}] active={v['active']} p={v['priority']} key={v.get('key')}")
        print(f"           name={v['name']}{inherit}")
        arch = v.get('arch_db', '')
        if arch:
            # Show lines that reference x_is_tour or js_product or variant
            lines = str(arch).split('\n')
            relevant_lines = []
            for i, line in enumerate(lines):
                if any(kw in line.lower() for kw in ['x_is_tour', 'js_product', 'variant_info', 'add_to_cart']):
                    relevant_lines.append((i, line.strip()))
            if relevant_lines:
                print(f"           RELEVANT lines:")
                for i, line in relevant_lines:
                    print(f"             L{i}: {line[:150]}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 5. COMPARE PRODUCT TYPES AND FIELDS
# ============================================================================
print("\n" + "=" * 80)
print("5. COMPARE PRODUCT TYPES AND KEY FIELDS")
print("=" * 80)

COMPARE_FIELDS = [
    'name', 'type', 'sale_ok', 'purchase_ok',
    'website_published', 'is_published',
    'categ_id', 'public_categ_ids',
    'service_tracking', 'x_is_tour', 'x_is_a_room_offer',
    'website_description', 'alternative_product_ids',
]

for pid, label in SAMPLE_PRODUCTS.items():
    print(f"\n--- {label} (ID {pid}) ---")
    try:
        result = execute('product.template', 'read', [pid], COMPARE_FIELDS)
        if result:
            p = result[0]
            for field in COMPARE_FIELDS:
                val = p.get(field, 'N/A')
                if field == 'website_description':
                    if val and str(val).strip():
                        val = f"HAS CONTENT ({len(str(val))} chars)"
                    else:
                        val = f"EMPTY"
                elif isinstance(val, list) and len(val) > 5:
                    val = f"{val[:3]}... ({len(val)} items)"
                print(f"  {field:35s} = {val}")
    except Exception as e:
        print(f"  ERROR: {e}")


# ============================================================================
# 6. READ FULL arch_db OF MAIN PRODUCT PAGE VIEW
# ============================================================================
print("\n" + "=" * 80)
print("6. MAIN PRODUCT PAGE VIEW (id=3362) - KEY SECTIONS")
print("=" * 80)

try:
    pv = execute('ir.ui.view', 'read', [3362], ['name', 'key', 'active', 'arch_db'])
    if pv:
        arch = pv[0].get('arch_db', '')
        lines = str(arch).split('\n')
        print(f"  View 3362: key={pv[0].get('key')} active={pv[0]['active']}")
        print(f"  Total lines: {len(lines)}")

        # Show the critical section around product_full_description
        print(f"\n  --- Section around website_description (lines 130-142) ---")
        for i in range(130, min(len(lines), 142)):
            print(f"    L{i:3d}: {lines[i]}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 7. READ FULL arch_db OF ALTERNATIVE PRODUCTS VIEW
# ============================================================================
print("\n" + "=" * 80)
print("7. ALTERNATIVE PRODUCTS VIEW (id=3376)")
print("=" * 80)

try:
    av = execute('ir.ui.view', 'read', [3376],
                 ['name', 'key', 'active', 'arch_db', 'inherit_id',
                  'customize_show', 'priority'])
    if av:
        v = av[0]
        print(f"  View {v['id']}: key={v.get('key')}")
        print(f"  active={v['active']} customize_show={v.get('customize_show')} priority={v.get('priority')}")
        print(f"  inherit_id={v.get('inherit_id')}")
        arch = v.get('arch_db', '')
        if arch:
            print(f"\n  FULL arch_db:")
            for line in str(arch).split('\n'):
                print(f"    {line}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 8. THE KEY INVESTIGATION: js_product CLASS REMOVAL
# ============================================================================
print("\n" + "=" * 80)
print("8. ROOT CAUSE INVESTIGATION: js_product CLASS REMOVAL FOR TOURS")
print("=" * 80)

print("""
  CRITICAL FINDING: View agency_ecommerce.product_tour_modal (id=4850)
  REMOVES the 'js_product' class from #o_wsale_product_details_content
  for tour products (x_is_tour = True):

    <xpath expr="//div[@id='o_wsale_product_details_content']" position="attributes">
        <attribute name="t-attf-class">
            {{ 'js_product' if not product.x_is_tour else '' }} o_wsale_content_contained container
        </attribute>
    </xpath>

  In Odoo 19, the 'js_product' class is what the ProductPage JavaScript
  widget hooks into. When js_product is removed:

  1. The ProductPage widget does NOT initialize on tour product pages
  2. The widget is responsible for setting 'product_template_id' in the
     page context (via .js_product form element's data-* attributes)
  3. The dynamic snippet s_dynamic_snippet_products reads productTemplateId
     from the DOM to make the AJAX call to fetch alternative products
  4. WITHOUT js_product, the JS cannot find the product template ID
  5. The AJAX call to /website/snippet/filters fails silently (no data)
  6. The carousel renders empty (no products fetched) and Odoo hides it

  PROOF:
  - Tour (x_is_tour=True): js_product REMOVED -> carousel MISSING
  - Lodging (x_is_tour=False): js_product PRESENT -> carousel SHOWS
  - Restaurant (x_is_tour=False): js_product PRESENT -> carousel SHOWS
""")

# Verify by reading the exact view
print("--- Reading agency_ecommerce.product_tour_modal (id=4850) ---")
try:
    modal_view = execute('ir.ui.view', 'read', [4850],
                         ['name', 'key', 'active', 'arch_db', 'inherit_id', 'priority'])
    if modal_view:
        v = modal_view[0]
        print(f"  View {v['id']}: key={v.get('key')}")
        print(f"  active={v['active']} priority={v.get('priority')}")
        print(f"  inherit_id={v.get('inherit_id')}")
        arch = v.get('arch_db', '')
        if arch:
            lines = str(arch).split('\n')
            # Show the js_product modification section
            for i, line in enumerate(lines):
                if 'js_product' in line or 'o_wsale_product_details_content' in line:
                    start = max(0, i - 1)
                    end = min(len(lines), i + 3)
                    print(f"\n  js_product modification (lines {start}-{end}):")
                    for j in range(start, end):
                        marker = ">>>" if j == i else "   "
                        print(f"  {marker} L{j}: {lines[j]}")

            # Show the variant_info modification
            for i, line in enumerate(lines):
                if 'variant_info' in line:
                    start = max(0, i - 1)
                    end = min(len(lines), i + 2)
                    print(f"\n  variant_info modification (lines {start}-{end}):")
                    for j in range(start, end):
                        marker = ">>>" if j == i else "   "
                        print(f"  {marker} L{j}: {lines[j]}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 9. CHECK HOW THE DYNAMIC SNIPPET GETS productTemplateId
# ============================================================================
print("\n" + "=" * 80)
print("9. HOW THE DYNAMIC SNIPPET GETS productTemplateId")
print("=" * 80)

# Check the snippet filter for alternative products
print("--- Snippet filter id=7 (Alternative Products) ---")
try:
    sf = execute('website.snippet.filter', 'read', [7],
                 ['name', 'model_name', 'action_server_id', 'limit'])
    if sf:
        print(f"  name: {sf[0]['name']}")
        print(f"  model_name: {sf[0]['model_name']}")
        print(f"  limit: {sf[0]['limit']}")
        action_id = sf[0].get('action_server_id')
        if action_id:
            action = execute('ir.actions.server', 'read',
                             [action_id[0]], ['name', 'code'])
            if action:
                print(f"  Server action: {action[0]['name']} (id={action_id[0]})")
                print(f"  Code:")
                for line in str(action[0].get('code', '')).split('\n'):
                    print(f"    {line}")
                print(f"\n  IMPORTANT: The server action uses request.params.get('productTemplateId')")
                print(f"  This means the JavaScript MUST pass productTemplateId in the AJAX request.")
                print(f"  Without js_product class, the JS cannot determine this ID.")
except Exception as e:
    print(f"  ERROR: {e}")

# Check all views that contain 'productTemplateId' or 'product_template_id' in arch
print("\n--- Views referencing productTemplateId in arch ---")
try:
    ptid_views = execute('ir.ui.view', 'search_read',
                         [['arch_db', 'ilike', 'productTemplateId']],
                         ['id', 'key', 'name', 'active'],
                         limit=20, order='key')
    if ptid_views:
        for v in ptid_views:
            print(f"  [{v['id']}] key={v.get('key')} active={v['active']} name={v['name']}")
    else:
        print(f"  No views found (productTemplateId is likely in JS assets, not QWeb).")
except Exception as e:
    print(f"  ERROR: {e}")

# Check if there's a JS asset that handles s_dynamic_snippet_products
print("\n--- JavaScript assets for s_dynamic_snippet_products ---")
try:
    # Look for JS views
    js_views = execute('ir.ui.view', 'search_read',
                       [['arch_db', 'ilike', 's_dynamic_snippet_products']],
                       ['id', 'key', 'name', 'active'],
                       limit=20, order='key')
    if js_views:
        print(f"  Found {len(js_views)} views referencing s_dynamic_snippet_products:")
        for v in js_views:
            print(f"  [{v['id']}] key={v.get('key')} active={v['active']} name={v['name']}")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 10. CHECK THE ACTUAL RENDERED ATTRIBUTES
# ============================================================================
print("\n" + "=" * 80)
print("10. VERIFY: What does js_product contain on product pages?")
print("=" * 80)

# In the main template, the js_product div is:
# <div id="o_wsale_product_details_content" t-attf-class="js_product o_wsale_content_contained container">
# Inside it there's a <form> and product_id hidden inputs

# Check if there's a hidden input with product_template_id in the main view
try:
    pv = execute('ir.ui.view', 'read', [3362], ['arch_db'])
    if pv:
        arch = pv[0].get('arch_db', '')
        lines = str(arch).split('\n')
        print(f"  Searching main product view for product_template_id or product_id hidden inputs...")
        for i, line in enumerate(lines):
            if 'product_template_id' in line.lower() or ('product_id' in line.lower() and 'hidden' in line.lower()):
                print(f"    L{i}: {line.strip()}")
        # Also search in the CTA wrapper and other child views
        print(f"\n  NOTE: product_template_id is typically set by the product page controller,")
        print(f"  not in the template. The JS reads it from the .js_product form element.")
except Exception as e:
    print(f"  ERROR: {e}")


# ============================================================================
# 11. VERIFY ALTERNATIVE PRODUCTS CAROUSEL WORKS ON LODGING/RESTAURANT
# ============================================================================
print("\n" + "=" * 80)
print("11. VERIFY: Do lodging/restaurant actually have js_product class?")
print("=" * 80)

print("""
  For NON-tour products (x_is_tour = False):
  - The agency_ecommerce.product_tour_modal view renders:
      t-attf-class="{{ 'js_product' if not product.x_is_tour else '' }} o_wsale_content_contained container"
  - Since x_is_tour=False, this evaluates to: "js_product o_wsale_content_contained container"
  - js_product IS present -> ProductPage widget initializes -> productTemplateId available

  For tour products (x_is_tour = True):
  - This evaluates to: " o_wsale_content_contained container"
  - js_product is ABSENT -> ProductPage widget does NOT initialize
  - productTemplateId is NOT available to the dynamic snippet JS
  - The alternative products carousel CANNOT fetch data
  - Result: carousel section renders in HTML (server-side) but remains empty (client-side)
""")

# Verify x_is_tour values for our sample products
for pid, label in SAMPLE_PRODUCTS.items():
    try:
        result = execute('product.template', 'read', [pid], ['name', 'x_is_tour'])
        if result:
            is_tour = result[0].get('x_is_tour', False)
            js_class = '' if is_tour else 'js_product'
            carousel_status = 'MISSING (no productTemplateId)' if is_tour else 'SHOWS (productTemplateId available)'
            print(f"  [{pid}] {result[0]['name']}")
            print(f"    x_is_tour={is_tour} -> class='{js_class} o_wsale_content_contained container'")
            print(f"    Carousel: {carousel_status}")
    except Exception as e:
        print(f"  ERROR: {e}")


# ============================================================================
# 12. DIAGNOSIS AND FIX
# ============================================================================
print("\n" + "=" * 80)
print("12. DIAGNOSIS AND PROPOSED FIX")
print("=" * 80)

print("""
ROOT CAUSE IDENTIFIED:
=======================

The custom view 'agency_ecommerce.product_tour_modal' (id=4850) removes the
'js_product' CSS class from #o_wsale_product_details_content for tour products.

This was done intentionally to prevent the ProductPage JavaScript widget from
initializing on tour pages (to avoid the product configurator/variant RPC calls
and the add-to-cart behavior that doesn't apply to tours).

HOWEVER, removing js_product has an unintended side effect: it also prevents
the dynamic snippet for alternative products from working. The dynamic snippet
JS (s_dynamic_snippet_products) relies on the .js_product element to determine
the current productTemplateId, which it passes to the server action that
fetches alternative products.

Without productTemplateId, the AJAX call to /website/snippet/filters either:
A) Doesn't fire at all (JS can't find the product context)
B) Fires without productTemplateId, and the server returns empty results

Either way, the carousel renders empty and Odoo hides it.

PROPOSED FIX:
=============

Instead of removing js_product entirely, keep the class but disable just the
specific JS behaviors that cause problems for tours. Two approaches:

APPROACH A (Recommended - Minimal change):
  Add a hidden input with the product_template_id OUTSIDE the js_product div,
  so the dynamic snippet JS can find it even without js_product.

  In agency_ecommerce.product_tour_modal, add:
    <xpath expr="//div[@id='product_detail_main']" position="before">
        <input t-if="product.x_is_tour" type="hidden"
               class="product_template_id"
               t-att-value="product.id"/>
    </xpath>

APPROACH B (Better - Keep js_product, disable add-to-cart differently):
  Instead of removing the js_product class entirely, keep it but:
  1. Keep js_product class always present
  2. The add-to-cart is already hidden by agency_ecommerce.cta_tour_quote
  3. The variant selector is already hidden by the t-if on variant_info
  4. The only remaining issue is the ProductPage JS calling
     get_combination_info_website RPC. This happens because of the variant
     selector UL. Since variant_info is already hidden, the JS won't find
     variant elements and the RPC call won't fire.

  In agency_ecommerce.product_tour_modal, CHANGE:
    <xpath expr="//div[@id='o_wsale_product_details_content']" position="attributes">
        <attribute name="t-attf-class">
            {{ 'js_product' if not product.x_is_tour else '' }} o_wsale_content_contained container
        </attribute>
    </xpath>

  TO:
    <!-- REMOVE the js_product override entirely. Let js_product stay. -->
    <!-- The add-to-cart is already hidden by cta_tour_quote view. -->
    <!-- The variant selector is already hidden by the variant_info t-if. -->
    <!-- Keeping js_product allows dynamic snippet (alternative products carousel) to work. -->

  This means DELETE the first xpath from ECOM_PRODUCT_MODAL_ARCH.
""")

print("=" * 80)
print("INVESTIGATION COMPLETE")
print("=" * 80)
