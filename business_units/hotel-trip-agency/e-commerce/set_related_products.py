"""
Set optional_product_ids (related products / cross-sell) for all published tours.

Logic: Each tour suggests 4-5 complementary or alternative tours based on:
- Same region/type but different experience
- Similar duration alternatives
- Commonly booked together
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

# --- Tour product IDs ---
WALKING_TOUR = 94
PALCOYO = 98
CHINCHERO = 131
CIRCUITO_SUR = 132
HUMANTAY = 133
COMBINADA = 134
VALLE_VIP = 135
VALLE_TRAD = 136
RAINBOW_MT = 137  # Montana De 7 Colores
MACHUPICCHU = 138
MP_BY_CAR = 139
VALLE_MP = 140    # Valle Sagrado conexion a MP
INKA_2D = 141     # Camino Inka 2D/1N
INKA_4D = 142     # Camino Inka 4D/3N
LARES = 143       # Lares Trek MP 4D/3N
SALKANTAY_4D = 144
SALKANTAY_5D = 145
CHOQUEQUIRAO = 146
QUESWACHACA = 147
FARALLONES = 148  # Los Farallones de Tecsecocha
WAQRAPUCARA = 149
TRAD_3D = 150     # Tradicional Cusco 3D/2N
MAGICO_4D = 151   # Cusco Magico 4D/3N
TRAD_5D = 152     # Cusco Tradicional 5D/4N
RUTA_SOL = 153    # Ruta del Sol Cusco a Puno
PAGO_TIERRA = 154 # Pago a la Tierra + Ceremonia Andina
PUNO_1D = 155     # Puno 01 Dia Isla Uros/Taquile

# --- Related products mapping ---
# Key: product_template_id
# Value: list of related product_template_ids
RELATED = {
    # === CITY / CULTURAL DAY TRIPS ===
    WALKING_TOUR: [CHINCHERO, COMBINADA, PAGO_TIERRA, RAINBOW_MT, VALLE_TRAD],
    CHINCHERO: [VALLE_TRAD, VALLE_VIP, CIRCUITO_SUR, COMBINADA, WALKING_TOUR],
    CIRCUITO_SUR: [CHINCHERO, COMBINADA, VALLE_TRAD, WALKING_TOUR, PAGO_TIERRA],
    COMBINADA: [CHINCHERO, CIRCUITO_SUR, VALLE_TRAD, WALKING_TOUR, RAINBOW_MT],
    PAGO_TIERRA: [WALKING_TOUR, CHINCHERO, COMBINADA, VALLE_VIP, HUMANTAY],

    # === SACRED VALLEY ===
    VALLE_TRAD: [VALLE_VIP, VALLE_MP, CHINCHERO, MACHUPICCHU, CIRCUITO_SUR],
    VALLE_VIP: [VALLE_TRAD, VALLE_MP, CHINCHERO, MACHUPICCHU, PAGO_TIERRA],
    VALLE_MP: [MACHUPICCHU, MP_BY_CAR, VALLE_VIP, VALLE_TRAD, INKA_2D],

    # === MOUNTAIN / NATURE DAY TRIPS ===
    RAINBOW_MT: [PALCOYO, HUMANTAY, WAQRAPUCARA, QUESWACHACA, WALKING_TOUR],
    PALCOYO: [RAINBOW_MT, HUMANTAY, QUESWACHACA, WAQRAPUCARA, FARALLONES],
    HUMANTAY: [RAINBOW_MT, PALCOYO, WAQRAPUCARA, QUESWACHACA, SALKANTAY_4D],
    WAQRAPUCARA: [FARALLONES, QUESWACHACA, RAINBOW_MT, HUMANTAY, PALCOYO],
    QUESWACHACA: [WAQRAPUCARA, RAINBOW_MT, HUMANTAY, FARALLONES, PALCOYO],
    FARALLONES: [WAQRAPUCARA, QUESWACHACA, CHOQUEQUIRAO, HUMANTAY, RAINBOW_MT],

    # === MACHU PICCHU ===
    MACHUPICCHU: [MP_BY_CAR, VALLE_MP, INKA_2D, SALKANTAY_4D, VALLE_TRAD],
    MP_BY_CAR: [MACHUPICCHU, VALLE_MP, INKA_2D, VALLE_VIP, SALKANTAY_4D],

    # === MULTI-DAY TREKS ===
    INKA_2D: [INKA_4D, SALKANTAY_4D, MACHUPICCHU, LARES, MP_BY_CAR],
    INKA_4D: [INKA_2D, SALKANTAY_5D, LARES, CHOQUEQUIRAO, SALKANTAY_4D],
    LARES: [SALKANTAY_4D, INKA_4D, CHOQUEQUIRAO, SALKANTAY_5D, INKA_2D],
    SALKANTAY_4D: [SALKANTAY_5D, LARES, INKA_4D, MACHUPICCHU, INKA_2D],
    SALKANTAY_5D: [SALKANTAY_4D, LARES, INKA_4D, CHOQUEQUIRAO, INKA_2D],
    CHOQUEQUIRAO: [INKA_4D, SALKANTAY_5D, LARES, FARALLONES, SALKANTAY_4D],

    # === MULTI-DAY PACKAGES ===
    TRAD_3D: [MAGICO_4D, TRAD_5D, MACHUPICCHU, VALLE_MP, RUTA_SOL],
    MAGICO_4D: [TRAD_3D, TRAD_5D, RUTA_SOL, MACHUPICCHU, PUNO_1D],
    TRAD_5D: [MAGICO_4D, TRAD_3D, RUTA_SOL, PUNO_1D, MACHUPICCHU],

    # === PUNO ===
    RUTA_SOL: [PUNO_1D, TRAD_5D, MAGICO_4D, TRAD_3D, MACHUPICCHU],
    PUNO_1D: [RUTA_SOL, TRAD_5D, MAGICO_4D, TRAD_3D, MACHUPICCHU],
}

# --- Apply to Odoo ---
print(f"Setting related products for {len(RELATED)} tours...\n")

# Get product names for display
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
        # Use [(6, 0, ids)] to replace the entire m2m field
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

print(f"\nDone: {success}/{len(RELATED)} tours updated successfully.")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for pid, pname, err in errors:
        print(f"  - {pname} ({pid}): {err}")
