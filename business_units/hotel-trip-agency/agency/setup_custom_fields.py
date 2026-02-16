#!/usr/bin/env python3
"""Create custom fields, supplier categories, and third-party products.

Closes gaps identified in the requirements analysis:
- Custom fields on res.partner (birthdate, medical, emergency contact)
- Custom fields on sale.order (travel date, departure city, service type, train category)
- Supplier categories by service type
- Third-party accommodation product
- Link passengers to test quotations via x_guests / x_guest_line_ids

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_custom_fields.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from defaults.categories import CATEGORIES

app = typer.Typer(help="Setup custom fields and complementary data")

# ── Custom fields to create ────────────────────────────────────────────────
PARTNER_FIELDS = [
    {
        'name': 'x_birthdate',
        'field_description': 'Date of Birth',
        'ttype': 'date',
        'model': 'res.partner',
    },
    {
        'name': 'x_medical_restrictions',
        'field_description': 'Medical / Dietary Restrictions',
        'ttype': 'text',
        'model': 'res.partner',
    },
    {
        'name': 'x_emergency_contact_name',
        'field_description': 'Emergency Contact Name',
        'ttype': 'char',
        'model': 'res.partner',
    },
    {
        'name': 'x_emergency_contact_phone',
        'field_description': 'Emergency Contact Phone',
        'ttype': 'char',
        'model': 'res.partner',
    },
]

SALE_ORDER_FIELDS = [
    {
        'name': 'x_travel_date',
        'field_description': 'Travel Date',
        'ttype': 'date',
        'model': 'sale.order',
    },
    {
        'name': 'x_departure_city',
        'field_description': 'Departure City',
        'ttype': 'char',
        'model': 'sale.order',
    },
    {
        'name': 'x_service_type',
        'field_description': 'Service Type',
        'ttype': 'selection',
        'model': 'sale.order',
        'selection_ids': [
            (0, 0, {'value': 'shared', 'name': 'Shared', 'sequence': 1}),
            (0, 0, {'value': 'private', 'name': 'Private', 'sequence': 2}),
        ],
    },
    {
        'name': 'x_train_category',
        'field_description': 'Train Category',
        'ttype': 'char',
        'model': 'sale.order',
    },
]

# ── Supplier categories ────────────────────────────────────────────────────
SUPPLIER_CATEGORIES = [
    'Proveedor - Transporte',
    'Proveedor - Tren',
    'Proveedor - Guía',
    'Proveedor - Hotel',
    'Proveedor - Restaurante',
    'Proveedor - Otros',
]

# ── Accommodation products ────────────────────────────────────────────────
# Purchase-only: for third-party hotel expenses
EXTERNAL_HOTEL_PRODUCT = {
    'name': 'Alojamiento Externo (Tercerizado)',
    'type': 'service',
    'purchase_ok': True,
    'sale_ok': False,
    'list_price': 0.0,
    'standard_price': 0.0,
}

# Sale product: generic own-hotel accommodation for agency quotations
# Price is set per quotation (varies by tour). Room assigned operationally from Hotel module.
OWN_HOTEL_PRODUCT = {
    'name': 'Alojamiento Propio',
    'type': 'service',
    'sale_ok': True,
    'purchase_ok': False,
    'list_price': 0.0,
    'description_sale': 'Precio por noche, habitación asignada operativamente',
}

# Generic tour service product: used as placeholder in PO lines generated from Biblia Operativa
TOUR_SERVICE_PRODUCT = {
    'name': 'Servicio de Tour',
    'default_code': 'SRV-TOUR',
    'type': 'service',
    'purchase_ok': True,
    'sale_ok': False,
    'list_price': 0.0,
    'standard_price': 0.0,
}

# ── Passenger data for custom field population ─────────────────────────────
COUNTRIES = {'US': 233, 'MX': 156, 'DE': 57, 'JP': 113, 'AR': 10}

PASSENGER_EXTRA_DATA = {
    'John Miller': {
        'x_nationality': COUNTRIES['US'],
        'x_document_type': 'Passport',
        'x_document_number': 'M12345678',
        'x_birthdate': '1985-03-15',
        'x_medical_restrictions': 'None',
        'x_emergency_contact_name': 'Mary Miller',
        'x_emergency_contact_phone': '+1 555 111 2222',
    },
    'Sarah Miller': {
        'x_nationality': COUNTRIES['US'],
        'x_document_type': 'Passport',
        'x_document_number': 'M12345679',
        'x_birthdate': '1987-07-22',
        'x_medical_restrictions': 'Vegetarian diet',
        'x_emergency_contact_name': 'John Miller',
        'x_emergency_contact_phone': '+1 555 234 5678',
    },
    'María García López': {
        'x_nationality': COUNTRIES['MX'],
        'x_document_type': 'Passport',
        'x_document_number': 'G98765432',
        'x_birthdate': '1990-11-08',
        'x_medical_restrictions': 'Peanut allergy - no peanuts or tree nuts',
        'x_emergency_contact_name': 'Carlos García',
        'x_emergency_contact_phone': '+52 55 1234 5678',
    },
    'Hans Müller': {
        'x_nationality': COUNTRIES['DE'],
        'x_document_type': 'Passport',
        'x_document_number': 'HM4567890',
        'x_birthdate': '1978-05-20',
        'x_medical_restrictions': 'None',
        'x_emergency_contact_name': 'Klaus Müller',
        'x_emergency_contact_phone': '+49 89 9876 5432',
    },
    'Claudia Müller': {
        'x_nationality': COUNTRIES['DE'],
        'x_document_type': 'Passport',
        'x_document_number': 'CM4567891',
        'x_birthdate': '1980-09-12',
        'x_medical_restrictions': 'Gluten-free diet',
        'x_emergency_contact_name': 'Hans Müller',
        'x_emergency_contact_phone': '+49 89 1234 5678',
    },
    'Takeshi Tanaka': {
        'x_nationality': COUNTRIES['JP'],
        'x_document_type': 'Passport',
        'x_document_number': 'TT1234567',
        'x_birthdate': '1982-01-30',
        'x_medical_restrictions': 'No beef',
        'x_emergency_contact_name': 'Kenji Tanaka',
        'x_emergency_contact_phone': '+81 3 9876 5432',
    },
    'Yuki Tanaka': {
        'x_nationality': COUNTRIES['JP'],
        'x_document_type': 'Passport',
        'x_document_number': 'YT1234568',
        'x_birthdate': '1984-06-15',
        'x_medical_restrictions': 'No beef',
        'x_emergency_contact_name': 'Takeshi Tanaka',
        'x_emergency_contact_phone': '+81 90 1234 5678',
    },
    'Roberto Fernández': {
        'x_nationality': COUNTRIES['AR'],
        'x_document_type': 'ID card',
        'x_document_number': '34567890',
        'x_birthdate': '1975-12-03',
        'x_medical_restrictions': 'Controlled hypertension (own medication)',
        'x_emergency_contact_name': 'Luis Fernández',
        'x_emergency_contact_phone': '+54 11 9876 5432',
    },
    'Ana Fernández': {
        'x_nationality': COUNTRIES['AR'],
        'x_document_type': 'ID card',
        'x_document_number': '34567891',
        'x_birthdate': '1978-08-19',
        'x_medical_restrictions': 'None',
        'x_emergency_contact_name': 'Roberto Fernández',
        'x_emergency_contact_phone': '+54 11 4567 8901',
    },
}

# ── Quotation → Passengers mapping ─────────────────────────────────────────
QUOTATION_PASSENGERS = {
    'TEST-HONEYMOON-MILLER': {
        'passengers': ['John Miller', 'Sarah Miller'],
        'x_travel_date': '2026-04-15',
        'x_departure_city': 'Lima',
        'x_service_type': 'private',
        'x_train_category': '',
    },
    'TEST-SOLO-GARCIA': {
        'passengers': ['María García López'],
        'x_travel_date': '2026-03-20',
        'x_departure_city': 'Ciudad de México',
        'x_service_type': 'shared',
        'x_train_category': '',
    },
    'TEST-FAMILY-MULLER': {
        'passengers': ['Hans Müller', 'Claudia Müller'],
        'x_travel_date': '2026-05-01',
        'x_departure_city': 'Frankfurt',
        'x_service_type': 'private',
        'x_train_category': 'Expedition',
    },
    'TEST-CULTURAL-TANAKA': {
        'passengers': ['Takeshi Tanaka', 'Yuki Tanaka'],
        'x_travel_date': '2026-04-25',
        'x_departure_city': 'Tokyo',
        'x_service_type': 'shared',
        'x_train_category': 'Vistadome',
    },
    'TEST-ANIVERSARIO-FERNANDEZ': {
        'passengers': ['Roberto Fernández', 'Ana Fernández'],
        'x_travel_date': '2026-03-10',
        'x_departure_city': 'Buenos Aires',
        'x_service_type': 'private',
        'x_train_category': 'Vistadome',
    },
}


def _get_model_id(client, model_name):
    """Get ir.model id for a given model name."""
    result = client.search_read('ir.model',
        domain=[['model', '=', model_name]],
        fields=['id'], limit=1)
    return result[0]['id'] if result else False


def _field_exists(client, model_name, field_name):
    """Check if a field already exists on a model."""
    result = client.search_read('ir.model.fields',
        domain=[['model', '=', model_name], ['name', '=', field_name]],
        fields=['id'], limit=1)
    return result[0]['id'] if result else False


def _create_custom_field(client, field_def):
    """Create a custom field via ir.model.fields if it doesn't exist."""
    model_name = field_def['model']
    field_name = field_def['name']

    existing_id = _field_exists(client, model_name, field_name)
    if existing_id:
        return existing_id, False

    model_id = _get_model_id(client, model_name)
    if not model_id:
        return False, False

    vals = {
        'model_id': model_id,
        'name': field_name,
        'field_description': field_def['field_description'],
        'ttype': field_def['ttype'],
        'store': True,
    }
    if 'selection_ids' in field_def:
        vals['selection_ids'] = field_def['selection_ids']

    result = client.execute('ir.model.fields', 'create', [vals])
    field_id = result[0] if isinstance(result, list) else result
    return field_id, True


