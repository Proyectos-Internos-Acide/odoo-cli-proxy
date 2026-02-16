#!/usr/bin/env python3
"""Create realistic test data: passengers, UTM sources, and quotations.

Creates sample customers and quotations to test the full agency flow:
  CRM Lead -> Quotation -> Confirm -> Project -> Operations

Usage:
    uv run python business_units/hotel-trip-agency/agency/create_test_quotations.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient

app = typer.Typer(help="Create test quotations for travel agency")

# ── Reference IDs ──────────────────────────────────────────────────────────
COUNTRIES = {'US': 233, 'MX': 156, 'DE': 57, 'JP': 113, 'AR': 10, 'PE': 173}
ID_TYPES = {'passport': 2, 'dni': 5, 'foreign_id': 3}
PRICELIST = {'PEN': 1, 'USD': 2}
PAYMENT_TERMS = {'immediate': 1, '30pct_60d': 8}

# Product IDs (from database)
PRODUCTS = {
    'city_tour': 75,           # City Tour Cusco (service, task_in_project)
    'palcoyo': 142,            # Palcoyo (service, project_only)
    'kit_cusco_3d2n': 154,     # Cusco 3D/2N Kit (service, task_in_project)
    'airport_shuttle': 14,     # Airport Shuttle (service, $25)
    'transport_airport': 149,  # Transportation from Airport (service)
    'apartment_301': 152,      # Apartment 301 ($70/night)
    'apartment_501': 120,      # Apartment 501 ($70/night)
    'deluxe_suite': 27,        # Deluxe Suite ($195/night)
    'deluxe_room': 21,         # Deluxe Room ($125/night)
    'breakfast': 10,           # Breakfast ($15)
    'champagne': 13,           # Champagne Bottle ($75)
}

# ── Test Passengers ────────────────────────────────────────────────────────
PASSENGERS = [
    {
        'name': 'John Miller',
        'email': 'john.miller@example.com',
        'phone': '+1 555 234 5678',
        'country_id': COUNTRIES['US'],
        'lang': 'en_US',
        'vat': 'US-PASS-M12345678',
        'l10n_latam_identification_type_id': ID_TYPES['passport'],
        'comment': '<p><b>Passenger Info:</b><br/>'
                   'DOB: 1985-03-15<br/>'
                   'Nationality: American<br/>'
                   'Emergency Contact: Mary Miller +1 555 111 2222<br/>'
                   'Medical: None<br/>'
                   'Dietary: No restrictions<br/>'
                   '<b>Notes:</b> Honeymoon trip with wife Sarah. '
                   'Request champagne on arrival.</p>',
        'category_id': [],  # will be set after tag creation
    },
    {
        'name': 'Sarah Miller',
        'email': 'sarah.miller@example.com',
        'phone': '+1 555 234 5679',
        'country_id': COUNTRIES['US'],
        'lang': 'en_US',
        'vat': 'US-PASS-M12345679',
        'l10n_latam_identification_type_id': ID_TYPES['passport'],
        'comment': '<p><b>Passenger Info:</b><br/>'
                   'DOB: 1987-07-22<br/>'
                   'Nationality: American<br/>'
                   'Emergency Contact: John Miller +1 555 234 5678<br/>'
                   'Medical: None<br/>'
                   'Dietary: Vegetarian</p>',
        'category_id': [],
        '_companion_of': 'John Miller',
    },
    {
        'name': 'María García López',
        'email': 'maria.garcia@example.com',
        'phone': '+52 55 8765 4321',
        'country_id': COUNTRIES['MX'],
        'lang': 'es_419',
        'vat': 'MX-PASS-G98765432',
        'l10n_latam_identification_type_id': ID_TYPES['passport'],
        'comment': '<p><b>Info Pasajero:</b><br/>'
                   'Fecha Nac.: 1990-11-08<br/>'
                   'Nacionalidad: Mexicana<br/>'
                   'Contacto Emergencia: Carlos García +52 55 1234 5678<br/>'
                   'Médico: Alergia al maní<br/>'
                   'Alimentario: Sin maní ni frutos secos<br/>'
                   '<b>Notas:</b> Viajera sola, fotógrafa profesional. '
                   'Interesada en ruinas arqueológicas.</p>',
        'category_id': [],
    },
    {
        'name': 'Hans Müller',
        'email': 'hans.mueller@example.de',
        'phone': '+49 89 1234 5678',
        'country_id': COUNTRIES['DE'],
        'lang': 'en_US',
        'vat': 'DE-PASS-HM4567890',
        'l10n_latam_identification_type_id': ID_TYPES['passport'],
        'comment': '<p><b>Passenger Info:</b><br/>'
                   'DOB: 1978-05-20<br/>'
                   'Nationality: German<br/>'
                   'Emergency Contact: Klaus Müller +49 89 9876 5432<br/>'
                   'Medical: None<br/>'
                   'Dietary: No restrictions<br/>'
                   '<b>Notes:</b> Family trip (4 pax). Wife Claudia, '
                   'children Max (12) and Sophie (9). '
                   'Need child-friendly activities.</p>',
        'category_id': [],
    },
    {
        'name': 'Claudia Müller',
        'email': 'claudia.mueller@example.de',
        'phone': '+49 89 1234 5679',
        'country_id': COUNTRIES['DE'],
        'lang': 'en_US',
        'l10n_latam_identification_type_id': ID_TYPES['passport'],
        'comment': '<p><b>Passenger Info:</b><br/>'
                   'DOB: 1980-09-12<br/>'
                   'Nationality: German<br/>'
                   'Medical: None<br/>'
                   'Dietary: Gluten-free</p>',
        'category_id': [],
        '_companion_of': 'Hans Müller',
    },
    {
        'name': 'Takeshi Tanaka',
        'email': 'takeshi.tanaka@example.jp',
        'phone': '+81 90 1234 5678',
        'country_id': COUNTRIES['JP'],
        'lang': 'en_US',
        'vat': 'JP-PASS-TT1234567',
        'l10n_latam_identification_type_id': ID_TYPES['passport'],
        'comment': '<p><b>Passenger Info:</b><br/>'
                   'DOB: 1982-01-30<br/>'
                   'Nationality: Japanese<br/>'
                   'Emergency Contact: Kenji Tanaka +81 3 9876 5432<br/>'
                   'Medical: None<br/>'
                   'Dietary: No beef<br/>'
                   '<b>Notes:</b> Traveling with wife Yuki. '
                   'Very interested in history and culture. '
                   'Speaks basic Spanish.</p>',
        'category_id': [],
    },
    {
        'name': 'Yuki Tanaka',
        'email': 'yuki.tanaka@example.jp',
        'phone': '+81 90 1234 5679',
        'country_id': COUNTRIES['JP'],
        'lang': 'en_US',
        'l10n_latam_identification_type_id': ID_TYPES['passport'],
        'comment': '<p><b>Passenger Info:</b><br/>'
                   'DOB: 1984-06-15<br/>'
                   'Nationality: Japanese<br/>'
                   'Medical: None<br/>'
                   'Dietary: No beef</p>',
        'category_id': [],
        '_companion_of': 'Takeshi Tanaka',
    },
    {
        'name': 'Roberto Fernández',
        'email': 'roberto.fernandez@example.ar',
        'phone': '+54 11 4567 8901',
        'country_id': COUNTRIES['AR'],
        'lang': 'es_419',
        'vat': '20-34567890-5',
        'l10n_latam_identification_type_id': ID_TYPES['dni'],
        'comment': '<p><b>Info Pasajero:</b><br/>'
                   'Fecha Nac.: 1975-12-03<br/>'
                   'Nacionalidad: Argentina<br/>'
                   'Contacto Emergencia: Luis Fernández +54 11 9876 5432<br/>'
                   'Médico: Hipertensión controlada (medicación propia)<br/>'
                   'Alimentario: Sin restricciones<br/>'
                   '<b>Notas:</b> Viaje aniversario con esposa Ana. '
                   'Prefieren servicio privado. Presupuesto medio.</p>',
        'category_id': [],
    },
    {
        'name': 'Ana Fernández',
        'email': 'ana.fernandez@example.ar',
        'phone': '+54 11 4567 8902',
        'country_id': COUNTRIES['AR'],
        'lang': 'es_419',
        'vat': '27-34567891-3',
        'l10n_latam_identification_type_id': ID_TYPES['dni'],
        'comment': '<p><b>Info Pasajero:</b><br/>'
                   'Fecha Nac.: 1978-08-19<br/>'
                   'Nacionalidad: Argentina<br/>'
                   'Médico: Ninguno<br/>'
                   'Alimentario: Sin restricciones</p>',
        'category_id': [],
        '_companion_of': 'Roberto Fernández',
    },
]

# ── Test Quotations ────────────────────────────────────────────────────────
QUOTATIONS = [
    {
        'ref': 'TEST-HONEYMOON-MILLER',
        'partner_name': 'John Miller',
        'pricelist_id': PRICELIST['USD'],
        'payment_term_id': PAYMENT_TERMS['30pct_60d'],
        'source_name': 'Instagram',
        'medium_name': 'Website',
        'note': '<p>Honeymoon Package - Special attention requested.<br/>'
                'Champagne on arrival. Late checkout if possible.<br/>'
                'Transfer: Airport pickup included.<br/>'
                'Passengers: John Miller & Sarah Miller</p>',
        'lines': [
            {'product_id': PRODUCTS['kit_cusco_3d2n'], 'qty': 2, 'price': 500.00,
             'name': 'Cusco 3D/2N - Paquete Completo (por persona)'},
            {'product_id': PRODUCTS['deluxe_suite'], 'qty': 2, 'price': 195.00,
             'name': 'Deluxe Suite - 2 noches (upgrade honeymoon)'},
            {'product_id': PRODUCTS['airport_shuttle'], 'qty': 2, 'price': 25.00,
             'name': 'Shuttle Aeropuerto (ida y vuelta)'},
            {'product_id': PRODUCTS['champagne'], 'qty': 1, 'price': 75.00,
             'name': 'Champagne de bienvenida'},
            {'product_id': PRODUCTS['breakfast'], 'qty': 4, 'price': 15.00,
             'name': 'Desayuno buffet (2 pax x 2 días)'},
        ],
    },
    {
        'ref': 'TEST-SOLO-GARCIA',
        'partner_name': 'María García López',
        'pricelist_id': PRICELIST['USD'],
        'payment_term_id': PAYMENT_TERMS['immediate'],
        'source_name': 'WhatsApp',
        'medium_name': 'Phone',
        'sale_order_template_id': 1,  # Paquete Cusco Prueba
        'note': '<p>Viajera sola - Servicio compartido.<br/>'
                'Interesada en fotografía y ruinas.<br/>'
                'Alergia al maní - coordinar con restaurantes.<br/>'
                'Canal: WhatsApp directo.<br/>'
                'Pasajero: María García López</p>',
        'lines': [
            {'product_id': PRODUCTS['city_tour'], 'qty': 1, 'price': 35.00,
             'name': 'City Tour Cusco - Servicio compartido'},
            {'product_id': PRODUCTS['palcoyo'], 'qty': 1, 'price': 45.00,
             'name': 'Excursión Palcoyo - Montaña de Colores'},
            {'product_id': PRODUCTS['apartment_301'], 'qty': 2, 'price': 70.00,
             'name': 'Apartment 301 - 2 noches'},
            {'product_id': PRODUCTS['airport_shuttle'], 'qty': 2, 'price': 25.00,
             'name': 'Shuttle Aeropuerto (ida y vuelta)'},
            {'product_id': PRODUCTS['breakfast'], 'qty': 2, 'price': 15.00,
             'name': 'Desayuno continental (2 días)'},
        ],
    },
    {
        'ref': 'TEST-FAMILY-MULLER',
        'partner_name': 'Hans Müller',
        'pricelist_id': PRICELIST['USD'],
        'payment_term_id': PAYMENT_TERMS['30pct_60d'],
        'source_name': 'Search engine',
        'medium_name': 'Website',
        'note': '<p>Family trip (4 pax: 2 adults + 2 children).<br/>'
                'Children ages: Max 12, Sophie 9.<br/>'
                'Need child-friendly activities.<br/>'
                'Claudia is gluten-free - coordinate meals.<br/>'
                'Two rooms needed (parents + children).<br/>'
                'Passengers: Hans, Claudia, Max, Sophie Müller</p>',
        'lines': [
            {'product_id': PRODUCTS['city_tour'], 'qty': 4, 'price': 35.00,
             'name': 'City Tour Cusco - 4 pax (2 adultos + 2 niños)'},
            {'product_id': PRODUCTS['palcoyo'], 'qty': 4, 'price': 45.00,
             'name': 'Excursión Palcoyo - 4 pax'},
            {'product_id': PRODUCTS['apartment_501'], 'qty': 3, 'price': 70.00,
             'name': 'Apartment 501 - Habitación familiar (3 noches)'},
            {'product_id': PRODUCTS['deluxe_room'], 'qty': 3, 'price': 125.00,
             'name': 'Deluxe Room - Habitación niños (3 noches)'},
            {'product_id': PRODUCTS['airport_shuttle'], 'qty': 4, 'price': 25.00,
             'name': 'Shuttle Aeropuerto x4 (ida)'},
            {'product_id': PRODUCTS['transport_airport'], 'qty': 4, 'price': 15.00,
             'name': 'Transporte Aeropuerto x4 (vuelta)'},
            {'product_id': PRODUCTS['breakfast'], 'qty': 12, 'price': 15.00,
             'name': 'Desayuno buffet (4 pax x 3 días)'},
        ],
    },
    {
        'ref': 'TEST-CULTURAL-TANAKA',
        'partner_name': 'Takeshi Tanaka',
        'pricelist_id': PRICELIST['USD'],
        'payment_term_id': PAYMENT_TERMS['immediate'],
        'source_name': 'Referral',
        'medium_name': 'Email',
        'note': '<p>Cultural package for Japanese couple.<br/>'
                'Very interested in Inca history.<br/>'
                'No beef in meals - coordinate with restaurants.<br/>'
                'Basic Spanish speakers.<br/>'
                'Referred by previous client.<br/>'
                'Passengers: Takeshi & Yuki Tanaka</p>',
        'lines': [
            {'product_id': PRODUCTS['kit_cusco_3d2n'], 'qty': 2, 'price': 500.00,
             'name': 'Cusco 3D/2N - Paquete Completo (por persona)'},
            {'product_id': PRODUCTS['city_tour'], 'qty': 2, 'price': 35.00,
             'name': 'City Tour Cusco adicional - Barrio San Blas (2 pax)'},
            {'product_id': PRODUCTS['airport_shuttle'], 'qty': 2, 'price': 25.00,
             'name': 'Shuttle Aeropuerto (ida y vuelta)'},
        ],
    },
    {
        'ref': 'TEST-ANIVERSARIO-FERNANDEZ',
        'partner_name': 'Roberto Fernández',
        'pricelist_id': PRICELIST['PEN'],
        'payment_term_id': PAYMENT_TERMS['30pct_60d'],
        'source_name': 'WhatsApp',
        'medium_name': 'Phone',
        'note': '<p>Viaje de aniversario - Servicio privado.<br/>'
                'Roberto tiene hipertensión controlada.<br/>'
                'Prefieren servicio privado por comodidad.<br/>'
                'Presupuesto en soles peruanos.<br/>'
                'Canal: WhatsApp directo.<br/>'
                'Pasajeros: Roberto & Ana Fernández</p>',
        'lines': [
            {'product_id': PRODUCTS['city_tour'], 'qty': 2, 'price': 130.00,
             'name': 'City Tour Cusco PRIVADO - 2 pax'},
            {'product_id': PRODUCTS['palcoyo'], 'qty': 2, 'price': 170.00,
             'name': 'Excursión Palcoyo PRIVADO - 2 pax'},
            {'product_id': PRODUCTS['apartment_301'], 'qty': 2, 'price': 260.00,
             'name': 'Apartment 301 - 2 noches (precio en soles)'},
            {'product_id': PRODUCTS['airport_shuttle'], 'qty': 2, 'price': 95.00,
             'name': 'Shuttle Aeropuerto (ida y vuelta, en soles)'},
            {'product_id': PRODUCTS['breakfast'], 'qty': 4, 'price': 55.00,
             'name': 'Desayuno buffet (2 pax x 2 días, en soles)'},
        ],
    },
]


def _get_or_create(client, model, domain, vals, label=""):
    """Find existing record or create new one. Returns record ID."""
    existing = client.search_read(model, domain=domain, fields=['id'], limit=1)
    if existing:
        return existing[0]['id'], False
    result = client.execute(model, 'create', [vals])
    rid = result[0] if isinstance(result, list) else result
    return rid, True


def _get_utm_source(client, name):
    """Get or create UTM source by name."""
    existing = client.search_read('utm.source', domain=[['name', '=', name]],
                                  fields=['id'], limit=1)
    if existing:
        return existing[0]['id']
    result = client.execute('utm.source', 'create', [{'name': name}])
    return result[0] if isinstance(result, list) else result


def _get_utm_medium(client, name):
    """Get UTM medium by name (these are predefined)."""
    existing = client.search_read('utm.medium', domain=[['name', '=', name]],
                                  fields=['id'], limit=1)
    return existing[0]['id'] if existing else False


@app.command()
def create():
    """Create test passengers and quotations for the travel agency."""
    client = OdooClient()
    client.connect()
    created_count = 0

    typer.secho("=" * 70, bold=True)
    typer.secho("  TEST DATA: PASSENGERS & QUOTATIONS", bold=True)
    typer.secho("=" * 70, bold=True)

    # ── 1. Create UTM Sources ──────────────────────────────────────────
    typer.secho("\n1. UTM Sources (sales channels)", bold=True)
    for src_name in ['WhatsApp', 'Instagram']:
        src_id = _get_utm_source(client, src_name)
        typer.secho(f"  [OK] {src_name} (id={src_id})", fg=typer.colors.GREEN)

    # ── 2. Create Partner Tags ─────────────────────────────────────────
    typer.secho("\n2. Partner tags", bold=True)
    tag_ids = {}
    for tag_name in ['Pasajero', 'VIP']:
        tag_id, is_new = _get_or_create(client, 'res.partner.category',
            domain=[['name', '=', tag_name]],
            vals={'name': tag_name},
            label=tag_name)
        tag_ids[tag_name] = tag_id
        status = 'CREATED' if is_new else 'OK'
        typer.secho(f"  [{status}] {tag_name} (id={tag_id})", fg=typer.colors.GREEN)
        if is_new:
            created_count += 1

    # ── 3. Create Passengers ───────────────────────────────────────────
    typer.secho("\n3. Test passengers", bold=True)
    partner_ids = {}

    for pax in PASSENGERS:
        pax_name = pax['name']
        partner_id, is_new = _get_or_create(client, 'res.partner',
            domain=[['name', '=', pax_name], ['email', '=', pax.get('email', '')]],
            vals={
                'name': pax_name,
                'email': pax.get('email', ''),
                'phone': pax.get('phone', ''),
                'country_id': pax.get('country_id', False),
                'lang': pax.get('lang', 'en_US'),
                'vat': pax.get('vat', ''),
                'l10n_latam_identification_type_id': pax.get(
                    'l10n_latam_identification_type_id', False),
                'comment': pax.get('comment', ''),
                'category_id': [(6, 0, [tag_ids['Pasajero']])],
                'customer_rank': 1,
            })
        partner_ids[pax_name] = partner_id

        if is_new:
            typer.secho(f"  [CREATED] {pax_name} (id={partner_id})", fg=typer.colors.GREEN)
            created_count += 1
        else:
            typer.secho(f"  [OK] {pax_name} (id={partner_id})", fg=typer.colors.GREEN)

        # Link companions as children of main contact
        companion_of = pax.get('_companion_of')
        if companion_of and companion_of in partner_ids:
            parent_id = partner_ids[companion_of]
            try:
                client.execute('res.partner', 'write', [partner_id],
                               {'parent_id': parent_id})
            except Exception:
                pass  # might fail if already set

    # Mark VIP passengers
    for vip_name in ['John Miller', 'Hans Müller']:
        if vip_name in partner_ids:
            try:
                client.execute('res.partner', 'write', [partner_ids[vip_name]],
                    {'category_id': [(6, 0, [tag_ids['Pasajero'], tag_ids['VIP']])]})
            except Exception:
                pass

    # ── 4. Create Quotations ───────────────────────────────────────────
    typer.secho("\n4. Test quotations", bold=True)

    for q in QUOTATIONS:
        ref = q['ref']
        partner_name = q['partner_name']
        partner_id = partner_ids.get(partner_name)

        if not partner_id:
            typer.secho(f"  [SKIP] {ref}: partner '{partner_name}' not found",
                        fg=typer.colors.YELLOW)
            continue

        # Check if quotation already exists (by client_order_ref)
        existing_so = client.search_read('sale.order',
            domain=[['client_order_ref', '=', ref]],
            fields=['id', 'name'], limit=1)
        if existing_so:
            typer.secho(
                f"  [OK] {ref} -> {existing_so[0]['name']} (already exists, id={existing_so[0]['id']})",
                fg=typer.colors.GREEN)
            continue

        # Resolve UTM source/medium
        source_id = _get_utm_source(client, q.get('source_name', '')) if q.get('source_name') else False
        medium_id = _get_utm_medium(client, q.get('medium_name', '')) if q.get('medium_name') else False

        # Create sale order
        so_vals = {
            'partner_id': partner_id,
            'client_order_ref': ref,
            'pricelist_id': q.get('pricelist_id', PRICELIST['USD']),
            'payment_term_id': q.get('payment_term_id', PAYMENT_TERMS['immediate']),
            'note': q.get('note', ''),
        }
        if source_id:
            so_vals['source_id'] = source_id
        if medium_id:
            so_vals['medium_id'] = medium_id
        if q.get('sale_order_template_id'):
            so_vals['sale_order_template_id'] = q['sale_order_template_id']

        result = client.execute('sale.order', 'create', [so_vals])
        so_id = result[0] if isinstance(result, list) else result

        # Create order lines
        for i, line in enumerate(q.get('lines', [])):
            line_vals = {
                'order_id': so_id,
                'product_id': line['product_id'],
                'product_uom_qty': line.get('qty', 1),
                'price_unit': line.get('price', 0),
                'name': line.get('name', ''),
                'sequence': (i + 1) * 10,
            }
            client.execute('sale.order.line', 'create', [line_vals])

        # Read back order total
        so_data = client.search_read('sale.order',
            domain=[['id', '=', so_id]],
            fields=['name', 'amount_total', 'currency_id'])
        so_name = so_data[0]['name'] if so_data else '?'
        total = so_data[0].get('amount_total', 0) if so_data else 0
        currency = so_data[0].get('currency_id', [0, ''])[1] if so_data else ''

        typer.secho(
            f"  [CREATED] {ref} -> {so_name} | partner={partner_name} | "
            f"total={total:.2f} {currency} | {len(q['lines'])} lines",
            fg=typer.colors.GREEN)
        created_count += 1

    # ── 5. Summary ─────────────────────────────────────────────────────
    typer.secho("\n" + "=" * 70, bold=True)
    typer.secho(f"  {created_count} records created", fg=typer.colors.BLUE, bold=True)
    typer.secho("=" * 70, bold=True)

    typer.secho("\nNext steps:", fg=typer.colors.CYAN)
    typer.secho("  1. Open Ventas > Cotizaciones in Odoo to review", fg=typer.colors.CYAN)
    typer.secho("  2. Review passenger data in Contactos", fg=typer.colors.CYAN)
    typer.secho("  3. Confirm a quotation to trigger project creation", fg=typer.colors.CYAN)
    typer.secho("  4. Check Proyecto > Tareas for the auto-created tasks", fg=typer.colors.CYAN)
    typer.secho("  5. Test the full flow: Confirm -> Invoice -> Payment", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
