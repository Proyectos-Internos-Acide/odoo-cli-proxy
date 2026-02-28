"""
Set ALL three product recommendation fields for published products
on the PRODUCTION Odoo instance (machupicchu-afdestiny-production).

Fields:
- optional_product_ids: shown in add-to-cart dialog (product.template IDs)
- alternative_product_ids: shown as carousel on product page (product.template IDs)
- accessory_product_ids: shown as suggestions on cart page (product.product IDs)

Products: 6 lodging + 21 restaurant + 28 tours = 55 total
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

import xmlrpc.client

# PRODUCTION credentials
url = os.getenv('TARGET_MIGRATION_URL').rstrip('/')
db = os.getenv('TARGET_MIGRATION_DB')
username = os.getenv('TARGET_MIGRATION_USERNAME')
password = os.getenv('TARGET_MIGRATION_PASSWORD')

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def execute(model, method, *args, **kwargs):
    return models.execute_kw(db, uid, password, model, method, args, kwargs)

print(f"Connected to PRODUCTION: {url} (db={db})\n")

# ==================== LODGING ====================
APT_702 = 81   # $60
APT_701 = 89   # $60
APT_601 = 90   # $70
APT_501 = 91   # $70
APT_401 = 92   # $70
APT_301 = 93   # $70

# ==================== RESTAURANT ====================
# Breakfast
DESAYUNO_CONT = 56       # Desayuno Continental 2

# Entree
LOMO_SALTADO = 57
CUY_AL_HORNO = 58
DIETA_POLLO = 60

# Hamburgers
HAMBURGUESA_CLAS = 61    # Hamburguesa Clasica
HAMBURGUESA_POLLO = 62   # Hamburguesa de Pollo
HAMBURGUESA_MIXTA = 63   # Hamburguesa Mixta

# Sandwiches
SAND_JAMON = 64
SAND_QUESO = 65
SAND_JAMON_QUESO = 66
SAND_CAPRESE = 67
SAND_HUEVO = 68

# Salchipapa
SALCHIPAPA = 69

# Drinks
JUGO_PAPAYA = 71
JUGO_FRESA = 72
JUGO_FRESA_LECHE = 73
JUGO_NARANJA = 74
JUGO_PINA = 75
JUGO_COMBINADO = 76
GASEOSA_500 = 79
GASEOSA_2L = 80

# ==================== TOURS ====================
# City / Cultural
CITY_TOUR = 54            # City Tour Cusco - $30
WALKING_TOUR = 94         # Walking Tour Cusco - $0
CHINCHERO = 129           # Chinchero Maras Moray - $50
CIRCUITO_SUR = 131        # Circuito Sur - $50
COMBINADA = 132           # Combinada - $30
PAGO_TIERRA = 146         # Pago a la Tierra - $300

# Sacred Valley
VALLE_TRAD = 153          # Valle Sagrado Tradicional - $90
VALLE_VIP = 154           # Valle Sagrado VIP - $100
VALLE_MP = 155            # Valle Sagrado conexion a MP - $1200

# Mountain / Nature
RAINBOW_MT = 145          # Montana De 7 Colores - $100
PALCOYO = 98              # Palcoyo - $0
HUMANTAY = 141            # Laguna Humantay - $120
WAQRAPUCARA = 156         # WAQRAPUCARA - $200
QUESWACHACA = 148         # QUESWACHACA +4 LAGUNAS - $200
FARALLONES = 140          # LOS FARALLONES DE TECSECOCHA - $400

# Machu Picchu
MACHUPICCHU = 144         # Machupicchu - $980
MP_BY_CAR = 143           # Machu Picchu By Car 2D/1N - $1200

# Multi-day Treks
INKA_2D = 126             # Camino Inka 2D/1N - $200
INKA_4D = 127             # Camino Inka 4D/3N - $2800
LARES = 142               # Lares Trek MP 4D/3N - $2400
SALKANTAY_4D = 150        # Salkantay 4D/3N - $1450
SALKANTAY_5D = 151        # Salkantay 5D/4N - $1550
CHOQUEQUIRAO = 130        # Choquequirao 4D/3N - $1700

# Multi-day Packages
TRAD_3D = 152             # Tradicional Cusco 3D/2N - $1300
MAGICO_4D = 134           # Cusco Magico 4D/3N - $1500
TRAD_5D = 135             # Cusco Tradicional 5D/4N - $1700

# Puno
PUNO_1D = 147             # Puno 01 Dia Uros/Taquile - $380
RUTA_SOL = 149            # Ruta del Sol Cusco a Puno - $600


# ==================== RELATED PRODUCTS MAPPING ====================
RELATED = {
    # === LODGING: apartments suggest alternatives by price tier ===
    APT_301: [APT_401, APT_501, APT_601, APT_701, APT_702],
    APT_401: [APT_301, APT_501, APT_601, APT_701, APT_702],
    APT_501: [APT_301, APT_401, APT_601, APT_701, APT_702],
    APT_601: [APT_301, APT_401, APT_501, APT_701, APT_702],
    APT_701: [APT_702, APT_601, APT_501, APT_401, APT_301],
    APT_702: [APT_701, APT_601, APT_501, APT_401, APT_301],

    # === RESTAURANT ===
    # Breakfast → entrees + hamburger
    DESAYUNO_CONT: [CUY_AL_HORNO, LOMO_SALTADO, HAMBURGUESA_CLAS, JUGO_PAPAYA],

    # Entrees → other entrees + hamburger
    CUY_AL_HORNO: [LOMO_SALTADO, DIETA_POLLO, HAMBURGUESA_MIXTA, JUGO_COMBINADO],
    LOMO_SALTADO: [CUY_AL_HORNO, DIETA_POLLO, HAMBURGUESA_MIXTA, JUGO_COMBINADO],
    DIETA_POLLO: [CUY_AL_HORNO, LOMO_SALTADO, HAMBURGUESA_POLLO, JUGO_FRESA],

    # Hamburgers → other hamburgers + entrees
    HAMBURGUESA_CLAS: [HAMBURGUESA_POLLO, HAMBURGUESA_MIXTA, SALCHIPAPA, GASEOSA_500],
    HAMBURGUESA_POLLO: [HAMBURGUESA_CLAS, HAMBURGUESA_MIXTA, SALCHIPAPA, GASEOSA_500],
    HAMBURGUESA_MIXTA: [HAMBURGUESA_CLAS, HAMBURGUESA_POLLO, SALCHIPAPA, GASEOSA_500],

    # Sandwiches → other sandwiches + drinks
    SAND_JAMON: [SAND_QUESO, SAND_JAMON_QUESO, SAND_CAPRESE, JUGO_NARANJA],
    SAND_QUESO: [SAND_JAMON, SAND_JAMON_QUESO, SAND_CAPRESE, JUGO_NARANJA],
    SAND_JAMON_QUESO: [SAND_JAMON, SAND_QUESO, SAND_CAPRESE, JUGO_FRESA_LECHE],
    SAND_CAPRESE: [SAND_JAMON, SAND_QUESO, SAND_HUEVO, JUGO_PINA],
    SAND_HUEVO: [SAND_JAMON, SAND_JAMON_QUESO, SAND_CAPRESE, JUGO_FRESA],

    # Salchipapa → hamburgers + drinks
    SALCHIPAPA: [HAMBURGUESA_CLAS, HAMBURGUESA_MIXTA, GASEOSA_500, GASEOSA_2L],

    # Drinks → other drinks + food combos
    JUGO_PAPAYA: [JUGO_FRESA, JUGO_NARANJA, JUGO_COMBINADO, JUGO_PINA],
    JUGO_FRESA: [JUGO_PAPAYA, JUGO_FRESA_LECHE, JUGO_NARANJA, JUGO_COMBINADO],
    JUGO_FRESA_LECHE: [JUGO_FRESA, JUGO_PAPAYA, JUGO_COMBINADO, JUGO_PINA],
    JUGO_NARANJA: [JUGO_PAPAYA, JUGO_FRESA, JUGO_PINA, JUGO_COMBINADO],
    JUGO_PINA: [JUGO_PAPAYA, JUGO_NARANJA, JUGO_FRESA, JUGO_COMBINADO],
    JUGO_COMBINADO: [JUGO_PAPAYA, JUGO_FRESA, JUGO_NARANJA, JUGO_PINA],
    GASEOSA_500: [GASEOSA_2L, HAMBURGUESA_CLAS, SALCHIPAPA, SAND_JAMON],
    GASEOSA_2L: [GASEOSA_500, HAMBURGUESA_MIXTA, SALCHIPAPA, SAND_JAMON_QUESO],

    # === TOURS (only alternative_product_ids — tours don't go to cart) ===
    # -- City / Cultural day trips --
    CITY_TOUR: [WALKING_TOUR, CHINCHERO, COMBINADA, PAGO_TIERRA, RAINBOW_MT],
    WALKING_TOUR: [CITY_TOUR, CHINCHERO, COMBINADA, PAGO_TIERRA, RAINBOW_MT],
    CHINCHERO: [VALLE_TRAD, VALLE_VIP, CIRCUITO_SUR, COMBINADA, WALKING_TOUR],
    CIRCUITO_SUR: [CHINCHERO, COMBINADA, VALLE_TRAD, WALKING_TOUR, PAGO_TIERRA],
    COMBINADA: [CHINCHERO, CIRCUITO_SUR, VALLE_TRAD, WALKING_TOUR, RAINBOW_MT],
    PAGO_TIERRA: [WALKING_TOUR, CHINCHERO, COMBINADA, VALLE_VIP, HUMANTAY],

    # -- Sacred Valley --
    VALLE_TRAD: [VALLE_VIP, VALLE_MP, CHINCHERO, MACHUPICCHU, CIRCUITO_SUR],
    VALLE_VIP: [VALLE_TRAD, VALLE_MP, CHINCHERO, MACHUPICCHU, PAGO_TIERRA],
    VALLE_MP: [MACHUPICCHU, MP_BY_CAR, VALLE_VIP, VALLE_TRAD, INKA_2D],

    # -- Mountain / Nature day trips --
    RAINBOW_MT: [PALCOYO, HUMANTAY, WAQRAPUCARA, QUESWACHACA, WALKING_TOUR],
    PALCOYO: [RAINBOW_MT, HUMANTAY, QUESWACHACA, WAQRAPUCARA, FARALLONES],
    HUMANTAY: [RAINBOW_MT, PALCOYO, WAQRAPUCARA, QUESWACHACA, SALKANTAY_4D],
    WAQRAPUCARA: [FARALLONES, QUESWACHACA, RAINBOW_MT, HUMANTAY, PALCOYO],
    QUESWACHACA: [WAQRAPUCARA, RAINBOW_MT, HUMANTAY, FARALLONES, PALCOYO],
    FARALLONES: [WAQRAPUCARA, QUESWACHACA, CHOQUEQUIRAO, HUMANTAY, RAINBOW_MT],

    # -- Machu Picchu --
    MACHUPICCHU: [MP_BY_CAR, VALLE_MP, INKA_2D, SALKANTAY_4D, VALLE_TRAD],
    MP_BY_CAR: [MACHUPICCHU, VALLE_MP, INKA_2D, VALLE_VIP, SALKANTAY_4D],

    # -- Multi-day Treks --
    INKA_2D: [INKA_4D, SALKANTAY_4D, MACHUPICCHU, LARES, MP_BY_CAR],
    INKA_4D: [INKA_2D, SALKANTAY_5D, LARES, CHOQUEQUIRAO, SALKANTAY_4D],
    LARES: [SALKANTAY_4D, INKA_4D, CHOQUEQUIRAO, SALKANTAY_5D, INKA_2D],
    SALKANTAY_4D: [SALKANTAY_5D, LARES, INKA_4D, MACHUPICCHU, INKA_2D],
    SALKANTAY_5D: [SALKANTAY_4D, LARES, INKA_4D, CHOQUEQUIRAO, INKA_2D],
    CHOQUEQUIRAO: [INKA_4D, SALKANTAY_5D, LARES, FARALLONES, SALKANTAY_4D],

    # -- Multi-day Packages --
    TRAD_3D: [MAGICO_4D, TRAD_5D, MACHUPICCHU, VALLE_MP, RUTA_SOL],
    MAGICO_4D: [TRAD_3D, TRAD_5D, RUTA_SOL, MACHUPICCHU, PUNO_1D],
    TRAD_5D: [MAGICO_4D, TRAD_3D, RUTA_SOL, PUNO_1D, MACHUPICCHU],

    # -- Puno --
    RUTA_SOL: [PUNO_1D, TRAD_5D, MAGICO_4D, TRAD_3D, MACHUPICCHU],
    PUNO_1D: [RUTA_SOL, TRAD_5D, MAGICO_4D, TRAD_3D, MACHUPICCHU],
}

# Tour IDs — these only get alternative_product_ids (no cart interaction)
TOUR_IDS = {
    CITY_TOUR, WALKING_TOUR, CHINCHERO, CIRCUITO_SUR, COMBINADA, PAGO_TIERRA,
    VALLE_TRAD, VALLE_VIP, VALLE_MP,
    RAINBOW_MT, PALCOYO, HUMANTAY, WAQRAPUCARA, QUESWACHACA, FARALLONES,
    MACHUPICCHU, MP_BY_CAR,
    INKA_2D, INKA_4D, LARES, SALKANTAY_4D, SALKANTAY_5D, CHOQUEQUIRAO,
    TRAD_3D, MAGICO_4D, TRAD_5D,
    RUTA_SOL, PUNO_1D,
}

# --- Build template → variant ID mapping for accessory_product_ids ---
all_ids = list(RELATED.keys())
for v in RELATED.values():
    all_ids.extend(v)
all_ids = list(set(all_ids))

print("Building template → variant mapping...")
products = execute('product.template', 'read', all_ids, ['name', 'product_variant_ids'])
name_map = {p['id']: p['name'] for p in products}
# Map template_id → first product.product variant ID
template_to_variant = {}
for p in products:
    if p['product_variant_ids']:
        template_to_variant[p['id']] = p['product_variant_ids'][0]

# --- Apply to Odoo ---
print(f"\nSetting recommendation fields for {len(RELATED)} products...\n")

errors = []
success = 0

for product_id, related_ids in RELATED.items():
    product_name = name_map.get(product_id, f"ID {product_id}")
    related_names = [name_map.get(rid, f"ID {rid}") for rid in related_ids]
    is_tour = product_id in TOUR_IDS

    if is_tour:
        # Tours: only carousel on product page, clear cart-related fields
        vals = {
            'alternative_product_ids': [(6, 0, related_ids)],
            'optional_product_ids': [(5,)],
            'accessory_product_ids': [(5,)],
        }
        label = "ALT"
    else:
        # Lodging/Restaurant: all 3 fields (carousel + cart modal + cart suggestions)
        variant_ids = [template_to_variant[rid] for rid in related_ids if rid in template_to_variant]
        vals = {
            'optional_product_ids': [(6, 0, related_ids)],
            'alternative_product_ids': [(6, 0, related_ids)],
            'accessory_product_ids': [(6, 0, variant_ids)],
        }
        label = "ALL"

    try:
        execute('product.template', 'write', [product_id], vals)
        print(f"  [{label}] {product_name} ({product_id})")
        for rn in related_names:
            print(f"       -> {rn}")
        success += 1
    except Exception as e:
        print(f"  ERROR on {product_name}: {e}")
        errors.append((product_id, product_name, str(e)))

print(f"\nDone: {success}/{len(RELATED)} products updated successfully.")
print("Tours: alternative_product_ids only (carousel)")
print("Lodging/Restaurant: all 3 fields (carousel + cart modal + cart suggestions)")
if errors:
    print(f"\nErrors ({len(errors)}):")
    for pid, pname, err in errors:
        print(f"  - {pname} ({pid}): {err}")
