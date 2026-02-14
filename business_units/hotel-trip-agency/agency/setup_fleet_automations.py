#!/usr/bin/env python3
"""Setup fleet/tour automations, task fields, work log, and task form view.

Creates:
- Custom fields on project.task (tour dates, fleet vehicle, driver, seats, operator)
- Custom fields on sale.order (tour dates, passengers, is_tour)
- Model x_task_work_log (structured work log by contact/operator)
- Task form view with fleet fields + operator + work log tab
- 4 automations: validate dates, propagate data, vehicle conflicts, sync changes

Depends on: setup_custom_fields.py (creates x_service_type, x_departure_city on sale.order)

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_fleet_automations.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from agency.defaults.automations import (
    VALIDATE_TOUR_DATES,
    PROPAGATE_TOUR_DATA,
    WARN_VEHICLE_CONFLICT,
    SYNC_TOUR_DATA_CHANGES,
    WORK_LOG_TO_CHATTER,
    RECALC_HOURS_ON_WRITE,
    RECALC_HOURS_ON_UNLINK,
    RECALC_ON_ALLOCATED_CHANGE,
)

app = typer.Typer(help="Setup fleet automations and task fields for tours")


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
    existing = _field_exists(client, field_def['model'], field_def['name'])
    if existing:
        return existing, False
    vals = {**field_def, 'model_id': model_id, 'store': True}
    result = client.execute('ir.model.fields', 'create', [vals])
    fid = result[0] if isinstance(result, list) else result
    return fid, True


def _get_field_id(client, model_name, field_name):
    result = client.search_read('ir.model.fields',
        domain=[['model', '=', model_name], ['name', '=', field_name]],
        fields=['id'], limit=1)
    return result[0]['id'] if result else False


def _create_model(client, name, model_name):
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


def _create_or_update_automation(client, name, model_id, trigger, trigger_field_ids, code):
    """Create or update a base.automation with its server action."""
    existing = client.search_read('base.automation',
        domain=[['name', '=', name]],
        fields=['id', 'action_server_ids'])

    if existing:
        auto_id = existing[0]['id']
        action_ids = existing[0].get('action_server_ids', [])
        if action_ids:
            client.execute('ir.actions.server', 'write', [action_ids[0]], {'code': code})
        client.execute('base.automation', 'write', [auto_id], {
            'trigger': trigger,
            'trigger_field_ids': [(6, 0, trigger_field_ids)] if trigger_field_ids else [(5, 0, 0)],
        })
        return auto_id, False
    else:
        action_result = client.execute('ir.actions.server', 'create', [{
            'name': name,
            'model_id': model_id,
            'state': 'code',
            'code': code,
        }])
        action_id = action_result[0] if isinstance(action_result, list) else action_result

        auto_result = client.execute('base.automation', 'create', [{
            'name': name,
            'model_id': model_id,
            'trigger': trigger,
            'trigger_field_ids': [(6, 0, trigger_field_ids)] if trigger_field_ids else [],
            'action_server_ids': [(6, 0, [action_id])],
            'active': True,
        }])
        auto_id = auto_result[0] if isinstance(auto_result, list) else auto_result
        return auto_id, True


# ── Task form view ────────────────────────────────────────────────────────

TASK_FORM_VIEW_ARCH = '''<data>
    <xpath expr="//div[@id='date_deadline_and_recurring_task']" position="after">
        <field name="x_assigned_operator_id" string="Operador Asignado" domain="[('customer_rank', '=', 0)]" options="{'no_create': True}"/>
        <field name="x_operator_ids" string="Operadores Asignados" widget="many2many_tags" invisible="not parent_id" domain="[('customer_rank', '=', 0)]" options="{'no_create': True, 'color_field': 'color'}"/>
        <field name="x_use_internal_users" invisible="parent_id"/>
        <field name="x_tour_start_date" readonly="1"/>
        <field name="x_tour_end_date" readonly="1"/>
        <field name="x_is_fleet_task"/>
        <label for="x_vehicle_id" invisible="not x_is_fleet_task"/>
        <field name="x_vehicle_id" nolabel="1" invisible="not x_is_fleet_task" options="{'no_create': True}"/>
        <label for="x_driver_id" invisible="not x_is_fleet_task"/>
        <field name="x_driver_id" nolabel="1" invisible="not x_is_fleet_task" options="{'no_create': True}"/>
        <label for="x_seats_needed" invisible="not x_is_fleet_task"/>
        <field name="x_seats_needed" nolabel="1" invisible="not x_is_fleet_task"/>
        <label for="x_available_seats" invisible="not x_is_fleet_task or not x_vehicle_id"/>
        <field name="x_available_seats" nolabel="1" invisible="not x_is_fleet_task or not x_vehicle_id" readonly="1"/>
    </xpath>
    <xpath expr="//page[@name='extra_info']" position="before">
        <page string="Registro de Trabajo" name="work_log">
            <group>
                <group>
                    <field name="allocated_hours" string="Horas Asignadas" widget="float_time"/>
                    <field name="x_total_hours_logged" string="Horas Registradas" widget="float_time" readonly="1"/>
                </group>
                <group>
                    <field name="x_remaining_hours" string="Horas Restantes" widget="float_time" readonly="1"/>
                </group>
            </group>
            <field name="x_work_log_ids">
                <list editable="bottom" default_order="x_date desc, id desc">
                    <control><create string="Agregar registro"/></control>
                    <field name="x_date" string="Fecha"/>
                    <field name="x_partner_id" string="Operador/Contacto" required="1" domain="[('customer_rank', '=', 0)]" options="{'no_create': True}"/>
                    <field name="x_service_type" string="Tipo de Servicio"/>
                    <field name="x_description" string="Descripcion"/>
                    <field name="x_hours_spent" string="Horas" widget="float_time" sum="Total"/>
                </list>
            </field>
        </page>
    </xpath>
    <xpath expr="//field[@name='child_ids']//field[@name='user_ids']" position="replace">
        <field name="x_operator_ids" string="Operadores Asignados" widget="many2many_tags" domain="[('customer_rank', '=', 0)]" options="{'no_create': True, 'color_field': 'color'}"/>
        <field name="user_ids" string="Usuarios Internos" widget="many2many_avatar_user" column_invisible="not parent.x_use_internal_users"/>
    </xpath>
</data>'''

TASK_FORM_VIEW_NAME = 'project.task.form.inherit.agency_fields'


@app.command()
def setup():
    """Create fleet fields, task view, and tour automations."""
    client = OdooClient()
    client.connect()

    typer.secho("=" * 70, bold=True)
    typer.secho("  FLEET AUTOMATIONS & TASK FIELDS SETUP", bold=True)
    typer.secho("=" * 70, bold=True)

    # ── 1. Fields on sale.order (tour-specific) ───────────────────────
    typer.secho("\n1. Tour fields on sale.order", bold=True)
    so_model_id = _get_model_id(client, 'sale.order')
    so_tour_fields = [
        {'name': 'x_is_tour', 'field_description': 'Es un Tour', 'ttype': 'boolean', 'model': 'sale.order'},
        {'name': 'x_tour_start_date', 'field_description': 'Fecha Inicio del Tour', 'ttype': 'date', 'model': 'sale.order'},
        {'name': 'x_tour_end_date', 'field_description': 'Fecha Fin del Tour', 'ttype': 'date', 'model': 'sale.order'},
        {'name': 'x_num_passengers', 'field_description': 'Numero de Pasajeros', 'ttype': 'integer', 'model': 'sale.order'},
    ]
    for fdef in so_tour_fields:
        fid, created = _create_field(client, fdef, so_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']}", fg=typer.colors.GREEN)

    # ── 2. Fields on project.task ─────────────────────────────────────
    typer.secho("\n2. Fleet/tour fields on project.task", bold=True)
    task_model_id = _get_model_id(client, 'project.task')
    task_fields = [
        {'name': 'x_tour_start_date', 'field_description': 'Fecha Inicio del Tour', 'ttype': 'date', 'model': 'project.task'},
        {'name': 'x_tour_end_date', 'field_description': 'Fecha Fin del Tour', 'ttype': 'date', 'model': 'project.task'},
        {'name': 'x_is_fleet_task', 'field_description': 'Requiere vehiculo propio', 'ttype': 'boolean', 'model': 'project.task'},
        {'name': 'x_vehicle_id', 'field_description': 'Vehiculo Asignado', 'ttype': 'many2one',
         'relation': 'fleet.vehicle', 'model': 'project.task'},
        {'name': 'x_driver_id', 'field_description': 'Chofer Asignado', 'ttype': 'many2one',
         'relation': 'res.partner', 'model': 'project.task'},
        {'name': 'x_seats_needed', 'field_description': 'Asientos Necesarios', 'ttype': 'integer', 'model': 'project.task'},
        {'name': 'x_available_seats', 'field_description': 'Asientos Disponibles', 'ttype': 'integer', 'model': 'project.task'},
        {'name': 'x_assigned_operator_id', 'field_description': 'Operador Asignado', 'ttype': 'many2one',
         'relation': 'res.partner', 'model': 'project.task'},
        {'name': 'x_total_hours_logged', 'field_description': 'Horas Registradas', 'ttype': 'float', 'model': 'project.task'},
        {'name': 'x_remaining_hours', 'field_description': 'Horas Restantes', 'ttype': 'float', 'model': 'project.task'},
        {'name': 'x_operator_ids', 'field_description': 'Operadores Asignados', 'ttype': 'many2many',
         'relation': 'res.partner', 'model': 'project.task'},
        {'name': 'x_use_internal_users', 'field_description': 'Mostrar Usuarios Internos', 'ttype': 'boolean', 'model': 'project.task'},
    ]
    for fdef in task_fields:
        fid, created = _create_field(client, fdef, task_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']}", fg=typer.colors.GREEN)

    # ── 2b. Model x_task_work_log ──────────────────────────────────────
    typer.secho("\n2b. Model x_task_work_log", bold=True)
    wl_model_id, created = _create_model(client, 'Task Work Log', 'x_task_work_log')
    typer.secho(f"  [{'CREATED' if created else 'OK'}] Model (id={wl_model_id})", fg=typer.colors.GREEN)

    # ── 2c. Fields on x_task_work_log ──────────────────────────────────
    typer.secho("\n2c. Fields on x_task_work_log", bold=True)
    work_log_fields = [
        {'name': 'x_sequence', 'field_description': 'Secuencia', 'ttype': 'integer', 'model': 'x_task_work_log'},
        {'name': 'x_task_id', 'field_description': 'Tarea', 'ttype': 'many2one',
         'relation': 'project.task', 'on_delete': 'cascade', 'model': 'x_task_work_log'},
        {'name': 'x_partner_id', 'field_description': 'Operador/Contacto', 'ttype': 'many2one',
         'relation': 'res.partner', 'model': 'x_task_work_log'},
        {'name': 'x_service_type', 'field_description': 'Tipo de Servicio', 'ttype': 'selection',
         'selection_ids': [
             (0, 0, {'value': 'transporte', 'name': 'Transporte', 'sequence': 1}),
             (0, 0, {'value': 'tren', 'name': 'Tren', 'sequence': 2}),
             (0, 0, {'value': 'guia', 'name': 'Guía', 'sequence': 3}),
             (0, 0, {'value': 'hotel', 'name': 'Hotel', 'sequence': 4}),
             (0, 0, {'value': 'restaurante', 'name': 'Restaurante', 'sequence': 5}),
             (0, 0, {'value': 'coordinacion', 'name': 'Coordinación', 'sequence': 6}),
             (0, 0, {'value': 'otros', 'name': 'Otros', 'sequence': 7}),
         ], 'model': 'x_task_work_log'},
        {'name': 'x_description', 'field_description': 'Descripcion', 'ttype': 'text', 'model': 'x_task_work_log'},
        {'name': 'x_date', 'field_description': 'Fecha', 'ttype': 'date', 'model': 'x_task_work_log'},
        {'name': 'x_hours_spent', 'field_description': 'Horas', 'ttype': 'float', 'model': 'x_task_work_log'},
    ]
    for fdef in work_log_fields:
        fid, created = _create_field(client, fdef, wl_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']} ({fdef['ttype']})", fg=typer.colors.GREEN)

    # ── 2d. ACL for x_task_work_log ────────────────────────────────────
    typer.secho("\n2d. ACL for x_task_work_log", bold=True)
    acl_id, created = _ensure_acl(client, 'access_x_task_work_log_user', wl_model_id)
    typer.secho(f"  [{'CREATED' if created else 'OK'}] ACL (id={acl_id})", fg=typer.colors.GREEN)

    # ── 2e. One2many on project.task → x_task_work_log ─────────────────
    typer.secho("\n2e. Work log o2m on project.task", bold=True)
    wl_o2m = {'name': 'x_work_log_ids', 'field_description': 'Registro de Trabajo',
              'ttype': 'one2many', 'relation': 'x_task_work_log', 'relation_field': 'x_task_id',
              'model': 'project.task'}
    fid, created = _create_field(client, wl_o2m, task_model_id)
    typer.secho(f"  [{'CREATED' if created else 'OK'}] x_work_log_ids (one2many)", fg=typer.colors.GREEN)

    # ── 3. Task form view ─────────────────────────────────────────────
    typer.secho("\n3. Task form view with fleet fields", bold=True)
    existing_view = client.search_read('ir.ui.view',
        domain=[['name', '=', TASK_FORM_VIEW_NAME]], fields=['id'])
    if existing_view:
        view_id = existing_view[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': TASK_FORM_VIEW_ARCH})
        typer.secho(f"  [UPDATED] View {view_id}", fg=typer.colors.GREEN)
    else:
        # Find base project.task form view dynamically
        base_task_view = client.search_read('ir.ui.view',
            domain=[['model', '=', 'project.task'], ['type', '=', 'form'],
                    ['inherit_id', '=', False], ['mode', '=', 'primary']],
            fields=['id', 'name'], limit=1)
        if not base_task_view:
            typer.secho("  [ERROR] Base project.task form view not found!", fg=typer.colors.RED)
            raise typer.Exit(1)
        base_view_id = base_task_view[0]['id']
        typer.secho(f"  Base view: {base_task_view[0]['name']} (id={base_view_id})", fg=typer.colors.CYAN)
        result = client.execute('ir.ui.view', 'create', [{
            'name': TASK_FORM_VIEW_NAME,
            'model': 'project.task',
            'inherit_id': base_view_id,
            'type': 'form',
            'arch': TASK_FORM_VIEW_ARCH,
            'priority': 99,
        }])
        view_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] View {view_id}", fg=typer.colors.GREEN)

    # ── 4. Automation: Validate Tour Dates ────────────────────────────
    typer.secho("\n4. Automation: Validate Tour Dates", bold=True)
    trigger_fields_15 = [
        _get_field_id(client, 'sale.order', 'x_tour_start_date'),
        _get_field_id(client, 'sale.order', 'x_tour_end_date'),
    ]
    trigger_fields_15 = [f for f in trigger_fields_15 if f]
    auto_id, created = _create_or_update_automation(
        client, 'Validate Tour Dates', so_model_id,
        'on_write', trigger_fields_15, VALIDATE_TOUR_DATES)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── 5. Automation: Propagate Tour Data to Tasks ───────────────────
    typer.secho("\n5. Automation: Propagate Tour Data to Tasks", bold=True)
    # on_state_set requires the state field
    state_field_id = _get_field_id(client, 'sale.order', 'state')
    auto_id, created = _create_or_update_automation(
        client, 'Propagate Tour Data to Tasks', so_model_id,
        'on_state_set', [state_field_id] if state_field_id else [], PROPAGATE_TOUR_DATA)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── 6. Automation: Warn Vehicle Date Conflict ─────────────────────
    typer.secho("\n6. Automation: Warn Vehicle Date Conflict", bold=True)
    trigger_fields_17 = [
        _get_field_id(client, 'project.task', 'x_seats_needed'),
        _get_field_id(client, 'project.task', 'x_tour_end_date'),
        _get_field_id(client, 'project.task', 'x_tour_start_date'),
        _get_field_id(client, 'project.task', 'x_vehicle_id'),
    ]
    trigger_fields_17 = [f for f in trigger_fields_17 if f]
    auto_id, created = _create_or_update_automation(
        client, 'Warn Vehicle Date Conflict', task_model_id,
        'on_write', trigger_fields_17, WARN_VEHICLE_CONFLICT)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── 7. Automation: Sync Tour Data Changes to Tasks ────────────────
    typer.secho("\n7. Automation: Sync Tour Data Changes to Tasks", bold=True)
    trigger_fields_18 = [
        _get_field_id(client, 'sale.order', 'x_service_type'),
        _get_field_id(client, 'sale.order', 'x_num_passengers'),
        _get_field_id(client, 'sale.order', 'x_departure_city'),
        _get_field_id(client, 'sale.order', 'x_tour_start_date'),
        _get_field_id(client, 'sale.order', 'x_tour_end_date'),
    ]
    trigger_fields_18 = [f for f in trigger_fields_18 if f]
    auto_id, created = _create_or_update_automation(
        client, 'Sync Tour Data Changes to Tasks', so_model_id,
        'on_write', trigger_fields_18, SYNC_TOUR_DATA_CHANGES)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── 8. Automation: Work Log → Task Chatter + Recalc ────────────
    typer.secho("\n8. Automation: Work Log to Task Chatter + Recalc Hours", bold=True)
    auto_id, created = _create_or_update_automation(
        client, 'Work Log: Post to Task Chatter', wl_model_id,
        'on_create', [], WORK_LOG_TO_CHATTER)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── 9. Automation: Work Log Edit → Chatter + Recalc ─────────────
    typer.secho("\n9. Automation: Work Log Edit → Chatter + Recalc", bold=True)
    trigger_fields_21 = [
        _get_field_id(client, 'x_task_work_log', 'x_hours_spent'),
        _get_field_id(client, 'x_task_work_log', 'x_partner_id'),
        _get_field_id(client, 'x_task_work_log', 'x_service_type'),
        _get_field_id(client, 'x_task_work_log', 'x_description'),
    ]
    trigger_fields_21 = [f for f in trigger_fields_21 if f]
    auto_id, created = _create_or_update_automation(
        client, 'Work Log: Recalc Hours on Edit', wl_model_id,
        'on_write', trigger_fields_21, RECALC_HOURS_ON_WRITE)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── 10. Automation: Recalc Hours on Work Log Delete ──────────────
    typer.secho("\n10. Automation: Recalc Hours on Work Log Delete", bold=True)
    auto_id, created = _create_or_update_automation(
        client, 'Work Log: Recalc Hours on Delete', wl_model_id,
        'on_unlink', [], RECALC_HOURS_ON_UNLINK)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── 11. Automation: Recalc Remaining on Allocated Hours Change ───
    typer.secho("\n11. Automation: Recalc Remaining on Allocated Hours Change", bold=True)
    allocated_field_id = _get_field_id(client, 'project.task', 'allocated_hours')
    trigger_fields_23 = [allocated_field_id] if allocated_field_id else []
    auto_id, created = _create_or_update_automation(
        client, 'Task: Recalc Remaining on Allocated Change', task_model_id,
        'on_write', trigger_fields_23, RECALC_ON_ALLOCATED_CHANGE)
    typer.secho(f"  [{'CREATED' if created else 'UPDATED'}] Automation {auto_id}", fg=typer.colors.GREEN)

    # ── Summary ───────────────────────────────────────────────────────
    typer.secho("\n" + "=" * 70, bold=True)
    typer.secho("  FLEET AUTOMATIONS SETUP COMPLETE", fg=typer.colors.BLUE, bold=True)
    typer.secho("=" * 70, bold=True)
    typer.secho("\nFields:", fg=typer.colors.CYAN)
    typer.secho("  sale.order: x_is_tour, x_tour_start_date, x_tour_end_date, x_num_passengers", fg=typer.colors.CYAN)
    typer.secho("  project.task: x_tour_start/end_date, x_is_fleet_task, x_vehicle_id, x_driver_id,", fg=typer.colors.CYAN)
    typer.secho("                x_seats_needed, x_available_seats, x_assigned_operator_id,", fg=typer.colors.CYAN)
    typer.secho("                x_work_log_ids, x_total_hours_logged, x_remaining_hours,", fg=typer.colors.CYAN)
    typer.secho("                x_operator_ids (m2m, subtasks only)", fg=typer.colors.CYAN)
    typer.secho("  x_task_work_log: x_task_id, x_partner_id, x_service_type, x_description, x_date, x_hours_spent", fg=typer.colors.CYAN)
    typer.secho("\nAutomations:", fg=typer.colors.CYAN)
    typer.secho("  - Validate Tour Dates: end >= start", fg=typer.colors.CYAN)
    typer.secho("  - Propagate Tour Data: SO confirmation -> task dates + seats", fg=typer.colors.CYAN)
    typer.secho("  - Warn Vehicle Conflict: blocks private conflicts, warns capacity overflow", fg=typer.colors.CYAN)
    typer.secho("  - Sync Tour Data Changes: SO edits -> task updates + private warnings", fg=typer.colors.CYAN)
    typer.secho("  - Work Log to Chatter: posts + recalculates hours on create", fg=typer.colors.CYAN)
    typer.secho("  - Recalc Hours on Edit: updates totals when hours modified", fg=typer.colors.CYAN)
    typer.secho("  - Recalc Hours on Delete: updates totals when log entry removed", fg=typer.colors.CYAN)
    typer.secho("  - Recalc Remaining on Allocated: updates remaining when budget changes", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
