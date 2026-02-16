#!/usr/bin/env python3
"""Setup tour groups model, fields, views, and menu.

Creates:
- Model x_tour_group (operational passenger groups for tours)
- Fields on x_tour_group (name, dates, capacity, passengers, notes, color)
- Reverse fields: x_sale_order_ids (m2m reverse), x_task_ids (o2m via x_tour_group_id)
- ACL for x_tour_group (full CRUD, group_id=1)
- Field x_tour_group_ids (m2m) on sale.order
- Field x_tour_group_id (m2o) on x_guests_line (per-passenger group assignment)
- Form + List views for x_tour_group
- Window action + menu item under Sales

Depends on: setup_fleet_automations.py (creates x_tour_group_id on project.task)

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_tour_groups.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from agency.defaults.views import TOUR_GROUP_FORM_ARCH, TOUR_GROUP_LIST_ARCH

app = typer.Typer(help="Setup tour groups model and views")


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


@app.command()
def setup():
    """Create tour groups model, fields, views, and menu."""
    client = OdooClient()
    client.connect()

    typer.secho("=" * 70, bold=True)
    typer.secho("  TOUR GROUPS SETUP", bold=True)
    typer.secho("=" * 70, bold=True)

    # ── 1. Create model x_tour_group ──────────────────────────────────
    typer.secho("\n1. Model x_tour_group", bold=True)
    group_model_id, created = _create_model(client, 'Tour Group', 'x_tour_group')
    typer.secho(f"  [{'CREATED' if created else 'OK'}] Model (id={group_model_id})", fg=typer.colors.GREEN)

    # ── 2. Fields on x_tour_group ─────────────────────────────────────
    typer.secho("\n2. Fields on x_tour_group", bold=True)
    group_fields = [
        {'name': 'x_start_date', 'field_description': 'Fecha Inicio', 'ttype': 'date',
         'model': 'x_tour_group'},
        {'name': 'x_end_date', 'field_description': 'Fecha Fin', 'ttype': 'date',
         'model': 'x_tour_group'},
        {'name': 'x_max_capacity', 'field_description': 'Capacidad Maxima', 'ttype': 'integer',
         'model': 'x_tour_group'},
        {'name': 'x_passenger_ids', 'field_description': 'Pasajeros', 'ttype': 'many2many',
         'relation': 'res.partner', 'model': 'x_tour_group'},
        {'name': 'x_notes', 'field_description': 'Notas Operativas', 'ttype': 'text',
         'model': 'x_tour_group'},
        {'name': 'x_color', 'field_description': 'Color', 'ttype': 'integer',
         'model': 'x_tour_group'},
    ]
    for fdef in group_fields:
        fid, created = _create_field(client, fdef, group_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] {fdef['name']} ({fdef['ttype']})", fg=typer.colors.GREEN)

    # ── 3. ACL for x_tour_group ───────────────────────────────────────
    typer.secho("\n3. ACL for x_tour_group", bold=True)
    acl_id, created = _ensure_acl(client, 'access_x_tour_group_user', group_model_id)
    typer.secho(f"  [{'CREATED' if created else 'OK'}] ACL (id={acl_id})", fg=typer.colors.GREEN)

    # ── 4. Field x_tour_group_ids on sale.order ───────────────────────
    typer.secho("\n4. Field x_tour_group_ids on sale.order", bold=True)
    so_model_id = _get_model_id(client, 'sale.order')
    so_group_field = {
        'name': 'x_tour_group_ids', 'field_description': 'Grupos de Tour',
        'ttype': 'many2many', 'relation': 'x_tour_group', 'model': 'sale.order',
    }
    fid, created = _create_field(client, so_group_field, so_model_id)
    typer.secho(f"  [{'CREATED' if created else 'OK'}] x_tour_group_ids (many2many)", fg=typer.colors.GREEN)

    # ── 4b. Reverse m2m: x_sale_order_ids on x_tour_group ─────────────
    typer.secho("\n4b. Reverse m2m x_sale_order_ids on x_tour_group", bold=True)
    # Query the existing x_tour_group_ids field to get its relation_table
    so_m2m_field = client.search_read('ir.model.fields',
        domain=[['model', '=', 'sale.order'], ['name', '=', 'x_tour_group_ids']],
        fields=['relation_table', 'column1', 'column2'], limit=1)
    if so_m2m_field:
        rel_table = so_m2m_field[0]['relation_table']
        col1 = so_m2m_field[0]['column1']
        col2 = so_m2m_field[0]['column2']
        typer.secho(f"  Source field: table={rel_table}, col1={col1}, col2={col2}", fg=typer.colors.CYAN)
        reverse_field = {
            'name': 'x_sale_order_ids', 'field_description': 'Ventas Vinculadas',
            'ttype': 'many2many', 'relation': 'sale.order', 'model': 'x_tour_group',
            'relation_table': rel_table, 'column1': col2, 'column2': col1,
        }
        fid, created = _create_field(client, reverse_field, group_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] x_sale_order_ids (many2many reverse)", fg=typer.colors.GREEN)
    else:
        typer.secho("  [SKIP] x_tour_group_ids not found on sale.order", fg=typer.colors.YELLOW)

    # ── 4c. One2many: x_task_ids on x_tour_group ──────────────────────
    typer.secho("\n4c. One2many x_task_ids on x_tour_group", bold=True)
    task_o2m = {
        'name': 'x_task_ids', 'field_description': 'Tareas de Flota',
        'ttype': 'one2many', 'relation': 'project.task', 'relation_field': 'x_tour_group_id',
        'model': 'x_tour_group',
    }
    fid, created = _create_field(client, task_o2m, group_model_id)
    typer.secho(f"  [{'CREATED' if created else 'OK'}] x_task_ids (one2many)", fg=typer.colors.GREEN)

    # ── 4d. Field x_tour_group_id on x_guests_line ────────────────────
    typer.secho("\n4d. Field x_tour_group_id on x_guests_line", bold=True)
    gl_model_id = _get_model_id(client, 'x_guests_line')
    if gl_model_id:
        gl_group_field = {
            'name': 'x_tour_group_id', 'field_description': 'Grupo de Tour',
            'ttype': 'many2one', 'relation': 'x_tour_group', 'model': 'x_guests_line',
        }
        fid, created = _create_field(client, gl_group_field, gl_model_id)
        typer.secho(f"  [{'CREATED' if created else 'OK'}] x_tour_group_id (many2one)", fg=typer.colors.GREEN)
    else:
        typer.secho("  [SKIP] x_guests_line model not found", fg=typer.colors.YELLOW)

    # ── 5. Form view for x_tour_group ─────────────────────────────────
    typer.secho("\n5. Form view for x_tour_group", bold=True)
    form_view_name = 'x_tour_group.form.agency'
    existing_form = client.search_read('ir.ui.view',
        domain=[['name', '=', form_view_name]], fields=['id'])
    if existing_form:
        view_id = existing_form[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': TOUR_GROUP_FORM_ARCH})
        typer.secho(f"  [UPDATED] Form view (id={view_id})", fg=typer.colors.GREEN)
    else:
        result = client.execute('ir.ui.view', 'create', [{
            'name': form_view_name,
            'model': 'x_tour_group',
            'type': 'form',
            'arch': TOUR_GROUP_FORM_ARCH,
            'priority': 16,
        }])
        view_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] Form view (id={view_id})", fg=typer.colors.GREEN)
    form_view_id = view_id

    # ── 6. List view for x_tour_group ─────────────────────────────────
    typer.secho("\n6. List view for x_tour_group", bold=True)
    list_view_name = 'x_tour_group.list.agency'
    existing_list = client.search_read('ir.ui.view',
        domain=[['name', '=', list_view_name]], fields=['id'])
    if existing_list:
        view_id = existing_list[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': TOUR_GROUP_LIST_ARCH})
        typer.secho(f"  [UPDATED] List view (id={view_id})", fg=typer.colors.GREEN)
    else:
        result = client.execute('ir.ui.view', 'create', [{
            'name': list_view_name,
            'model': 'x_tour_group',
            'type': 'list',
            'arch': TOUR_GROUP_LIST_ARCH,
            'priority': 16,
        }])
        view_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] List view (id={view_id})", fg=typer.colors.GREEN)
    list_view_id = view_id

    # ── 7. Window action ──────────────────────────────────────────────
    typer.secho("\n7. Window action for x_tour_group", bold=True)
    action_name = 'Grupos de Tour'
    existing_action = client.search_read('ir.actions.act_window',
        domain=[['name', '=', action_name], ['res_model', '=', 'x_tour_group']],
        fields=['id'])
    if existing_action:
        action_id = existing_action[0]['id']
        client.execute('ir.actions.act_window', 'write', [action_id], {
            'view_mode': 'list,form',
        })
        typer.secho(f"  [OK] Action (id={action_id})", fg=typer.colors.GREEN)
    else:
        result = client.execute('ir.actions.act_window', 'create', [{
            'name': action_name,
            'res_model': 'x_tour_group',
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }])
        action_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] Action (id={action_id})", fg=typer.colors.GREEN)

    # ── 8. Menu item under Sales ──────────────────────────────────────
    typer.secho("\n8. Menu item under Sales", bold=True)
    menu_name = 'Grupos de Tour'
    existing_menu = client.search_read('ir.ui.menu',
        domain=[['name', '=', menu_name], ['action', '=', f'ir.actions.act_window,{action_id}']],
        fields=['id'])
    if existing_menu:
        typer.secho(f"  [OK] Menu (id={existing_menu[0]['id']})", fg=typer.colors.GREEN)
    else:
        # Find "Orders" parent menu under Sales
        # First find the root Sales menu, then find Orders under it
        parent_id = False
        sales_menu = client.search_read('ir.ui.menu',
            domain=[['name', '=', 'Sales'], ['parent_id', '=', False]],
            fields=['id'], limit=1)
        if sales_menu:
            sales_root_id = sales_menu[0]['id']
            orders_menu = client.search_read('ir.ui.menu',
                domain=[['name', '=', 'Orders'], ['parent_id', '=', sales_root_id]],
                fields=['id'], limit=1)
            if orders_menu:
                parent_id = orders_menu[0]['id']
                typer.secho(f"  Parent menu: Sales > Orders (id={parent_id})", fg=typer.colors.CYAN)
            else:
                parent_id = sales_root_id
                typer.secho(f"  Parent menu: Sales (id={parent_id})", fg=typer.colors.CYAN)

        result = client.execute('ir.ui.menu', 'create', [{
            'name': menu_name,
            'action': f'ir.actions.act_window,{action_id}',
            'parent_id': parent_id,
            'sequence': 15,
        }])
        menu_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] Menu (id={menu_id})", fg=typer.colors.GREEN)

    # ── Summary ───────────────────────────────────────────────────────
    typer.secho("\n" + "=" * 70, bold=True)
    typer.secho("  TOUR GROUPS SETUP COMPLETE", fg=typer.colors.BLUE, bold=True)
    typer.secho("=" * 70, bold=True)
    typer.secho("\nModel:", fg=typer.colors.CYAN)
    typer.secho("  x_tour_group: x_name, x_start_date, x_end_date, x_max_capacity, x_passenger_ids, x_notes, x_color", fg=typer.colors.CYAN)
    typer.secho("  + x_sale_order_ids (m2m reverse → sale.order)", fg=typer.colors.CYAN)
    typer.secho("  + x_task_ids (o2m → project.task via x_tour_group_id)", fg=typer.colors.CYAN)
    typer.secho("\nFields on existing models:", fg=typer.colors.CYAN)
    typer.secho("  sale.order: x_tour_group_ids (many2many)", fg=typer.colors.CYAN)
    typer.secho("  project.task: x_tour_group_id (many2one) — created by setup_fleet_automations.py", fg=typer.colors.CYAN)
    typer.secho("  x_guests_line: x_tour_group_id (many2one) — per-passenger group", fg=typer.colors.CYAN)
    typer.secho("\nViews:", fg=typer.colors.CYAN)
    typer.secho(f"  Form: {form_view_name} (id={form_view_id})", fg=typer.colors.CYAN)
    typer.secho(f"  List: {list_view_name} (id={list_view_id})", fg=typer.colors.CYAN)
    typer.secho(f"\nAction: {action_name} (id={action_id})", fg=typer.colors.CYAN)
    typer.secho("\nNext steps:", fg=typer.colors.YELLOW)
    typer.secho("  1. Run setup_fleet_automations.py to add x_tour_group_id to task form", fg=typer.colors.YELLOW)
    typer.secho("  2. Run setup_biblia_operativa.py to update SO form with x_tour_group_ids", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
