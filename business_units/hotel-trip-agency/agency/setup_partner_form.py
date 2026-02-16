#!/usr/bin/env python3
"""Setup partner form view with guest/passenger fields.

Creates an inherited view on res.partner form that adds:
- Birthdate field (after document number)
- Medical restrictions
- Emergency contact name and phone
- Clearer labels for travel document fields (vs fiscal ID)

Depends on: setup_custom_fields.py (creates the x_ fields on res.partner)
Depends on: booking engine view 3702 (adds x_nationality, x_document_type, x_document_number)

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_partner_form.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from agency.defaults.views import PARTNER_GUEST_FIELDS_ARCH

app = typer.Typer(help="Setup partner form with guest/passenger fields")

VIEW_NAME = 'res.partner.form.inherit.agency_guest_fields'


def _find_booking_engine_view(client):
    """Find the booking engine view that adds x_nationality/x_document_type to res.partner."""
    # Search for res.partner form views containing x_document_type in their arch
    candidates = client.search_read('ir.ui.view',
        domain=[['model', '=', 'res.partner'], ['type', '=', 'form'],
                ['arch_db', 'ilike', 'x_document_type']],
        fields=['id', 'name', 'inherit_id'], limit=5)
    for v in candidates:
        # Skip our own view
        if v['name'] == VIEW_NAME:
            continue
        return v['id'], v['name']
    return False, False


@app.command()
def setup():
    """Create partner form view with guest fields + update field labels."""
    client = OdooClient()
    client.connect()

    typer.secho("=" * 70, bold=True)
    typer.secho("  PARTNER FORM - GUEST FIELDS SETUP", bold=True)
    typer.secho("=" * 70, bold=True)

    # ── 1. Find booking engine view dynamically ─────────────────────
    typer.secho("\n1. Find booking engine view", bold=True)
    be_view_id, be_view_name = _find_booking_engine_view(client)
    if be_view_id:
        typer.secho(f"  [OK] {be_view_name} (id={be_view_id})", fg=typer.colors.GREEN)
    else:
        typer.secho("  [ERROR] Booking engine view not found (needs x_document_type on res.partner)!", fg=typer.colors.RED)
        typer.secho("  Cannot create inherited view. Run booking engine setup first.", fg=typer.colors.RED)
        raise typer.Exit(1)

    # ── 2. Create/update inherited view ───────────────────────────────
    typer.secho("\n2. Partner form view", bold=True)
    existing = client.search_read('ir.ui.view',
        domain=[['name', '=', VIEW_NAME]],
        fields=['id'])

    if existing:
        view_id = existing[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': PARTNER_GUEST_FIELDS_ARCH})
        typer.secho(f"  [UPDATED] View {view_id}", fg=typer.colors.GREEN)
    else:
        result = client.execute('ir.ui.view', 'create', [{
            'name': VIEW_NAME,
            'model': 'res.partner',
            'inherit_id': be_view_id,
            'type': 'form',
            'arch': PARTNER_GUEST_FIELDS_ARCH,
            'priority': 99,
        }])
        view_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] View {view_id}", fg=typer.colors.GREEN)

    # ── 3. Update field labels to Spanish ─────────────────────────────
    typer.secho("\n3. Update field labels", bold=True)
    label_updates = {
        'x_birthdate': 'Fecha de Nacimiento',
        'x_medical_restrictions': 'Restricciones Medicas / Alimentarias',
        'x_emergency_contact_name': 'Contacto de Emergencia',
        'x_emergency_contact_phone': 'Tel. Emergencia',
        'x_document_type': 'Tipo Doc. de Viaje',
        'x_document_number': 'Nro. Doc. de Viaje',
    }
    for fname, label in label_updates.items():
        field = client.search_read('ir.model.fields',
            domain=[['model', '=', 'res.partner'], ['name', '=', fname]],
            fields=['id', 'field_description'])
        if field:
            client.execute('ir.model.fields', 'write', [field[0]['id']], {'field_description': label})
            typer.secho(f"  [OK] {fname} -> \"{label}\"", fg=typer.colors.GREEN)
        else:
            typer.secho(f"  [SKIP] {fname} not found", fg=typer.colors.YELLOW)

    # ── Summary ───────────────────────────────────────────────────────
    typer.secho("\n" + "=" * 70, bold=True)
    typer.secho("  PARTNER FORM SETUP COMPLETE", fg=typer.colors.BLUE, bold=True)
    typer.secho("=" * 70, bold=True)
    typer.secho(f"\nView: {VIEW_NAME} (id={view_id})", fg=typer.colors.CYAN)
    typer.secho("Fields added to contact form:", fg=typer.colors.CYAN)
    typer.secho("  Left column:  Nacionalidad, Tipo Doc. de Viaje, Nro. Doc. de Viaje, Fecha de Nacimiento", fg=typer.colors.CYAN)
    typer.secho("  Right column: Restricciones Medicas, Contacto Emergencia, Tel. Emergencia", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
