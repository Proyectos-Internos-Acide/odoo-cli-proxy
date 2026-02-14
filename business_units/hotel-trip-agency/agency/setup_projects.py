#!/usr/bin/env python3
"""Create project template with standard tasks for tour operations.

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_projects.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from defaults.categories import CATEGORIES
from agency.defaults.projects import TEMPLATE_NAME, STANDARD_TASKS, TEMPLATE_STAGES

app = typer.Typer(help="Configure project templates for travel agency")


@app.command()
def setup():
    """Create project template with standard tasks."""
    client = OdooClient()
    client.connect()
    changes = 0

    typer.secho("=" * 60, bold=True)
    typer.secho("  PROJECT TEMPLATE CONFIGURATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # ---------------------------------------------------------------
    # 1. Check/Create project template
    # ---------------------------------------------------------------
    typer.secho(f"\n1. Project template: {TEMPLATE_NAME}", bold=True)

    existing = client.search_read('project.project',
        domain=[['name', '=', TEMPLATE_NAME], ['is_template', '=', True]],
        fields=['id', 'name', 'task_count'])

    if existing:
        template_id = existing[0]['id']
        typer.secho(f"  [OK] Template already exists (id={template_id}, tasks={existing[0]['task_count']})",
            fg=typer.colors.GREEN)
    else:
        regular = client.search_read('project.project',
            domain=[['name', '=', TEMPLATE_NAME]],
            fields=['id', 'is_template'])
        if regular:
            template_id = regular[0]['id']
            if not regular[0].get('is_template'):
                client.execute('project.project', 'write', [template_id], {'is_template': True})
                typer.secho(f"  [FIXED] Existing project converted to template (id={template_id})",
                    fg=typer.colors.GREEN)
                changes += 1
        else:
            result = client.execute('project.project', 'create', [{
                'name': TEMPLATE_NAME,
                'is_template': True,
                'allow_billable': True,
            }])
            template_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] Template id={template_id}", fg=typer.colors.GREEN)
            changes += 1

    # ---------------------------------------------------------------
    # 2. Create kanban stages for the template
    # ---------------------------------------------------------------
    typer.secho("\n2. Kanban stages", bold=True)

    existing_stages = client.search_read('project.task.type',
        domain=[['project_ids', 'in', [template_id]]],
        fields=['name'])
    existing_stage_names = {s['name'] for s in existing_stages}
    pendientes_stage_id = None

    for stage_def in TEMPLATE_STAGES:
        if stage_def['name'] in existing_stage_names:
            stage = [s for s in existing_stages if s['name'] == stage_def['name']][0]
            typer.secho(f"  [OK] {stage_def['name']} (id={stage['id']})", fg=typer.colors.GREEN)
            if stage_def['name'] == 'Pendientes':
                pendientes_stage_id = stage['id']
        else:
            result = client.execute('project.task.type', 'create', [{
                'name': stage_def['name'],
                'sequence': stage_def['sequence'],
                'project_ids': [(4, template_id)],
            }])
            sid = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] {stage_def['name']} (id={sid})", fg=typer.colors.GREEN)
            if stage_def['name'] == 'Pendientes':
                pendientes_stage_id = sid
            changes += 1

    # ---------------------------------------------------------------
    # 3. Create standard tasks in the template
    # ---------------------------------------------------------------
    typer.secho("\n3. Standard tasks", bold=True)

    existing_tasks = client.search_read('project.task',
        domain=[['project_id', '=', template_id]],
        fields=['name', 'stage_id'])
    existing_names = {et['name'] for et in existing_tasks}

    for task_def in STANDARD_TASKS:
        task_name = task_def['name']
        if task_name in existing_names:
            task = [t for t in existing_tasks if t['name'] == task_name][0]
            # Fix stage if missing
            if not task['stage_id'] and pendientes_stage_id:
                client.execute('project.task', 'write', [task['id']], {'stage_id': pendientes_stage_id})
                typer.secho(f"  [FIXED] {task_name} -> Pendientes", fg=typer.colors.GREEN)
                changes += 1
            else:
                typer.secho(f"  [OK] {task_name} (already exists)", fg=typer.colors.GREEN)
        else:
            vals = {
                'name': task_name,
                'description': task_def['description'],
                'project_id': template_id,
            }
            if pendientes_stage_id:
                vals['stage_id'] = pendientes_stage_id
            result = client.execute('project.task', 'create', [vals])
            task_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] {task_name}", fg=typer.colors.GREEN)
            changes += 1

    # ---------------------------------------------------------------
    # 4. Link tour products to the project template
    # ---------------------------------------------------------------
    typer.secho("\n4. Link tour products to template", bold=True)

    tour_products = client.search_read('product.template',
        domain=[['categ_id', '=', CATEGORIES['tours_packages']]],
        fields=['name', 'service_tracking', 'project_template_id'])

    for p in tour_products:
        current_tmpl = p.get('project_template_id')
        tracking = p.get('service_tracking', 'no')

        if tracking not in ('task_in_project', 'project_only'):
            typer.secho(f"  [SKIP] {p['name']}: tracking={tracking} (not project-based)",
                fg=typer.colors.YELLOW)
            continue

        if current_tmpl and current_tmpl[0] == template_id:
            typer.secho(f"  [OK] {p['name']}: already linked to template",
                fg=typer.colors.GREEN)
        else:
            try:
                client.execute('product.template', 'write', [p['id']],
                    {'project_template_id': template_id})
                typer.secho(f"  [LINKED] {p['name']} -> {TEMPLATE_NAME}",
                    fg=typer.colors.GREEN)
                changes += 1
            except Exception as e:
                typer.secho(f"  [ERROR] {p['name']}: {str(e)[:80]}", fg=typer.colors.RED)

    # ---------------------------------------------------------------
    # 5. Show existing projects
    # ---------------------------------------------------------------
    typer.secho("\n5. Existing projects", bold=True)

    projects = client.search_read('project.project', domain=[],
        fields=['name', 'is_template', 'task_count', 'partner_id'])
    for p in projects:
        ptype = "TEMPLATE" if p.get('is_template') else "PROJECT"
        partner = p.get('partner_id', [None, ''])[1] if p.get('partner_id') else '-'
        typer.secho(f"  [{ptype}] {p['name']} | tasks={p.get('task_count', 0)} | partner={partner}",
            fg=typer.colors.CYAN)

    typer.secho(f"\nDone. {changes} changes made.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