@app.command()
def setup(
    test_data: bool = typer.Option(False, "--test-data", help="Also populate test passenger data and link to test quotations"),
):
    """Create custom fields, supplier categories, and third-party products."""
    client = OdooClient()
    client.connect()
    created = 0

    typer.secho("=" * 70, bold=True)
    typer.secho("  CUSTOM FIELDS & CATEGORIES SETUP", bold=True)
    typer.secho("=" * 70, bold=True)

    # ── 1. Custom fields on res.partner ────────────────────────────────
    typer.secho("\n1. Custom fields on res.partner", bold=True)
    for fdef in PARTNER_FIELDS:
        fid, is_new = _create_custom_field(client, fdef)
        status = 'CREATED' if is_new else 'OK'
        color = typer.colors.GREEN
        typer.secho(f"  [{status}] {fdef['name']}: {fdef['ttype']} - \"{fdef['field_description']}\"",
                    fg=color)
        if is_new:
            created += 1

    # ── 2. Custom fields on sale.order ─────────────────────────────────
    typer.secho("\n2. Custom fields on sale.order", bold=True)
    for fdef in SALE_ORDER_FIELDS:
        fid, is_new = _create_custom_field(client, fdef)
        status = 'CREATED' if is_new else 'OK'
        color = typer.colors.GREEN
        typer.secho(f"  [{status}] {fdef['name']}: {fdef['ttype']} - \"{fdef['field_description']}\"",
                    fg=color)
        if is_new:
            created += 1

    # ── 3. Supplier categories ─────────────────────────────────────────
    typer.secho("\n3. Supplier categories (partner tags)", bold=True)
    for cat_name in SUPPLIER_CATEGORIES:
        existing = client.search_read('res.partner.category',
            domain=[['name', '=', cat_name]], fields=['id'], limit=1)
        if existing:
            typer.secho(f"  [OK] {cat_name} (id={existing[0]['id']})", fg=typer.colors.GREEN)
        else:
            result = client.execute('res.partner.category', 'create',
                                    [{'name': cat_name}])
            cat_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] {cat_name} (id={cat_id})", fg=typer.colors.GREEN)
            created += 1

    # ── 4. Third-party accommodation product ───────────────────────────
    typer.secho("\n4. Third-party accommodation product", bold=True)
    prod_name = EXTERNAL_HOTEL_PRODUCT['name']
    existing = client.search_read('product.template',
        domain=[['name', '=', prod_name]], fields=['id'], limit=1)
    if existing:
        typer.secho(f"  [OK] {prod_name} (id={existing[0]['id']})", fg=typer.colors.GREEN)
    else:
        result = client.execute('product.template', 'create', [{
            'name': prod_name,
            'type': EXTERNAL_HOTEL_PRODUCT['type'],
            'purchase_ok': EXTERNAL_HOTEL_PRODUCT['purchase_ok'],
            'sale_ok': EXTERNAL_HOTEL_PRODUCT['sale_ok'],
            'list_price': EXTERNAL_HOTEL_PRODUCT['list_price'],
            'standard_price': EXTERNAL_HOTEL_PRODUCT['standard_price'],
            'categ_id': CATEGORIES['services'],
        }])
        pid = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] {prod_name} (id={pid})", fg=typer.colors.GREEN)
        created += 1

    # ── 5. Own-hotel accommodation product (for agency quotations) ────
    typer.secho("\n5. Own-hotel accommodation product (for quotations)", bold=True)
    own_name = OWN_HOTEL_PRODUCT['name']
    existing = client.search_read('product.template',
        domain=[['name', '=', own_name]], fields=['id'], limit=1)
    if existing:
        typer.secho(f"  [OK] {own_name} (id={existing[0]['id']})", fg=typer.colors.GREEN)
    else:
        result = client.execute('product.template', 'create', [{
            'name': own_name,
            'type': OWN_HOTEL_PRODUCT['type'],
            'sale_ok': OWN_HOTEL_PRODUCT['sale_ok'],
            'purchase_ok': OWN_HOTEL_PRODUCT['purchase_ok'],
            'list_price': OWN_HOTEL_PRODUCT['list_price'],
            'description_sale': OWN_HOTEL_PRODUCT['description_sale'],
            'categ_id': CATEGORIES['services'],
        }])
        pid = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] {own_name} (id={pid})", fg=typer.colors.GREEN)
        created += 1

    # ── 6. Tour service product (for PO lines from Biblia Operativa) ──
    typer.secho("\n6. Tour service product (for PO lines)", bold=True)
    tour_name = TOUR_SERVICE_PRODUCT['name']
    existing = client.search_read('product.template',
        domain=[['name', '=', tour_name]], fields=['id'], limit=1)
    if existing:
        typer.secho(f"  [OK] {tour_name} (id={existing[0]['id']})", fg=typer.colors.GREEN)
    else:
        result = client.execute('product.template', 'create', [{
            'name': tour_name,
            'default_code': TOUR_SERVICE_PRODUCT['default_code'],
            'type': TOUR_SERVICE_PRODUCT['type'],
            'purchase_ok': TOUR_SERVICE_PRODUCT['purchase_ok'],
            'sale_ok': TOUR_SERVICE_PRODUCT['sale_ok'],
            'list_price': TOUR_SERVICE_PRODUCT['list_price'],
            'standard_price': TOUR_SERVICE_PRODUCT['standard_price'],
            'categ_id': CATEGORIES['services'],
        }])
        pid = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] {tour_name} (id={pid})", fg=typer.colors.GREEN)
        created += 1

    # ── 7-8. Test data (only with --test-data flag) ────────────────────
    if not test_data:
        typer.secho("\n[SKIP] Test data (use --test-data to populate passengers and link quotations)", fg=typer.colors.YELLOW)
    else:
        typer.secho("\n6. Populate test passenger custom fields", bold=True)
        for pax_name, data in PASSENGER_EXTRA_DATA.items():
            partner = client.search_read('res.partner',
                domain=[['name', '=', pax_name]],
                fields=['id'], limit=1)
            if not partner:
                typer.secho(f"  [SKIP] {pax_name}: not found", fg=typer.colors.YELLOW)
                continue

            pid = partner[0]['id']
            try:
                client.execute('res.partner', 'write', [pid], data)
                typer.secho(f"  [OK] {pax_name}: fields updated", fg=typer.colors.GREEN)
            except Exception as e:
                typer.secho(f"  [ERROR] {pax_name}: {str(e)[:80]}", fg=typer.colors.RED)

        typer.secho("\n7. Link test passengers to quotations", bold=True)
        for ref, qdata in QUOTATION_PASSENGERS.items():
            so = client.search_read('sale.order',
                domain=[['client_order_ref', '=', ref]],
                fields=['id', 'name', 'x_guests', 'x_guest_line_ids'], limit=1)
            if not so:
                typer.secho(f"  [SKIP] {ref}: quotation not found", fg=typer.colors.YELLOW)
                continue

            so_id = so[0]['id']
            so_name = so[0]['name']

            pax_ids = []
            for pax_name in qdata['passengers']:
                partner = client.search_read('res.partner',
                    domain=[['name', '=', pax_name]],
                    fields=['id'], limit=1)
                if partner:
                    pax_ids.append(partner[0]['id'])

            so_vals = {}
            if qdata.get('x_travel_date'):
                so_vals['x_travel_date'] = qdata['x_travel_date']
            if qdata.get('x_departure_city'):
                so_vals['x_departure_city'] = qdata['x_departure_city']
            if qdata.get('x_service_type'):
                so_vals['x_service_type'] = qdata['x_service_type']
            if qdata.get('x_train_category'):
                so_vals['x_train_category'] = qdata['x_train_category']

            if pax_ids:
                so_vals['x_guests'] = [(6, 0, pax_ids)]

            if so_vals:
                try:
                    client.execute('sale.order', 'write', [so_id], so_vals)
                    typer.secho(
                        f"  [OK] {so_name} ({ref}): {len(pax_ids)} passengers linked, "
                        f"travel={qdata.get('x_travel_date', '-')}, "
                        f"city={qdata.get('x_departure_city', '-')}, "
                        f"type={qdata.get('x_service_type', '-')}",
                        fg=typer.colors.GREEN)
                except Exception as e:
                    typer.secho(f"  [ERROR] {so_name}: {str(e)[:100]}", fg=typer.colors.RED)

            existing_lines = client.search_read('x_guests_line',
                domain=[['x_sale_order_id', '=', so_id]],
                fields=['id', 'x_guest_partner_id'], limit=50)
            existing_pax = {
                line['x_guest_partner_id'][0]
                for line in existing_lines
                if line.get('x_guest_partner_id')
            }

            for i, pax_id in enumerate(pax_ids):
                if pax_id in existing_pax:
                    continue
                try:
                    pax_data = client.search_read('res.partner',
                        domain=[['id', '=', pax_id]],
                        fields=['name'], limit=1)
                    pax_display = pax_data[0]['name'] if pax_data else str(pax_id)
                    client.execute('x_guests_line', 'create', [{
                        'x_sale_order_id': so_id,
                        'x_guest_partner_id': pax_id,
                        'x_name': pax_display,
                        'x_sequence': (i + 1) * 10,
                    }])
                    typer.secho(f"    [+] Guest line: {pax_display}", fg=typer.colors.CYAN)
                except Exception as e:
                    typer.secho(f"    [ERROR] Guest line for {pax_id}: {str(e)[:80]}",
                                fg=typer.colors.RED)

    # ── Summary ────────────────────────────────────────────────────────
    typer.secho("\n" + "=" * 70, bold=True)
    typer.secho(f"  {created} new records created", fg=typer.colors.BLUE, bold=True)
    typer.secho("=" * 70, bold=True)

    typer.secho("\nCustom fields:", fg=typer.colors.CYAN)
    typer.secho("  res.partner: x_birthdate, x_medical_restrictions,", fg=typer.colors.CYAN)
    typer.secho("               x_emergency_contact_name, x_emergency_contact_phone", fg=typer.colors.CYAN)
    typer.secho("  sale.order:  x_travel_date, x_departure_city,", fg=typer.colors.CYAN)
    typer.secho("               x_service_type, x_train_category", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
