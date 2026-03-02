"""
Setup payment terms and prepayment configuration for tour quotations.

Creates:
- Payment term: "50% Anticipo, 50% antes del viaje" (50% now, 50% in 30 days)
- Updates all SO templates with prepayment_percent = 0.50 (50%)

Usage:
    python -m business_units.hotel-trip-agency.agency.setup_payment_config
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from odoo_cli.client import OdooClient

# --- Configuration ---
PAYMENT_TERMS = [
    {
        'name': '50% Anticipo, 50% antes del viaje',
        'note': '50% al confirmar la reserva, 50% restante 30 días después.',
        'lines': [
            {'value': 'percent', 'value_amount': 50.0, 'nb_days': 0, 'delay_type': 'days_after'},
            {'value': 'percent', 'value_amount': 50.0, 'nb_days': 30, 'delay_type': 'days_after'},
        ]
    },
]

PREPAYMENT_PERCENT = 0.50  # 50% online portal payment


def setup_payment_terms(client):
    """Create custom payment terms if they don't exist."""
    created = []
    for term in PAYMENT_TERMS:
        existing = client.execute('account.payment.term', 'search', [
            ['name', '=', term['name']]
        ])
        if existing:
            print(f"  [SKIP] Payment term already exists: '{term['name']}' (ID={existing[0]})")
            created.append(existing[0])
            continue

        term_id = client.execute('account.payment.term', 'create', [{
            'name': term['name'],
            'note': term.get('note', ''),
            'line_ids': [(0, 0, line) for line in term['lines']],
        }])
        result_id = term_id[0] if isinstance(term_id, list) else term_id
        print(f"  [OK] Created payment term: '{term['name']}' (ID={result_id})")
        created.append(result_id)

    return created


def update_template_prepayment(client, prepayment_pct):
    """Update prepayment_percent on all SO templates."""
    tmpl_ids = client.execute('sale.order.template', 'search', [['id', '>', 0]])
    if not tmpl_ids:
        print("  [WARN] No SO templates found")
        return

    templates = client.execute('sale.order.template', 'read', tmpl_ids, [
        'name', 'prepayment_percent', 'require_payment'
    ])

    to_update = []
    for t in templates:
        if t['prepayment_percent'] != prepayment_pct or not t['require_payment']:
            to_update.append(t['id'])

    if not to_update:
        print(f"  [SKIP] All {len(templates)} templates already have prepayment={prepayment_pct*100:.0f}%")
        return

    client.execute('sale.order.template', 'write', to_update, {
        'prepayment_percent': prepayment_pct,
        'require_payment': True,
    })
    print(f"  [OK] Updated {len(to_update)}/{len(templates)} templates → prepayment={prepayment_pct*100:.0f}%")

    # Show results
    updated = client.execute('sale.order.template', 'read', to_update[:5], [
        'name', 'prepayment_percent', 'require_payment'
    ])
    for t in updated:
        print(f"       {t['name']}: require_payment={t['require_payment']}, prepayment={t['prepayment_percent']*100:.0f}%")
    if len(to_update) > 5:
        print(f"       ... and {len(to_update) - 5} more")


def main():
    print("=== Payment Configuration Setup ===\n")

    # Connect to production
    client = OdooClient(
        url=os.environ.get('TARGET_MIGRATION_URL', 'https://machupicchu-afdestiny-production.odoo.com/'),
        db=os.environ.get('TARGET_MIGRATION_DB', 'machupicchu-afdestiny-production'),
        username=os.environ.get('TARGET_MIGRATION_USERNAME', 'ayfdestinyeirl@gmail.com'),
        password=os.environ.get('TARGET_MIGRATION_PASSWORD', 'L^yUbD2^+p^2h.#'),
    )
    client.connect()
    print(f"Connected to {client.url} as uid={client.uid}\n")

    # 1. Create payment terms
    print("1. Payment Terms")
    term_ids = setup_payment_terms(client)
    print()

    # 2. Update SO templates prepayment
    print("2. SO Template Prepayment")
    update_template_prepayment(client, PREPAYMENT_PERCENT)
    print()

    # Summary
    print("=== Summary ===")
    print(f"  Payment terms created/verified: {len(term_ids)}")
    print(f"  Prepayment percent: {PREPAYMENT_PERCENT*100:.0f}%")
    print()
    print("Next steps:")
    print("  1. Activate Mercado Pago or Stripe in Contabilidad → Configuración → Proveedores de Pago")
    print("  2. New payment terms available in Contabilidad → Configuración → Plazos de Pago")
    print("  3. On each quotation, set payment_term_id to '50% Anticipo' in the main tab")
    print("  4. The 50% prepayment is already configured in Other Info → Online Payment")


if __name__ == '__main__':
    main()
