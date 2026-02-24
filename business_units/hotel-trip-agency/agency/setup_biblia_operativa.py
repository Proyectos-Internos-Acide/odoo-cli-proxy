#!/usr/bin/env python3
"""Setup Biblia Operativa: itinerary, operators, passenger details, views, automation.

Creates:
- x_itinerary_line custom model (structured itinerary table)
- x_operator_line custom model (assigned operators/suppliers)
- Related fields on x_guests_line (passenger details from res.partner)
- Fields on sale.order (itinerary o2m, operators o2m, inclusions, key_times, observations)
- Fields on sale.order.template (is_tour, itinerary o2m, operators o2m, inclusions, etc.)
- ACL rules for both custom models
- View 4487 update: Biblia Operativa tab on sale.order form
- Inherited view on sale.order.template form
- Automation: copy Biblia Operativa from template to quotation

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_biblia_operativa.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from agency.defaults.views import (
    SALE_ORDER_BIBLIA_ARCH,
    TEMPLATE_BIBLIA_ARCH,
    BIBLIA_AUTOMATION_CODE,
    EXCHANGE_RATE_ARCH,
    BIBLIA_REPORT_KEY,
    BIBLIA_REPORT_TEMPLATE,
    VOUCHER_REPORT_KEY,
    VOUCHER_REPORT_TEMPLATE,
)
from agency.defaults.automations import CREATE_POS_FROM_OPERATORS

app = typer.Typer(help="Setup Biblia Operativa (itinerary, operators, passengers, views, automation)")


# ── Helpers ───────────────────────────────────────────────────────────────

def _get_model_id(client, model_name):
    result = client.search_read('ir.model',
        domain=[['model', '=', model_name]], fields=['id'], limit=1)
    return result[0]['id'] if result else False


def _field_exists(client, model_name, field_name):
    result = client.search_read('ir.model.fields',
        domain=[['model', '=', model_name], ['name', '=', field_name]],
        fields=['id'], limit=1)
    return result[0]['id'] if result else False


def _create_field(client, field_def, model_id):
    """Create a field if it doesn't exist. Returns (id, created)."""
    existing = _field_exists(client, field_def['model'], field_def['name'])
    if existing:
        return existing, False
    vals = {**field_def, 'model_id': model_id}
    if 'store' not in vals:
        vals['store'] = True
    result = client.execute('ir.model.fields', 'create', [vals])
    fid = result[0] if isinstance(result, list) else result
    return fid, True


def _create_model(client, name, model_name):
    """Create a custom model if it doesn't exist. Returns (id, created)."""
    existing = client.search_read('ir.model',
        domain=[['model', '=', model_name]], fields=['id'])
    if existing:
        return existing[0]['id'], False
    result = client.execute('ir.model', 'create', [{
        'name': name,
        'model': model_name,
        'state': 'manual',
    }])
    mid = result[0] if isinstance(result, list) else result
    return mid, True


def _ensure_acl(client, name, model_id, group_id=1):
    """Ensure ACL rule exists for a model. Returns (id, created)."""
    existing = client.search_read('ir.model.access',
        domain=[['name', '=', name]], fields=['id'])
    if existing:
        return existing[0]['id'], False
    result = client.execute('ir.model.access', 'create', [{
        'name': name,
        'model_id': model_id,
        'group_id': group_id,
        'perm_read': True,
        'perm_write': True,
        'perm_create': True,
        'perm_unlink': True,
    }])
    aid = result[0] if isinstance(result, list) else result
    return aid, True


# View architectures and automation code imported from defaults/views.py


# ── Aliases for backward compatibility ────────────────────────────────────
SALE_ORDER_VIEW_ARCH = SALE_ORDER_BIBLIA_ARCH
TEMPLATE_VIEW_ARCH = TEMPLATE_BIBLIA_ARCH
AUTOMATION_CODE = BIBLIA_AUTOMATION_CODE


# ── Main setup ────────────────────────────────────────────────────────────

