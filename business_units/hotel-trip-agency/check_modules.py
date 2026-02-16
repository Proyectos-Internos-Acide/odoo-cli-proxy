#!/usr/bin/env python3
"""Audit current Odoo instance configuration for travel agency setup."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(__file__))

from odoo_cli import OdooClient
from defaults.modules import AUDIT_MODULES, SETTINGS_FIELDS

client = OdooClient()
client.connect()

# === 1. Check modules ===
print("=" * 60)
print("  1. MODULE STATUS")
print("=" * 60)

installed = client.search_read('ir.module.module',
    domain=[['name', 'in', AUDIT_MODULES]],
    fields=['name', 'state', 'shortdesc'])

found_names = set()
for m in sorted(installed, key=lambda x: x['name']):
    found_names.add(m['name'])
    status = 'OK' if m['state'] == 'installed' else m['state'].upper()
    print(f"  [{status:>12}] {m['name']} - {m['shortdesc']}")

missing = set(AUDIT_MODULES) - found_names
if missing:
    for name in sorted(missing):
        print(f"  [  NOT FOUND] {name}")

# === 2. Settings ===
print("\n" + "=" * 60)
print("  2. SETTINGS (res.config.settings)")
print("=" * 60)
try:
    settings = client.search_read('res.config.settings',
        domain=[], fields=SETTINGS_FIELDS, limit=1, order='id desc')
    if settings:
        for key in SETTINGS_FIELDS:
            val = settings[0].get(key, 'N/A')
            print(f"  {key}: {val}")
    else:
        print("  No settings record found")
except Exception as e:
    print(f"  Error: {e}")

# === 3. Product Categories ===
print("\n" + "=" * 60)
print("  3. PRODUCT CATEGORIES")
print("=" * 60)
cats = client.search_read('product.category', domain=[], fields=['name', 'complete_name'])
for c in cats:
    print(f"  [{c['id']:>3}] {c.get('complete_name', c['name'])}")

# === 4. Product Templates ===
print("\n" + "=" * 60)
print("  4. PRODUCT TEMPLATES")
print("=" * 60)
products = client.search_read('product.template', domain=[],
    fields=['name', 'type', 'categ_id', 'sale_ok', 'purchase_ok',
            'website_published', 'list_price'])
for p in products:
    cat = p.get('categ_id', [None, ''])[1] if p.get('categ_id') else '-'
    pub = 'PUB' if p.get('website_published') else 'UNPUB'
    print(f"  [{p['id']:>3}] {p['name'][:40]:<40} | {p.get('type', '-'):<10} | {cat:<20} | ${p.get('list_price', 0):>8.2f} | {pub}")

# === 5. Product Tags ===
print("\n" + "=" * 60)
print("  5. PRODUCT TAGS")
print("=" * 60)
try:
    tags = client.search_read('product.tag', domain=[], fields=['name'])
    if tags:
        for t in tags:
            print(f"  [{t['id']:>3}] {t['name']}")
    else:
        print("  (none)")
except Exception as e:
    print(f"  Not available: {e}")

# === 6. Quotation Templates ===
print("\n" + "=" * 60)
print("  6. QUOTATION TEMPLATES (sale.order.template)")
print("=" * 60)
try:
    templates = client.search_read('sale.order.template', domain=[],
        fields=['name', 'number_of_days', 'sale_order_template_line_ids',
                'sale_order_template_option_ids'])
    if templates:
        for t in templates:
            lines = len(t.get('sale_order_template_line_ids', []))
            opts = len(t.get('sale_order_template_option_ids', []))
            print(f"  [{t['id']:>3}] {t['name']} | validity={t.get('number_of_days')} days | lines={lines} | options={opts}")
    else:
        print("  (none)")
except Exception as e:
    print(f"  Error: {e}")

# === 7. Sale Orders (last 5) ===
print("\n" + "=" * 60)
print("  7. SALE ORDERS (recent)")
print("=" * 60)
total_orders = len(client.execute('sale.order', 'search', []))
orders = client.search_read('sale.order', domain=[],
    fields=['name', 'partner_id', 'state', 'amount_total'],
    limit=5, order='id desc')
print(f"  Total: {total_orders}")
for o in orders:
    partner = o.get('partner_id', [None, ''])[1] if o.get('partner_id') else '-'
    print(f"  {o['name']:<10} | {partner:<25} | state={o['state']:<10} | ${o.get('amount_total', 0):>8.2f}")

# === 8. CRM ===
print("\n" + "=" * 60)
print("  8. CRM PIPELINE")
print("=" * 60)
try:
    stages = client.search_read('crm.stage', domain=[], fields=['name', 'sequence'])
    for s in sorted(stages, key=lambda x: x.get('sequence', 0)):
        print(f"  Stage: {s['name']}")
    total_leads = len(client.execute('crm.lead', 'search', []))
    print(f"  Total leads/opportunities: {total_leads}")
except Exception as e:
    print(f"  Error: {e}")

# === 9. Projects ===
print("\n" + "=" * 60)
print("  9. PROJECTS")
print("=" * 60)
try:
    projects = client.search_read('project.project', domain=[],
        fields=['name', 'partner_id', 'task_count'])
    if projects:
        for p in projects:
            partner = p.get('partner_id', [None, ''])[1] if p.get('partner_id') else '-'
            print(f"  [{p['id']:>3}] {p['name']:<30} | partner={partner} | tasks={p.get('task_count', 0)}")
    else:
        print("  (none)")
except Exception as e:
    print(f"  Error: {e}")

# === 10. Analytic Accounts ===
print("\n" + "=" * 60)
print("  10. ANALYTIC ACCOUNTS & PLANS")
print("=" * 60)
try:
    plans = client.search_read('account.analytic.plan', domain=[], fields=['name', 'parent_id'])
    print("  Plans:")
    for p in plans:
        parent = p.get('parent_id', [None, ''])[1] if p.get('parent_id') else '-'
        print(f"    [{p['id']:>3}] {p['name']} | parent={parent}")
except Exception as e:
    print(f"  Plans error: {e}")

try:
    accounts = client.search_read('account.analytic.account', domain=[],
        fields=['name', 'plan_id', 'partner_id'], limit=20)
    print(f"  Accounts ({len(accounts)}):")
    for a in accounts:
        plan = a.get('plan_id', [None, ''])[1] if a.get('plan_id') else '-'
        print(f"    [{a['id']:>3}] {a['name']} | plan={plan}")
except Exception as e:
    print(f"  Accounts error: {e}")

# === 11. Fleet ===
print("\n" + "=" * 60)
print("  11. FLEET VEHICLES")
print("=" * 60)
try:
    vehicles = client.search_read('fleet.vehicle', domain=[],
        fields=['name', 'model_id', 'license_plate', 'state_id'])
    if vehicles:
        for v in vehicles:
            model = v.get('model_id', [None, ''])[1] if v.get('model_id') else '-'
            print(f"  [{v['id']:>3}] {v.get('name', '-')} | model={model} | plate={v.get('license_plate', '-')}")
    else:
        print("  (none)")
except Exception as e:
    print(f"  Error: {e}")

# === 12. BoM (Manufacturing) ===
print("\n" + "=" * 60)
print("  12. BILLS OF MATERIALS (mrp.bom)")
print("=" * 60)
try:
    boms = client.search_read('mrp.bom', domain=[],
        fields=['product_tmpl_id', 'type', 'bom_line_ids'])
    if boms:
        for b in boms:
            product = b.get('product_tmpl_id', [None, ''])[1] if b.get('product_tmpl_id') else '-'
            print(f"  [{b['id']:>3}] {product} | type={b.get('type')} | lines={len(b.get('bom_line_ids', []))}")
    else:
        print("  (none)")
except Exception as e:
    print(f"  MRP not installed (expected): {e}")

# === 13. Website ===
print("\n" + "=" * 60)
print("  13. WEBSITE CONFIG")
print("=" * 60)
websites = client.search_read('website', domain=[],
    fields=['name', 'domain', 'default_lang_id', 'tz', 'company_id'])
for w in websites:
    company = w.get('company_id', [None, ''])[1] if w.get('company_id') else '-'
    print(f"  [{w['id']:>3}] {w.get('name', '-')} | domain={w.get('domain', '-')} | tz={w.get('tz', '-')} | company={company}")

# === 14. Companies ===
print("\n" + "=" * 60)
print("  14. COMPANIES")
print("=" * 60)
companies = client.search_read('res.company', domain=[],
    fields=['name', 'currency_id', 'country_id'])
for c in companies:
    currency = c.get('currency_id', [None, ''])[1] if c.get('currency_id') else '-'
    country = c.get('country_id', [None, ''])[1] if c.get('country_id') else '-'
    print(f"  [{c['id']:>3}] {c['name']} | currency={currency} | country={country}")

# === 15. Expense products ===
print("\n" + "=" * 60)
print("  15. EXPENSE-ELIGIBLE PRODUCTS")
print("=" * 60)
try:
    expenses = client.search_read('product.product',
        domain=[['can_be_expensed', '=', True]],
        fields=['name', 'list_price'])
    if expenses:
        for ex in expenses:
            print(f"  [{ex['id']:>3}] {ex['name']} | price={ex.get('list_price')}")
    else:
        print("  (none)")
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "=" * 60)
print("  AUDIT COMPLETE")
print("=" * 60)
