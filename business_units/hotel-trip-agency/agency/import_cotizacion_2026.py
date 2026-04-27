#!/usr/bin/env python3
"""
Import products from COTIZACION 2026.xlsx into Odoo production.
Creates categories, attributes, product templates and variants.

Usage:
    python import_cotizacion_2026.py --dry-run   # Preview what will be created
    python import_cotizacion_2026.py              # Actually create products
"""

import xmlrpc.client
import openpyxl
import re
import sys
import os
from collections import defaultdict

# --- Connection ---
URL = 'https://machupicchu-afdestiny-production.odoo.com/'
DB = 'machupicchu-afdestiny-production'
USER = 'ayfdestinyeirl@gmail.com'
PW = os.environ.get('ODOO_PW', 'L^yUbD2^+p^2h.#')
EXCEL_PATH = '/home/gonzalo/Descargas/COTIZACION 2026.xlsx'

DRY_RUN = '--dry-run' in sys.argv

# --- City normalization ---
CITY_MAP = {
    'Mchupicchu': 'Machupicchu',
    'Valle Sagrado': 'Valle Sagrado',
    'Tour Cusco': 'Cusco',
    'Tour Lima': 'Lima',
    'Tour Puno': 'Puno',
    'Tour Arequipa': 'Arequipa',
    'Tour Maldonado': 'Maldonado',
    'Tour Valle Sargrado': 'Valle Sagrado',
    'Tour Valle Sagrado': 'Valle Sagrado',
}

def normalize_city(raw):
    raw = (raw or '').strip()
    return CITY_MAP.get(raw, raw)

# --- Tour name typo corrections ---
TOUR_NAME_FIXES = {
    'Valle sagrado - Pisac - Ollantao': 'Valle sagrado - Pisac - Ollanta',
    'Cerrojo': 'Cerrojo',  # normalize extra spaces
}

# --- Pax range helpers ---
PAX_RANGES_STANDARD = ['1 pax', '2 pax', '3 pax', '4 pax', '5-6 pax', '7-8 pax', '9-10 pax']

def extract_pax_label(name):
    """Extract pax label from product name like 'City Tour x3' or 'Amazonia (1pax)'"""
    # Match patterns: x1, x2, x3, x4, x5-6, x7-8, x9-10
    m = re.search(r'x\s*(\d+(?:\s*-\s*\d+)?)\s*(?:pax)?$', name.strip(), re.IGNORECASE)
    if m:
        val = m.group(1).replace(' ', '')
        return f"{val} pax"
    # Match: (1pax), (+2pax), (1 pax), etc
    m = re.search(r'\((\+?\d+(?:\s*-?\s*\d+)?)\s*pax\)', name, re.IGNORECASE)
    if m:
        val = m.group(1).replace(' ', '')
        return f"{val} pax"
    # Match: - 1 pax, - 2pax at end
    m = re.search(r'-\s*(\d+(?:\s*-\s*\d+)?)\s*pax$', name.strip(), re.IGNORECASE)
    if m:
        val = m.group(1).replace(' ', '')
        return f"{val} pax"
    return None

