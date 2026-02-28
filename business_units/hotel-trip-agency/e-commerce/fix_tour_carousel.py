"""
Fix: Remove the js_product class override from tour product pages.

The custom view agency_ecommerce.product_tour_modal was removing the js_product
class for tours, which broke the alternative products carousel (dynamic snippet
needs js_product to resolve the current productTemplateId via AJAX).

This script updates the view's arch_db in PRODUCTION to remove that xpath block.
The variant selector is already hidden separately, so js_product is safe to keep.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

import xmlrpc.client

# PRODUCTION
url = os.getenv('TARGET_MIGRATION_URL').rstrip('/')
db = os.getenv('TARGET_MIGRATION_DB')
username = os.getenv('TARGET_MIGRATION_USERNAME')
password = os.getenv('TARGET_MIGRATION_PASSWORD')

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def execute(model, method, *args, **kwargs):
    return models.execute_kw(db, uid, password, model, method, args, kwargs)

print(f"Connected to PRODUCTION: {url}\n")

# Find the view
views = execute('ir.ui.view', 'search_read',
    [['name', '=', 'agency_ecommerce.product_tour_modal']],
    ['id', 'name', 'key', 'arch_db'])

if not views:
    print("ERROR: View 'agency_ecommerce.product_tour_modal' not found!")
    sys.exit(1)

view = views[0]
print(f"Found view: {view['name']} (id={view['id']})")

arch = view['arch_db']

# Check if the js_product xpath is present
if 'js_product' not in arch:
    print("The js_product xpath is already removed. Nothing to do.")
    sys.exit(0)

# Remove the js_product xpath block
# The block looks like:
#   <xpath expr="//div[@id='o_wsale_product_details_content']" position="attributes">
#       <attribute name="t-attf-class">...</attribute>
#   </xpath>
import re
# Match the entire xpath block that contains js_product
pattern = r'\s*<!--[^>]*js_product[^>]*-->\s*<xpath[^>]*o_wsale_product_details_content[^>]*>\s*<attribute[^>]*>[^<]*js_product[^<]*</attribute>\s*</xpath>'
new_arch = re.sub(pattern, '', arch)

if new_arch == arch:
    # Try a simpler pattern without the comment
    pattern2 = r'\s*<xpath[^>]*o_wsale_product_details_content[^>]*position="attributes"[^>]*>\s*<attribute[^>]*t-attf-class[^>]*>[^<]*</attribute>\s*</xpath>'
    new_arch = re.sub(pattern2, '', arch)

if new_arch == arch:
    print("WARNING: Could not find the xpath block to remove via regex.")
    print("Attempting manual removal by finding the exact substring...")
    # Find start and end markers
    start_marker = '<xpath expr="//div[@id=\'o_wsale_product_details_content\']"'
    end_marker = '</xpath>'
    start_idx = arch.find(start_marker)
    if start_idx == -1:
        # Try with double quotes
        start_marker = '<xpath expr="//div[@id=&quot;o_wsale_product_details_content&quot;]"'
        start_idx = arch.find(start_marker)

    if start_idx >= 0:
        end_idx = arch.find(end_marker, start_idx) + len(end_marker)
        # Also remove the comment before it
        comment_start = arch.rfind('<!--', 0, start_idx)
        comment_end = arch.find('-->', comment_start) + 3
        if comment_start >= 0 and comment_end <= start_idx + 5:
            start_idx = comment_start
        new_arch = arch[:start_idx].rstrip() + '\n    ' + arch[end_idx:].lstrip()
        print(f"Manually removed {end_idx - start_idx} chars from arch")
    else:
        print("ERROR: Could not locate the xpath block at all!")
        print("First 500 chars of arch:")
        print(arch[:500])
        sys.exit(1)

# Write the updated arch
execute('ir.ui.view', 'write', [view['id']], {'arch': new_arch},
        context={'lang': 'en_US'})

print(f"\nUpdated view {view['id']} — removed js_product class override.")
print("Tours will now keep the js_product class, allowing the alternative products carousel to work.")