@app.command()
def setup():
    """Create Biblia Operativa models, fields, views, and automation."""
    client = OdooClient()
    client.connect()

    typer.secho("=" * 70, bold=True)
    typer.secho("  BIBLIA OPERATIVA SETUP", bold=True)
    typer.secho("=" * 70, bold=True)

    # ── 1. Model x_itinerary_line ─────────────────────────────────────
    typer.secho("\n1. Model x_itinerary_line", bold=True)
    itin_model_id, created = _create_model(client, 'Itinerary Line', 'x_itinerary_line')
    typer.secho(f"  [{'CREATED' if created else 'OK'}] Model (id={itin_model_id})", fg=typer.colors.GREEN)

    # ── 2. Fields on x_itinerary_line ─────────────────────────────────
    typer.secho("\n2. Fields on x_itinerary_line", bold=True)
    itinerary_fields = [
        {'name': 'x_sequence', 'field_description': 'Secuencia', 'ttype': 'integer', 'model': 'x_itinerary_line'},
        {'name': 'x_day_number', 'field_description': 'Dia', 'ttype': 'integer', 'model': 'x_itinerary_line'},
        {'name': 'x_title', 'field_description': 'Titulo', 'ttype': 'char', 'model': 'x_itinerary_line', 'translate': True},
        {'name': 'x_description', 'field_description': 'Descripcion', 'ttype': 'text', 'model': 'x_itinerary_line', 'translate': True},
        {'name': 'x_accommodation', 'field_description': 'Alojamiento', 'ttype': 'char', 'model': 'x_itinerary_line', 'translate': True},
        {'name': 'x_meals', 'field_description': 'Comidas', 'ttype': 'char', 'model': 'x_itinerary_line', 'translate': True},
        {'name': 'x_sale_order_id', 'field_description': 'Venta', 'ttype': 'many2one',
         'relation': 'sale.order', 'on_delete': 'cascade', 'model': 'x_itinerary_line'},
        {'name': 'x_template_id', 'field_description': 'Plantilla', 'ttype': 'many2one',
         'relation': 'sale.order.template', 'on_delete': 'cascade', 'model': 'x_itinerary_line'},
    ]
    for fdef in itinerary_fields:
        fid, created = _create_field(client, fdef, itin_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']} ({fdef['ttype']})", fg=typer.colors.GREEN)

    # ── 3. ACL for x_itinerary_line ───────────────────────────────────
    typer.secho("\n3. ACL for x_itinerary_line", bold=True)
    acl_id, created = _ensure_acl(client, 'access_x_itinerary_line_user', itin_model_id)
    typer.secho(f"  [{'CREATED' if created else 'OK'}] ACL (id={acl_id})", fg=typer.colors.GREEN)

    # ── 4. Model x_operator_line ──────────────────────────────────────
    typer.secho("\n4. Model x_operator_line", bold=True)
    oper_model_id, created = _create_model(client, 'Operator Line', 'x_operator_line')
    typer.secho(f"  [{'CREATED' if created else 'OK'}] Model (id={oper_model_id})", fg=typer.colors.GREEN)

    # ── 5. Fields on x_operator_line ──────────────────────────────────
    typer.secho("\n5. Fields on x_operator_line", bold=True)
    operator_fields = [
        {'name': 'x_sequence', 'field_description': 'Secuencia', 'ttype': 'integer', 'model': 'x_operator_line'},
        {'name': 'x_partner_id', 'field_description': 'Operador', 'ttype': 'many2one',
         'relation': 'res.partner', 'model': 'x_operator_line'},
        {'name': 'x_service_type', 'field_description': 'Tipo de Servicio', 'ttype': 'selection',
         'selection_ids': [
             (0, 0, {'value': 'transporte', 'name': 'Transporte', 'sequence': 1}),
             (0, 0, {'value': 'tren', 'name': 'Tren', 'sequence': 2}),
             (0, 0, {'value': 'guia', 'name': 'Guía', 'sequence': 3}),
             (0, 0, {'value': 'hotel', 'name': 'Hotel', 'sequence': 4}),
             (0, 0, {'value': 'restaurante', 'name': 'Restaurante', 'sequence': 5}),
             (0, 0, {'value': 'otros', 'name': 'Otros', 'sequence': 6}),
         ], 'model': 'x_operator_line'},
        {'name': 'x_phone_rel', 'field_description': 'Telefono', 'ttype': 'char',
         'related': 'x_partner_id.phone', 'readonly': True, 'store': False, 'model': 'x_operator_line'},
        {'name': 'x_email_rel', 'field_description': 'Email', 'ttype': 'char',
         'related': 'x_partner_id.email', 'readonly': True, 'store': False, 'model': 'x_operator_line'},
        {'name': 'x_sale_order_id', 'field_description': 'Venta', 'ttype': 'many2one',
         'relation': 'sale.order', 'on_delete': 'cascade', 'model': 'x_operator_line'},
        {'name': 'x_template_id', 'field_description': 'Plantilla', 'ttype': 'many2one',
         'relation': 'sale.order.template', 'on_delete': 'cascade', 'model': 'x_operator_line'},
        {'name': 'x_cost', 'field_description': 'Costo Estimado', 'ttype': 'float',
         'model': 'x_operator_line'},
        {'name': 'x_purchase_order_id', 'field_description': 'Pedido de Compra', 'ttype': 'many2one',
         'relation': 'purchase.order', 'readonly': True, 'model': 'x_operator_line'},
        {'name': 'x_po_state', 'field_description': 'Estado PO', 'ttype': 'selection',
         'related': 'x_purchase_order_id.state', 'readonly': True, 'store': False, 'model': 'x_operator_line'},
        {'name': 'x_description', 'field_description': 'Descripcion', 'ttype': 'char',
         'model': 'x_operator_line'},
        {'name': 'x_date', 'field_description': 'Fecha', 'ttype': 'date',
         'model': 'x_operator_line'},
    ]
    for fdef in operator_fields:
        fid, created = _create_field(client, fdef, oper_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']} ({fdef['ttype']})", fg=typer.colors.GREEN)

    # ── 6. ACL for x_operator_line ────────────────────────────────────
    typer.secho("\n6. ACL for x_operator_line", bold=True)
    acl_id, created = _ensure_acl(client, 'access_x_operator_line_user', oper_model_id)
    typer.secho(f"  [{'CREATED' if created else 'OK'}] ACL (id={acl_id})", fg=typer.colors.GREEN)

    # ── 7. Related fields on x_guests_line (passenger details) ────────
    typer.secho("\n7. Related fields on x_guests_line", bold=True)
    guest_model_id = _get_model_id(client, 'x_guests_line')
    if not guest_model_id:
        typer.secho("  [WARN] Model x_guests_line not found — skip passenger related fields", fg=typer.colors.YELLOW)
    else:
        guest_related_fields = [
            {'name': 'x_nationality_id', 'field_description': 'Nacionalidad', 'ttype': 'many2one',
             'relation': 'res.country', 'related': 'x_guest_partner_id.x_nationality',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_document_type_rel', 'field_description': 'Tipo Doc.', 'ttype': 'selection',
             'related': 'x_guest_partner_id.x_document_type',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_document_number_rel', 'field_description': 'Nro. Doc.', 'ttype': 'char',
             'related': 'x_guest_partner_id.x_document_number',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_birthdate_rel', 'field_description': 'Fecha Nac.', 'ttype': 'date',
             'related': 'x_guest_partner_id.x_birthdate',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_phone_rel', 'field_description': 'Telefono', 'ttype': 'char',
             'related': 'x_guest_partner_id.phone',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_email_rel', 'field_description': 'Email', 'ttype': 'char',
             'related': 'x_guest_partner_id.email',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_lang_rel', 'field_description': 'Idioma', 'ttype': 'selection',
             'related': 'x_guest_partner_id.lang',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_medical_rel', 'field_description': 'Restricciones', 'ttype': 'text',
             'related': 'x_guest_partner_id.x_medical_restrictions',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_emergency_name_rel', 'field_description': 'Contacto Emerg.', 'ttype': 'char',
             'related': 'x_guest_partner_id.x_emergency_contact_name',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
            {'name': 'x_emergency_phone_rel', 'field_description': 'Tel. Emergencia', 'ttype': 'char',
             'related': 'x_guest_partner_id.x_emergency_contact_phone',
             'readonly': True, 'store': False, 'model': 'x_guests_line'},
        ]
        for fdef in guest_related_fields:
            fid, created = _create_field(client, fdef, guest_model_id)
            typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']} (related)", fg=typer.colors.GREEN)

    # ── 8. Fields on sale.order ────────────────────────────────────────
    typer.secho("\n8. Fields on sale.order", bold=True)
    so_model_id = _get_model_id(client, 'sale.order')
    so_fields = [
        {'name': 'x_itinerary_line_ids', 'field_description': 'Lineas de Itinerario',
         'ttype': 'one2many', 'relation': 'x_itinerary_line', 'relation_field': 'x_sale_order_id',
         'model': 'sale.order'},
        {'name': 'x_operator_line_ids', 'field_description': 'Operadores Asignados',
         'ttype': 'one2many', 'relation': 'x_operator_line', 'relation_field': 'x_sale_order_id',
         'model': 'sale.order'},
        {'name': 'x_inclusions', 'field_description': 'Servicios Incluidos', 'ttype': 'html',
         'model': 'sale.order', 'translate': True},
        {'name': 'x_key_times', 'field_description': 'Horarios Clave', 'ttype': 'text',
         'model': 'sale.order', 'translate': True},
        {'name': 'x_special_observations', 'field_description': 'Observaciones Especiales', 'ttype': 'text',
         'model': 'sale.order', 'translate': True},
    ]
    for fdef in so_fields:
        fid, created = _create_field(client, fdef, so_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']} ({fdef['ttype']})", fg=typer.colors.GREEN)

    # ── 9. Fields on sale.order.template ───────────────────────────────
    typer.secho("\n9. Fields on sale.order.template", bold=True)
    tmpl_model_id = _get_model_id(client, 'sale.order.template')
    tmpl_fields = [
        {'name': 'x_is_tour', 'field_description': 'Es un Tour', 'ttype': 'boolean',
         'model': 'sale.order.template'},
        {'name': 'x_itinerary_line_ids', 'field_description': 'Lineas de Itinerario',
         'ttype': 'one2many', 'relation': 'x_itinerary_line', 'relation_field': 'x_template_id',
         'model': 'sale.order.template'},
        {'name': 'x_operator_line_ids', 'field_description': 'Operadores por Defecto',
         'ttype': 'one2many', 'relation': 'x_operator_line', 'relation_field': 'x_template_id',
         'model': 'sale.order.template'},
        {'name': 'x_inclusions', 'field_description': 'Servicios Incluidos', 'ttype': 'html',
         'model': 'sale.order.template', 'translate': True},
        {'name': 'x_key_times', 'field_description': 'Horarios Clave', 'ttype': 'text',
         'model': 'sale.order.template', 'translate': True},
        {'name': 'x_special_observations', 'field_description': 'Observaciones Especiales', 'ttype': 'text',
         'model': 'sale.order.template', 'translate': True},
    ]
    for fdef in tmpl_fields:
        fid, created = _create_field(client, fdef, tmpl_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']} ({fdef['ttype']})", fg=typer.colors.GREEN)

    # ── 10. View: sale.order Biblia Operativa tab ─────────────────────
    typer.secho("\n10. View: sale.order form (Biblia Operativa + Tour section)", bold=True)
    # Look up existing action IDs for buttons (reports + PO creation)
    _biblia_rpt = client.search_read('ir.actions.report',
        domain=[['report_name', '=', BIBLIA_REPORT_KEY]], fields=['id'], limit=1)
    _voucher_rpt = client.search_read('ir.actions.report',
        domain=[['report_name', '=', VOUCHER_REPORT_KEY]], fields=['id'], limit=1)
    _create_po_sa = client.search_read('ir.actions.server',
        domain=[['name', '=', 'Create POs from Biblia Operators']], fields=['id'], limit=1)
    # Build arch: replace placeholders if actions exist, otherwise strip buttons
    so_arch = SALE_ORDER_VIEW_ARCH
    if _biblia_rpt and _voucher_rpt:
        so_arch = so_arch.replace('{biblia_report_action_id}', str(_biblia_rpt[0]['id']))
        so_arch = so_arch.replace('{voucher_report_action_id}', str(_voucher_rpt[0]['id']))
        typer.secho(f"  Buttons: Biblia→{_biblia_rpt[0]['id']}, Voucher→{_voucher_rpt[0]['id']}", fg=typer.colors.CYAN)
    else:
        # First run: reports not created yet — remove button divs, will be added in step 19
        import re
        so_arch = re.sub(r'<div[^>]*name="biblia_buttons"[^>]*>.*?</div>\s*', '', so_arch, flags=re.DOTALL)
        so_arch = re.sub(r'<div[^>]*name="voucher_button"[^>]*>.*?</div>\s*', '', so_arch, flags=re.DOTALL)
        typer.secho("  Buttons: deferred to step 19 (reports not yet created)", fg=typer.colors.CYAN)
    if _create_po_sa:
        so_arch = so_arch.replace('{create_po_action_id}', str(_create_po_sa[0]['id']))
        typer.secho(f"  Button: CreatePO→{_create_po_sa[0]['id']}", fg=typer.colors.CYAN)
    else:
        # First run: server action not yet created — remove PO button, will be added in step 19
        import re
        so_arch = re.sub(r'<button[^>]*name="\{create_po_action_id\}"[^/]*/>', '', so_arch)
        typer.secho("  Button: CreatePO deferred to step 19", fg=typer.colors.CYAN)

    SO_VIEW_NAME = 'sale.order.form.inherit.agency_biblia'
    existing_view = client.search_read('ir.ui.view',
        domain=[['name', '=', SO_VIEW_NAME]],
        fields=['id'])
    if existing_view:
        view_id = existing_view[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': so_arch})
        typer.secho(f"  [UPDATED] View {view_id}", fg=typer.colors.GREEN)
    else:
        # Find base sale.order form view dynamically
        base_so_view = client.search_read('ir.ui.view',
            domain=[['model', '=', 'sale.order'], ['type', '=', 'form'],
                    ['inherit_id', '=', False], ['mode', '=', 'primary']],
            fields=['id', 'name'], limit=1)
        if not base_so_view:
            typer.secho("  [ERROR] Base sale.order form view not found!", fg=typer.colors.RED)
            raise typer.Exit(1)
        base_view_id = base_so_view[0]['id']
        typer.secho(f"  Base view: {base_so_view[0]['name']} (id={base_view_id})", fg=typer.colors.CYAN)
        result = client.execute('ir.ui.view', 'create', [{
            'name': SO_VIEW_NAME,
            'model': 'sale.order',
            'inherit_id': base_view_id,
            'type': 'form',
            'arch': so_arch,
            'priority': 99,
        }])
        view_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] View {view_id}", fg=typer.colors.GREEN)

    # ── 11. View: sale.order.template Biblia Operativa tab ────────────
    typer.secho("\n11. View: sale.order.template form", bold=True)
    TMPL_VIEW_NAME = 'sale.order.template.form.inherit.agency_biblia'
    existing_tmpl_view = client.search_read('ir.ui.view',
        domain=[['name', '=', TMPL_VIEW_NAME]],
        fields=['id'])
    if existing_tmpl_view:
        view_id = existing_tmpl_view[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': TEMPLATE_VIEW_ARCH})
        typer.secho(f"  [UPDATED] View {view_id}", fg=typer.colors.GREEN)
    else:
        # Find base sale.order.template form view dynamically
        base_tmpl_view = client.search_read('ir.ui.view',
            domain=[['model', '=', 'sale.order.template'], ['type', '=', 'form'],
                    ['inherit_id', '=', False], ['mode', '=', 'primary']],
            fields=['id', 'name'], limit=1)
        if not base_tmpl_view:
            typer.secho("  [ERROR] Base sale.order.template form view not found!", fg=typer.colors.RED)
            raise typer.Exit(1)
        base_view_id = base_tmpl_view[0]['id']
        typer.secho(f"  Base view: {base_tmpl_view[0]['name']} (id={base_view_id})", fg=typer.colors.CYAN)
        result = client.execute('ir.ui.view', 'create', [{
            'name': TMPL_VIEW_NAME,
            'model': 'sale.order.template',
            'inherit_id': base_view_id,
            'type': 'form',
            'arch': TEMPLATE_VIEW_ARCH,
            'priority': 99,
        }])
        view_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] View {view_id}", fg=typer.colors.GREEN)

    # ── 12. Automation: copy template → quotation ─────────────────────
    typer.secho("\n12. Automation: Copy Biblia Operativa from Template", bold=True)
    existing_auto = client.search_read('base.automation',
        domain=[['name', '=', 'Copy Biblia Operativa from Template']],
        fields=['id', 'action_server_ids'])
    if existing_auto:
        auto_id = existing_auto[0]['id']
        action_ids = existing_auto[0].get('action_server_ids', [])
        if action_ids:
            client.execute('ir.actions.server', 'write', [action_ids[0]], {'code': AUTOMATION_CODE})
        # Ensure trigger is on_create_or_write with no trigger_field_ids
        client.execute('base.automation', 'write', [auto_id], {
            'trigger': 'on_create_or_write',
            'trigger_field_ids': [(5, 0, 0)],
        })
        typer.secho(f"  [UPDATED] Automation {auto_id}", fg=typer.colors.GREEN)
    else:
        action_result = client.execute('ir.actions.server', 'create', [{
            'name': 'Copy Biblia Operativa from Template',
            'model_id': so_model_id,
            'state': 'code',
            'code': AUTOMATION_CODE,
        }])
        action_id = action_result[0] if isinstance(action_result, list) else action_result

        auto_result = client.execute('base.automation', 'create', [{
            'name': 'Copy Biblia Operativa from Template',
            'model_id': so_model_id,
            'trigger': 'on_create_or_write',
            'trigger_field_ids': [],
            'action_server_ids': [(6, 0, [action_id])],
            'active': True,
        }])
        auto_id = auto_result[0] if isinstance(auto_result, list) else auto_result
        typer.secho(f"  [CREATED] Automation {auto_id} (action {action_id})", fg=typer.colors.GREEN)

    # ── 13. View: Exchange rate on quotation PDF ─────────────────────
    typer.secho("\n13. View: Exchange rate on quotation PDF", bold=True)
    RATE_VIEW_NAME = 'sale.report_saleorder_document.exchange_rate'
    existing_rate = client.search_read('ir.ui.view',
        domain=[['name', '=', RATE_VIEW_NAME]],
        fields=['id'])
    if existing_rate:
        view_id = existing_rate[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': EXCHANGE_RATE_ARCH})
        typer.secho(f"  [UPDATED] View {view_id}", fg=typer.colors.GREEN)
    else:
        # Find base sale order report template
        base_report = client.search_read('ir.ui.view',
            domain=[['key', '=', 'sale.report_saleorder_document']],
            fields=['id', 'name'], limit=1)
        if not base_report:
            # Fallback: search by name
            base_report = client.search_read('ir.ui.view',
                domain=[['name', 'ilike', 'report_saleorder_document'],
                        ['type', '=', 'qweb']],
                fields=['id', 'name'], limit=1)
        if base_report:
            base_view_id = base_report[0]['id']
            typer.secho(f"  Base report: {base_report[0]['name']} (id={base_view_id})", fg=typer.colors.CYAN)
            result = client.execute('ir.ui.view', 'create', [{
                'name': RATE_VIEW_NAME,
                'model': 'sale.order',
                'inherit_id': base_view_id,
                'type': 'qweb',
                'arch': EXCHANGE_RATE_ARCH,
                'priority': 99,
            }])
            view_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] View {view_id}", fg=typer.colors.GREEN)
        else:
            typer.secho("  [WARN] Base sale order report view not found", fg=typer.colors.YELLOW)

    # ── 14. PDF Report: Biblia Operativa ─────────────────────────────
    typer.secho("\n14. PDF Report: Biblia Operativa", bold=True)
    # Get sale.order model id for binding
    so_model = client.search_read('ir.model',
        domain=[['model', '=', 'sale.order']], fields=['id'], limit=1)
    so_model_id = so_model[0]['id'] if so_model else False

    # 14a. QWeb template
    existing_biblia_tmpl = client.search_read('ir.ui.view',
        domain=[['key', '=', BIBLIA_REPORT_KEY]], fields=['id'])
    if existing_biblia_tmpl:
        client.execute('ir.ui.view', 'write', [existing_biblia_tmpl[0]['id']],
            {'arch': BIBLIA_REPORT_TEMPLATE})
        typer.secho(f"  [UPDATED] QWeb template (id={existing_biblia_tmpl[0]['id']})", fg=typer.colors.GREEN)
    else:
        result = client.execute('ir.ui.view', 'create', [{
            'name': BIBLIA_REPORT_KEY,
            'type': 'qweb',
            'key': BIBLIA_REPORT_KEY,
            'arch': BIBLIA_REPORT_TEMPLATE,
        }])
        tmpl_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] QWeb template (id={tmpl_id})", fg=typer.colors.GREEN)

    # 14b. Report action
    biblia_report_vals = {
        'print_report_name': "'Biblia Operativa - %s' % object.name",
    }
    existing_biblia_report = client.search_read('ir.actions.report',
        domain=[['report_name', '=', BIBLIA_REPORT_KEY]], fields=['id'])
    if existing_biblia_report:
        client.execute('ir.actions.report', 'write', [existing_biblia_report[0]['id']], biblia_report_vals)
        typer.secho(f"  [UPDATED] Report action (id={existing_biblia_report[0]['id']})", fg=typer.colors.GREEN)
    else:
        report_vals = {
            'name': 'Biblia Operativa',
            'model': 'sale.order',
            'report_type': 'qweb-pdf',
            'report_name': BIBLIA_REPORT_KEY,
            'binding_type': 'report',
            **biblia_report_vals,
        }
        if so_model_id:
            report_vals['binding_model_id'] = so_model_id
        result = client.execute('ir.actions.report', 'create', [report_vals])
        report_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] Report action (id={report_id})", fg=typer.colors.GREEN)

    # ── 15. PDF Report: Voucher Pasajero ──────────────────────────────
    typer.secho("\n15. PDF Report: Voucher Pasajero", bold=True)

    # 15a. QWeb template
    existing_voucher_tmpl = client.search_read('ir.ui.view',
        domain=[['key', '=', VOUCHER_REPORT_KEY]], fields=['id'])
    if existing_voucher_tmpl:
        client.execute('ir.ui.view', 'write', [existing_voucher_tmpl[0]['id']],
            {'arch': VOUCHER_REPORT_TEMPLATE})
        typer.secho(f"  [UPDATED] QWeb template (id={existing_voucher_tmpl[0]['id']})", fg=typer.colors.GREEN)
    else:
        result = client.execute('ir.ui.view', 'create', [{
            'name': VOUCHER_REPORT_KEY,
            'type': 'qweb',
            'key': VOUCHER_REPORT_KEY,
            'arch': VOUCHER_REPORT_TEMPLATE,
        }])
        tmpl_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] QWeb template (id={tmpl_id})", fg=typer.colors.GREEN)

    # 15b. Report action
    voucher_report_vals = {
        'print_report_name': "'Voucher - %s' % object.name",
    }
    existing_voucher_report = client.search_read('ir.actions.report',
        domain=[['report_name', '=', VOUCHER_REPORT_KEY]], fields=['id'])
    if existing_voucher_report:
        client.execute('ir.actions.report', 'write', [existing_voucher_report[0]['id']], voucher_report_vals)
        typer.secho(f"  [UPDATED] Report action (id={existing_voucher_report[0]['id']})", fg=typer.colors.GREEN)
    else:
        report_vals = {
            'name': 'Voucher Pasajero',
            'model': 'sale.order',
            'report_type': 'qweb-pdf',
            'report_name': VOUCHER_REPORT_KEY,
            'binding_type': 'report',
            **voucher_report_vals,
        }
        if so_model_id:
            report_vals['binding_model_id'] = so_model_id
        result = client.execute('ir.actions.report', 'create', [report_vals])
        report_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] Report action (id={report_id})", fg=typer.colors.GREEN)

    # ── 16. (Superseded by step 19 — all button injection done there) ──
    typer.secho("\n16. Button injection", bold=True)
    typer.secho("  [SKIP] Handled in step 19 (all action IDs injected together)", fg=typer.colors.CYAN)

    # ── 17. Cleanup: remove old duplicate view if exists ─────────────
    typer.secho("\n17. Cleanup old views", bold=True)
    old_views = client.search_read('ir.ui.view',
        domain=[['name', '=', 'sale.order.form.inherit.agency_tour'],
                ['model', '=', 'sale.order']],
        fields=['id'])
    if old_views:
        client.execute('ir.ui.view', 'unlink', [v['id'] for v in old_views])
        typer.secho(f"  [DELETED] {len(old_views)} old agency_tour view(s)", fg=typer.colors.GREEN)
    else:
        typer.secho("  [OK] No old views to clean up", fg=typer.colors.GREEN)

    # ── 18. Server action: Create POs from Biblia operators ──────────
    typer.secho("\n18. Server action: Create POs from Biblia operators", bold=True)
    CREATE_PO_ACTION_NAME = 'Create POs from Biblia Operators'
    existing_sa = client.search_read('ir.actions.server',
        domain=[['name', '=', CREATE_PO_ACTION_NAME]],
        fields=['id'])
    if existing_sa:
        sa_id = existing_sa[0]['id']
        client.execute('ir.actions.server', 'write', [sa_id], {
            'code': CREATE_POS_FROM_OPERATORS,
        })
        typer.secho(f"  [UPDATED] Server action {sa_id}", fg=typer.colors.GREEN)
    else:
        result = client.execute('ir.actions.server', 'create', [{
            'name': CREATE_PO_ACTION_NAME,
            'model_id': so_model_id,
            'state': 'code',
            'code': CREATE_POS_FROM_OPERATORS,
        }])
        sa_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] Server action {sa_id}", fg=typer.colors.GREEN)

    # ── 19. Inject all action IDs into SO form view ───────────────────
    typer.secho("\n19. Inject action IDs into SO form view", bold=True)
    biblia_report = client.search_read('ir.actions.report',
        domain=[['report_name', '=', BIBLIA_REPORT_KEY]], fields=['id'], limit=1)
    voucher_report = client.search_read('ir.actions.report',
        domain=[['report_name', '=', VOUCHER_REPORT_KEY]], fields=['id'], limit=1)
    biblia_report_id = biblia_report[0]['id'] if biblia_report else 0
    voucher_report_id = voucher_report[0]['id'] if voucher_report else 0

    so_view_final = client.search_read('ir.ui.view',
        domain=[['name', '=', 'sale.order.form.inherit.agency_biblia']],
        fields=['id'], limit=1)
    if so_view_final and biblia_report_id and voucher_report_id and sa_id:
        arch_final = SALE_ORDER_VIEW_ARCH.replace(
            '{biblia_report_action_id}', str(biblia_report_id)
        ).replace(
            '{voucher_report_action_id}', str(voucher_report_id)
        ).replace(
            '{create_po_action_id}', str(sa_id)
        )
        client.execute('ir.ui.view', 'write', [so_view_final[0]['id']], {'arch': arch_final})
        typer.secho(f"  [OK] Biblia→{biblia_report_id}, Voucher→{voucher_report_id}, CreatePO→{sa_id}", fg=typer.colors.GREEN)
    else:
        typer.secho("  [WARN] Could not inject all action IDs (missing view or actions)", fg=typer.colors.YELLOW)

    # ── Summary ───────────────────────────────────────────────────────
    typer.secho("\n" + "=" * 70, bold=True)
    typer.secho("  BIBLIA OPERATIVA SETUP COMPLETE", fg=typer.colors.BLUE, bold=True)
    typer.secho("=" * 70, bold=True)
    typer.secho("\nCreated:", fg=typer.colors.CYAN)
    typer.secho("  - Model: x_itinerary_line (structured itinerary table)", fg=typer.colors.CYAN)
    typer.secho("  - Model: x_operator_line (assigned operators/suppliers)", fg=typer.colors.CYAN)
    typer.secho("  - Related fields on x_guests_line (passenger details from res.partner)", fg=typer.colors.CYAN)
    typer.secho("  - sale.order: itinerary, operators, inclusions, key_times, observations", fg=typer.colors.CYAN)
    typer.secho("  - sale.order.template: is_tour, itinerary, operators, inclusions, etc.", fg=typer.colors.CYAN)
    typer.secho("  - ACL: full CRUD for Role/User on both custom models", fg=typer.colors.CYAN)
    typer.secho("  - Views: Biblia Operativa tab on SO form + template form", fg=typer.colors.CYAN)
    typer.secho("  - Automation: copies Biblia from template to quotation (on_create_or_write)", fg=typer.colors.CYAN)
    typer.secho("  - PDF: Biblia Operativa report (Print menu on sale.order)", fg=typer.colors.CYAN)
    typer.secho("  - PDF: Voucher Pasajero report (Print menu, one page per passenger)", fg=typer.colors.CYAN)
    typer.secho("\nNote: Passenger data (restrictions, birthdate, etc.) is filled in the", fg=typer.colors.YELLOW)
    typer.secho("  contact form (res.partner) and shown as readonly in the Biblia.", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