def extract_base_name(name):
    """Remove pax suffix from name to get base tour/traslado name"""
    # Remove: x1, x2, x 5 -6, (1pax), (+2pax), - 1 pax
    cleaned = re.sub(r'\s*x\s*\d+(?:\s*-\s*\d+)?\s*(?:pax)?\s*$', '', name.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*\(\+?\d+(?:\s*-?\s*\d+)?\s*pax\)\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s*-\s*\d+(?:\s*-\s*\d+)?\s*pax\s*$', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

# --- Room type normalization ---
def extract_room_type(tipo_hab):
    """Extract room type from 'Hotel Name - Simple' format"""
    if not tipo_hab:
        return None
    # Handle both " - " and "- " (typo without leading space)
    m = re.search(r'\s*-\s*(Simple|Doble o Matrimonial|Tripe|Triple|Triples|Familiar\s*)\s*$', tipo_hab, re.IGNORECASE)
    if m:
        rt = m.group(1).strip()
        if rt in ('Tripe', 'Triple', 'Triples'):
            return 'Triple'
        if rt.startswith('Familiar'):
            return 'Familiar'
        if rt == 'Doble o Matrimonial':
            return 'Doble o Matrimonial'
        if rt == 'Simple':
            return 'Simple'
        return rt
    return None

def extract_hotel_name_from_tipo(tipo_hab):
    """Extract hotel name from tipo_hab column (before the room type dash)"""
    if not tipo_hab:
        return None
    m = re.search(r'^(.+?)\s*-\s*(?:Simple|Doble o Matrimonial|Tripe|Triple|Familiar)', tipo_hab, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None

ROOM_TYPES_ORDER = ['Simple', 'Doble o Matrimonial', 'Triple', 'Familiar']


class OdooImporter:
    def __init__(self):
        if not DRY_RUN:
            common = xmlrpc.client.ServerProxy(f'{URL}xmlrpc/2/common')
            self.uid = common.authenticate(DB, USER, PW, {})
            self.models = xmlrpc.client.ServerProxy(f'{URL}xmlrpc/2/object')
            self._load_existing()
        else:
            self.uid = None
            self.models = None
            self._existing_products = set()
            self._existing_categories = {}
            self._existing_attrs = {}
            self._existing_attr_values = {}

        self.wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
        self.created_categories = {}
        self.created_products = []
        self.skipped_products = []

    def execute(self, model, method, *args, **kwargs):
        return self.models.execute_kw(DB, self.uid, PW, model, method, *args, **kwargs)

    def _load_existing(self):
        """Load existing data to avoid duplicates"""
        # Existing product templates
        prods = self.execute('product.template', 'search_read', [[]], {'fields': ['name'], 'limit': 5000})
        self._existing_products = {p['name'].strip() for p in prods}
        print(f"  Loaded {len(self._existing_products)} existing product templates")

        # Existing categories
        cats = self.execute('product.category', 'search_read',
                            [[['name', 'ilike', 'Agencia']]],
                            {'fields': ['id', 'name']})
        self._existing_categories = {c['name']: c['id'] for c in cats}
        print(f"  Loaded {len(self._existing_categories)} existing Agencia categories")

        # Existing attributes
        attrs = self.execute('product.attribute', 'search_read', [[]], {'fields': ['id', 'name', 'value_ids']})
        self._existing_attrs = {a['name']: a for a in attrs}
        print(f"  Loaded {len(self._existing_attrs)} existing attributes")

        # Existing attribute values
        vals = self.execute('product.attribute.value', 'search_read', [[]], {'fields': ['id', 'name', 'attribute_id']})
        self._existing_attr_values = {}
        for v in vals:
            key = (v['attribute_id'][0], v['name'])
            self._existing_attr_values[key] = v['id']
        print(f"  Loaded {len(self._existing_attr_values)} existing attribute values")

    # ------ Category management ------
    def get_or_create_category(self, name):
        if name in self._existing_categories:
            return self._existing_categories[name]
        if name in self.created_categories:
            return self.created_categories[name]
        if DRY_RUN:
            fake_id = 9000 + len(self.created_categories)
            self.created_categories[name] = fake_id
            return fake_id
        cat_id = self.execute('product.category', 'create', [{'name': name}])
        if isinstance(cat_id, list):
            cat_id = cat_id[0]
        self._existing_categories[name] = cat_id
        self.created_categories[name] = cat_id
        print(f"    [CAT] Created category: {name} (id={cat_id})")
        return cat_id

    # ------ Attribute management ------
    def get_or_create_attribute(self, attr_name, value_names):
        """Get or create attribute with given values. Returns (attr_id, {value_name: value_id})"""
        if DRY_RUN:
            return (9999, {v: 8000 + i for i, v in enumerate(value_names)})

        attr_data = self._existing_attrs.get(attr_name)
        if attr_data:
            attr_id = attr_data['id']
        else:
            attr_id = self.execute('product.attribute', 'create', [{
                'name': attr_name,
                'create_variant': 'always',
                'display_type': 'radio',
            }])
            if isinstance(attr_id, list):
                attr_id = attr_id[0]
            self._existing_attrs[attr_name] = {'id': attr_id, 'name': attr_name, 'value_ids': []}
            print(f"    [ATTR] Created attribute: {attr_name} (id={attr_id})")

        # Ensure all values exist
        value_map = {}
        for vname in value_names:
            key = (attr_id, vname)
            if key in self._existing_attr_values:
                value_map[vname] = self._existing_attr_values[key]
            else:
                vid = self.execute('product.attribute.value', 'create', [{
                    'name': vname,
                    'attribute_id': attr_id,
                }])
                if isinstance(vid, list):
                    vid = vid[0]
                self._existing_attr_values[key] = vid
                value_map[vname] = vid
                print(f"    [VAL] Created value: {vname} for attr {attr_name} (id={vid})")

        return (attr_id, value_map)

    # ------ Product creation ------
    def create_simple_product(self, name, categ_name, price, product_type='service'):
        """Create a simple product without variants"""
        if name in self._existing_products:
            self.skipped_products.append((name, 'already exists'))
            return None

        categ_id = self.get_or_create_category(categ_name)

        if DRY_RUN:
            self.created_products.append({
                'type': 'simple',
                'name': name,
                'category': categ_name,
                'price': price,
            })
            self._existing_products.add(name)
            return None

        tmpl_id = self.execute('product.template', 'create', [{
            'name': name,
            'type': product_type,
            'categ_id': categ_id,
            'list_price': round(price, 2) if price else 0,
            'sale_ok': True,
            'purchase_ok': True,
        }])
        if isinstance(tmpl_id, list):
            tmpl_id = tmpl_id[0]

        self._existing_products.add(name)
        self.created_products.append({
            'type': 'simple',
            'name': name,
            'category': categ_name,
            'price': price,
            'tmpl_id': tmpl_id,
        })
        print(f"  [PROD] {name} | price={price} | cat={categ_name}")
        return tmpl_id

    def create_variant_product(self, name, categ_name, attr_name, variants, product_type='service'):
        """
        Create a product with variants.
        variants: list of (value_name, price_extra)
        Product base price = 0, each variant has price_extra.
        """
        if name in self._existing_products:
            self.skipped_products.append((name, 'already exists'))
            return None

        # Filter out variants with price <= 0
        valid_variants = [(v, p) for v, p in variants if p and p > 0]
        if not valid_variants:
            self.skipped_products.append((name, 'all variants have price 0'))
            return None

        categ_id = self.get_or_create_category(categ_name)
        value_names = [v for v, _ in valid_variants]
        attr_id, value_map = self.get_or_create_attribute(attr_name, value_names)

        if DRY_RUN:
            self.created_products.append({
                'type': 'variant',
                'name': name,
                'category': categ_name,
                'attribute': attr_name,
                'variants': valid_variants,
            })
            self._existing_products.add(name)
            return None

        # Create product template
        tmpl_id = self.execute('product.template', 'create', [{
            'name': name,
            'type': product_type,
            'categ_id': categ_id,
            'list_price': 0,
            'sale_ok': True,
            'purchase_ok': True,
        }])
        if isinstance(tmpl_id, list):
            tmpl_id = tmpl_id[0]
        print(f"  [PROD] {name} | cat={categ_name} | tmpl_id={tmpl_id}")

        # Add attribute line
        value_ids = [value_map[v] for v in value_names]
        attr_line_id = self.execute('product.template.attribute.line', 'create', [{
            'product_tmpl_id': tmpl_id,
            'attribute_id': attr_id,
            'value_ids': [[6, 0, value_ids]],
        }])
        if isinstance(attr_line_id, list):
            attr_line_id = attr_line_id[0]

        # Set price_extra on PTAVs
        ptavs = self.execute('product.template.attribute.value', 'search_read',
                             [[['attribute_line_id', '=', attr_line_id]]],
                             {'fields': ['id', 'name', 'product_attribute_value_id']})
        for ptav in ptavs:
            pav_name = ptav['name']
            for vname, vprice in valid_variants:
                if vname == pav_name:
                    self.execute('product.template.attribute.value', 'write',
                                 [[ptav['id']], {'price_extra': round(vprice, 2)}])
                    print(f"    variant {vname} -> price_extra={round(vprice, 2)}")
                    break

        self._existing_products.add(name)
        self.created_products.append({
            'type': 'variant',
            'name': name,
            'category': categ_name,
            'attribute': attr_name,
            'variants': valid_variants,
            'tmpl_id': tmpl_id,
        })
        return tmpl_id

    # ====== DATA PARSERS ======

    def parse_hotels(self):
        """Parse all hotel sheets and return grouped hotel data"""
        hotels = []  # (hotel_name, city, stars, [(room_type, price_per_person, price_per_night)])

        for stars in ['2 estrellas', '3 estrellas', '4 estrellas', '5 estrellas']:
            sheet_name = f'Hotel {stars}'
            ws = self.wb[sheet_name]
            star_num = stars.split()[0]

            # Group by (hotel_name, city) to avoid cross-city collisions
            current_hotels = defaultdict(lambda: {'rooms': []})

            for row in ws.iter_rows(min_row=2, values_only=True):
                tipo_hab = row[3]  # "Hotel Name - Simple"
                hotel_name_col = (row[4] or '').strip() if row[4] else None
                price_noche = row[5]
                price_persona = row[6]

                if not tipo_hab:
                    continue

                room_type = extract_room_type(tipo_hab)
                if not room_type:
                    continue

                # Prefer hotel name from tipo_hab (fixes Suites Larco 656/657/658/659 typo)
                hotel_from_tipo = extract_hotel_name_from_tipo(tipo_hab)
                hotel_name = hotel_from_tipo or hotel_name_col
                if not hotel_name:
                    continue
                if hotel_name.lower() in ('arbnb', 'none', ''):
                    continue

                city = normalize_city(row[1]) if row[1] else None
                pp = price_persona if price_persona and price_persona > 0 else 0
                pn = price_noche if price_noche and price_noche > 0 else 0

                if pp == 0 and pn == 0:
                    continue

                # Key includes city to prevent cross-city collisions
                key = (hotel_name, star_num, city or 'Otro')
                current_hotels[key]['rooms'].append((room_type, pp, pn))

            for (hname, snum, city), data in current_hotels.items():
                hotels.append((hname, city, snum, data['rooms']))

        # Detect name collisions across cities and add city suffix
        name_cities = defaultdict(set)
        for hname, city, stars, rooms in hotels:
            name_cities[hname].add(city)

        result = []
        for hname, city, stars, rooms in hotels:
            if len(name_cities[hname]) > 1:
                display_name = f"{hname} ({city})"
            else:
                display_name = hname
            result.append((display_name, city, stars, rooms))

        return result

    def parse_traslados(self):
        """Parse traslados sheet, group by route"""
        ws = self.wb['Traslados']
        routes = defaultdict(lambda: {'city': None, 'variants': []})

        for row in ws.iter_rows(min_row=2, values_only=True):
            city = normalize_city(row[1]) if row[1] else None
            route = (row[2] or '').strip()
            pax_range = (row[4] or '').strip()
            price = row[5]

            if not route or not pax_range:
                continue
            if price is None or price == 0:
                continue

            # Extract pax label from pax_range column
            pax_label = extract_pax_label(pax_range)
            if not pax_label:
                # Try to extract number from pax_range text
                m = re.search(r'(\d+(?:\s*-\s*\d+)?)\s*pax', pax_range, re.IGNORECASE)
                if m:
                    pax_label = f"{m.group(1).replace(' ', '')} pax"
                else:
                    continue

            route_clean = route.strip()
            if city:
                routes[route_clean]['city'] = city
            routes[route_clean]['variants'].append((pax_label, round(price, 2)))

        return dict(routes)

    def parse_restaurantes(self):
        """Parse restaurantes sheet"""
        ws = self.wb['Restaurantes']
        items = []
        skip_names = {'o', 'p', 'q', 'r', 'ds', '', 'OOOOOO'}

        for row in ws.iter_rows(min_row=2, values_only=True):
            name = (row[2] or '').strip()
            price = row[3]

            if not name or name in skip_names:
                continue
            if price is None or price == 0:
                continue

            items.append((name, round(price, 2)))
        return items

    def parse_boletos(self):
        """Parse boletos sheet"""
        ws = self.wb['Boletos']
        items = []

        for row in ws.iter_rows(min_row=2, values_only=True):
            name = (row[1] or '').strip()
            price = row[4]

            if not name:
                continue
            if price is None or price == 0:
                continue

            items.append((name, round(price, 2)))
        return items

    def parse_tours_compartidos(self):
        """Parse tours compartidos - some have pax variants embedded in name"""
        ws = self.wb['Tours Compartidos']
        skip_names = {'OOOOOO', '', 'o', 'p', 'q'}

        # Collect all rows
        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            name = (row[2] or '').strip()
            category = (row[1] or '').strip()
            price = row[6]

            if not name or name in skip_names:
                continue
            if price is None:
                continue  # Allow price=0 for some entries? No, skip
            if price == 0:
                continue

            rows.append((name, category, price))

        # Group: check if name has pax suffix
        grouped = defaultdict(lambda: {'category': None, 'variants': []})
        simple = []

        for name, category, price in rows:
            pax_label = extract_pax_label(name)
            if pax_label:
                base = extract_base_name(name)
                grouped[base]['category'] = category
                grouped[base]['variants'].append((pax_label, round(price, 2)))
            else:
                simple.append((name, category, round(price, 2)))

        return simple, dict(grouped)

    def parse_tours_privados(self):
        """Parse tours privados - grouped by base tour name with pax variants"""
        ws = self.wb['Tours Privados']

        grouped = defaultdict(lambda: {'category': None, 'variants': []})

        for row in ws.iter_rows(min_row=2, values_only=True):
            name = (row[2] or '').strip()
            category = (row[1] or '').strip()
            price = row[6]

            if not name:
                continue
            if price is None or price == 0:
                continue
            # Some prices are strings like '.'
            if isinstance(price, str):
                continue

            pax_label = extract_pax_label(name)
            base = extract_base_name(name)
            # Fix known typos
            base = TOUR_NAME_FIXES.get(base, base)

            if pax_label and base:
                grouped[base]['category'] = category
                grouped[base]['variants'].append((pax_label, round(price, 2)))

        return dict(grouped)

    # ====== IMPORT METHODS ======

    def import_hotels(self):
        print("\n" + "=" * 60)
        print("HOTELES")
        print("=" * 60)

        hotels = self.parse_hotels()
        for hotel_name, city, stars, rooms in hotels:
            categ = f"Agencia - Hotel {stars}\u2605 {city}"
            # Unique attribute per hotel (pattern: TIPO HABITACION HOTEL NAME)
            attr_name = f"TIPO HABITACION {hotel_name.upper()}"

            # Build variants from room data
            # Deduplicate room types (take first occurrence)
            seen = {}
            for rt, pp, pn in rooms:
                if rt not in seen:
                    seen[rt] = pp

            variants = [(rt, seen[rt]) for rt in ROOM_TYPES_ORDER if rt in seen]
            self.create_variant_product(hotel_name, categ, attr_name, variants)

    def import_traslados(self):
        print("\n" + "=" * 60)
        print("TRASLADOS")
        print("=" * 60)

        routes = self.parse_traslados()
        for route_name, data in routes.items():
            city = data['city'] or 'Otro'
            categ = f"Agencia - Traslado {city}"
            # Unique attribute per route
            attr_name = f"RANGO PAX {route_name.upper()}"

            # Deduplicate
            seen = {}
            for pax, price in data['variants']:
                if pax not in seen:
                    seen[pax] = price

            variants = [(pax, seen[pax]) for pax in PAX_RANGES_STANDARD if pax in seen]
            # Also add non-standard pax ranges
            for pax in seen:
                if pax not in PAX_RANGES_STANDARD:
                    variants.append((pax, seen[pax]))

            self.create_variant_product(route_name, categ, attr_name, variants)

    def import_restaurantes(self):
        print("\n" + "=" * 60)
        print("RESTAURANTES")
        print("=" * 60)

        items = self.parse_restaurantes()
        for name, price in items:
            self.create_simple_product(name, "Agencia - Restaurante", price)

    def import_boletos(self):
        print("\n" + "=" * 60)
        print("BOLETOS")
        print("=" * 60)

        items = self.parse_boletos()
        for name, price in items:
            self.create_simple_product(name, "Agencia - Boletos", price)

    def import_tours_compartidos(self):
        print("\n" + "=" * 60)
        print("TOURS COMPARTIDOS")
        print("=" * 60)

        simple, grouped = self.parse_tours_compartidos()

        # Simple tours (flat price)
        for name, category, price in simple:
            city = normalize_city(category)
            categ = f"Agencia - Tour Compartido {city}"
            self.create_simple_product(name, categ, price)

        # Grouped tours (pax variants)
        for base_name, data in grouped.items():
            city = normalize_city(data['category'])
            categ = f"Agencia - Tour Compartido {city}"
            # Unique attribute per tour
            attr_name = f"RANGO PAX {base_name.upper()}"
            self.create_variant_product(base_name, categ, attr_name, data['variants'])

    def import_tours_privados(self):
        print("\n" + "=" * 60)
        print("TOURS PRIVADOS")
        print("=" * 60)

        grouped = self.parse_tours_privados()
        for base_name, data in grouped.items():
            city = normalize_city(data['category'])
            categ = f"Agencia - Tour Privado {city}"
            # Unique attribute per tour
            attr_name = f"RANGO PAX {base_name.upper()}"
            self.create_variant_product(base_name, categ, attr_name, data['variants'])

    # ====== MAIN ======
    def run(self):
        mode = "DRY RUN" if DRY_RUN else "PRODUCTION"
        print(f"\n{'#' * 60}")
        print(f"  COTIZACION 2026 IMPORT - {mode}")
        print(f"{'#' * 60}")

        if not DRY_RUN:
            print("\nLoading existing data from Odoo...")

        # Import in order of priority
        self.import_restaurantes()
        self.import_boletos()
        self.import_traslados()
        self.import_hotels()
        self.import_tours_compartidos()
        self.import_tours_privados()

        # Summary
        print(f"\n{'=' * 60}")
        print("RESUMEN")
        print(f"{'=' * 60}")

        if self.created_categories:
            print(f"\nCategorias a crear ({len(self.created_categories)}):")
            for name in sorted(self.created_categories.keys()):
                print(f"  + {name}")

        simple_count = sum(1 for p in self.created_products if p['type'] == 'simple')
        variant_count = sum(1 for p in self.created_products if p['type'] == 'variant')
        total_variants = sum(len(p['variants']) for p in self.created_products if p['type'] == 'variant')

        print(f"\nProductos a crear: {len(self.created_products)}")
        print(f"  - Simples (sin variantes): {simple_count}")
        print(f"  - Con variantes: {variant_count} templates ({total_variants} variantes total)")

        if self.skipped_products:
            print(f"\nProductos omitidos: {len(self.skipped_products)}")
            for name, reason in self.skipped_products[:20]:
                print(f"  - {name}: {reason}")
            if len(self.skipped_products) > 20:
                print(f"  ... y {len(self.skipped_products) - 20} mas")

        if DRY_RUN:
            print(f"\n{'=' * 60}")
            print("DETALLE DE PRODUCTOS")
            print(f"{'=' * 60}")
            for p in self.created_products:
                if p['type'] == 'simple':
                    print(f"\n  [SIMPLE] {p['name']}")
                    print(f"    Categoria: {p['category']}")
                    print(f"    Precio: ${p['price']}")
                else:
                    print(f"\n  [VARIANTE] {p['name']}")
                    print(f"    Categoria: {p['category']}")
                    print(f"    Atributo: {p['attribute']}")
                    for vname, vprice in p['variants']:
                        print(f"      {vname}: ${vprice}")


if __name__ == '__main__':
    importer = OdooImporter()
    importer.run()
