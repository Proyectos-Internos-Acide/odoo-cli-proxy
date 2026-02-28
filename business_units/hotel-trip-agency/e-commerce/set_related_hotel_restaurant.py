"""
Set optional_product_ids (related products / cross-sell) for hotel rooms and restaurant products.

Hotel logic: suggest alternative rooms at similar/adjacent price tiers.
Restaurant logic: suggest complementary items from same or adjacent categories.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

import xmlrpc.client

url = os.getenv('ODOO_URL').rstrip('/')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USER')
password = os.getenv('ODOO_PASSWORD')

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def execute(model, method, *args, **kwargs):
    return models.execute_kw(db, uid, password, model, method, args, kwargs)

# ========== HOTEL ROOMS ==========
# Premium tier
DELUXE_SUITE = 15    # $195
# Mid tier
STANDARD_ROOM = 17   # $95
APT_301 = 93         # $70
APT_401 = 92         # $70
APT_501 = 91         # $70
APT_601 = 90         # $70
# Budget tier
APT_701 = 89         # $60
APT_702 = 81         # $60

# ========== RESTAURANT ==========
# Breakfast
BREAKFAST = 10           # $15
BREAKFAST_TRAY = 11      # $15
DESAYUNO_CONT = 56       # $15
# Entree / Main
CUY_AL_HORNO = 58        # $65
LOMO_SALTADO = 57        # $1
DIETA_POLLO = 60         # $1
SOPA_MINUTA = 156        # $15
# Hamburgers
HAMBURGUESA = 63         # $1

# --- Related products mapping ---
RELATED = {
    # === HOTEL: each room suggests alternatives across tiers ===
    DELUXE_SUITE: [STANDARD_ROOM, APT_301, APT_401, APT_501],
    STANDARD_ROOM: [DELUXE_SUITE, APT_301, APT_401, APT_601],
    APT_301: [APT_401, APT_501, APT_601, STANDARD_ROOM, APT_701],
    APT_401: [APT_301, APT_501, APT_601, STANDARD_ROOM, APT_702],
    APT_501: [APT_301, APT_401, APT_601, APT_701, APT_702],
    APT_601: [APT_301, APT_401, APT_501, APT_701, APT_702],
    APT_701: [APT_702, APT_601, APT_501, APT_301, STANDARD_ROOM],
    APT_702: [APT_701, APT_601, APT_501, APT_401, STANDARD_ROOM],

    # === RESTAURANT: complementary items ===
    # Breakfasts suggest other breakfasts + popular mains
    BREAKFAST: [BREAKFAST_TRAY, DESAYUNO_CONT, SOPA_MINUTA, CUY_AL_HORNO],
    BREAKFAST_TRAY: [BREAKFAST, DESAYUNO_CONT, SOPA_MINUTA, CUY_AL_HORNO],
    DESAYUNO_CONT: [BREAKFAST, BREAKFAST_TRAY, SOPA_MINUTA, CUY_AL_HORNO],

    # Mains suggest other mains + breakfasts
    CUY_AL_HORNO: [LOMO_SALTADO, SOPA_MINUTA, DIETA_POLLO, HAMBURGUESA],
    LOMO_SALTADO: [CUY_AL_HORNO, SOPA_MINUTA, DIETA_POLLO, HAMBURGUESA],
    DIETA_POLLO: [CUY_AL_HORNO, LOMO_SALTADO, SOPA_MINUTA, HAMBURGUESA],
    SOPA_MINUTA: [CUY_AL_HORNO, LOMO_SALTADO, DIETA_POLLO, HAMBURGUESA],

    # Hamburger suggests mains
    HAMBURGUESA: [CUY_AL_HORNO, LOMO_SALTADO, SOPA_MINUTA, DIETA_POLLO],
}

# --- Apply to Odoo ---
print(f"Setting related products for {len(RELATED)} products...\n")

all_ids = list(RELATED.keys())
for v in RELATED.values():
    all_ids.extend(v)
all_ids = list(set(all_ids))

products = execute('product.template', 'read', all_ids, ['name'])
name_map = {p['id']: p['name'] for p in products}

errors = []
success = 0

for product_id, related_ids in RELATED.items():
    product_name = name_map.get(product_id, f"ID {product_id}")
    related_names = [name_map.get(rid, f"ID {rid}") for rid in related_ids]

    try:
        execute('product.template', 'write', [product_id], {
            'optional_product_ids': [(6, 0, related_ids)]
        })
        print(f"  {product_name} ({product_id})")
        for rn in related_names:
            print(f"    -> {rn}")
        success += 1
    except Exception as e:
        print(f"  ERROR on {product_name}: {e}")
        errors.append((product_id, product_name, str(e)))

print(f"\nDone: {success}/{len(RELATED)} products updated successfully.")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for pid, pname, err in errors:
        print(f"  - {pname} ({pid}): {err}")
