#!/usr/bin/env python3
"""Configure POS categories and preparation display for restaurant.

Usage:
    uv run python business_units/hotel-trip-agency/restaurant/setup_pos.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import typer
from odoo_cli import OdooClient
from defaults.i18n import t, write_translations, search_translatable
from restaurant.defaults.pos_categories import (
    POS_CATEGORIES, PREP_DISPLAY_NAME, PREP_STAGES,
)

app = typer.Typer(help="Configure POS categories and prep display for restaurant")


@app.command()
def setup():
    """Create/verify POS categories, prep display, and show POS summary."""
    client = OdooClient()
    client.connect()
    changes = 0

    typer.secho("=" * 60, bold=True)
    typer.secho("  RESTAURANT POS CONFIGURATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # ---------------------------------------------------------------
    # 1. Verify pos_restaurant is installed
    # ---------------------------------------------------------------
    typer.secho("\n1. Checking pos_restaurant module...", bold=True)
    mod = client.search_read('ir.module.module',
        domain=[['name', '=', 'pos_restaurant']],
        fields=['state'])
    if not mod or mod[0]['state'] != 'installed':
        typer.secho("  [FAIL] pos_restaurant is not installed.", fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.secho("  [OK] pos_restaurant is installed", fg=typer.colors.GREEN)

    # ---------------------------------------------------------------
    # 2. Create/verify POS categories
    # ---------------------------------------------------------------
    typer.secho("\n2. POS Categories", bold=True)

    for cat_def in POS_CATEGORIES:
        cat_name = t(cat_def['name'])
        existing = search_translatable(client, 'pos.category', 'name',
            cat_def['name'], fields=['id', 'name', 'sequence'])

        if existing:
            cat_id = existing[0]['id']
            typer.secho(f"  [OK] {cat_name} (id={cat_id}, seq={existing[0].get('sequence', '-')})",
                fg=typer.colors.GREEN)
        else:
            result = client.execute('pos.category', 'create', [{
                'name': cat_name,
                'sequence': cat_def.get('sequence', 10),
            }])
            cat_id = result[0] if isinstance(result, list) else result
            typer.secho(f"  [CREATED] {cat_name} (id={cat_id})", fg=typer.colors.GREEN)
            changes += 1

        write_translations(client, 'pos.category', cat_id, {
            'name': cat_def['name'],
        })

    # ---------------------------------------------------------------
    # 3. Create/verify preparation display
    # ---------------------------------------------------------------
    typer.secho("\n3. Preparation Display", bold=True)

    existing_display = client.search_read('pos.prep.display',
        domain=[['name', '=', PREP_DISPLAY_NAME]],
        fields=['id', 'name'])

    if existing_display:
        display_id = existing_display[0]['id']
        typer.secho(f"  [OK] '{PREP_DISPLAY_NAME}' already exists (id={display_id})",
            fg=typer.colors.GREEN)
    else:
        result = client.execute('pos.prep.display', 'create', [{
            'name': PREP_DISPLAY_NAME,
        }])
        display_id = result[0] if isinstance(result, list) else result
        typer.secho(f"  [CREATED] '{PREP_DISPLAY_NAME}' (id={display_id})", fg=typer.colors.GREEN)
        changes += 1

    # Verify/create stages
    typer.secho("\n  Preparation Stages:", bold=True)
    existing_stages = client.search_read('pos.prep.stage',
        domain=[['prep_display_id', '=', display_id]],
        fields=['name', 'color', 'alert_timer'])

    existing_stage_names = {s['name'] for s in existing_stages}

    for stage_def in PREP_STAGES:
        if stage_def['name'] in existing_stage_names:
            typer.secho(f"    [OK] {stage_def['name']}", fg=typer.colors.GREEN)
        else:
            result = client.execute('pos.prep.stage', 'create', [{
                'name': stage_def['name'],
                'color': stage_def['color'],
                'alert_timer': stage_def['alert_timer'],
                'prep_display_id': display_id,
            }])
            typer.secho(f"    [CREATED] {stage_def['name']}", fg=typer.colors.GREEN)
            changes += 1

    # ---------------------------------------------------------------
    # 4. POS Config summary
    # ---------------------------------------------------------------
    typer.secho("\n4. POS Config Summary", bold=True)

    configs = client.search_read('pos.config', domain=[],
        fields=['name', 'module_pos_restaurant', 'module_pos_hr',
                'iface_splitbill', 'iface_printbill', 'cash_control',
                'self_ordering_mode'])

    for cfg in configs:
        is_rest = cfg.get('module_pos_restaurant', False)
        label = "RESTAURANT" if is_rest else "POS"
        typer.secho(f"  [{label}] {cfg['name']} (id={cfg['id']})", fg=typer.colors.CYAN)
        if is_rest:
            typer.secho(f"    split_bill={cfg.get('iface_splitbill')}, "
                f"print_bill={cfg.get('iface_printbill')}, "
                f"cash_control={cfg.get('cash_control')}, "
                f"self_order={cfg.get('self_ordering_mode', 'off')}",
                fg=typer.colors.CYAN)

    # ---------------------------------------------------------------
    # 5. Floors & Tables summary
    # ---------------------------------------------------------------
    typer.secho("\n5. Floors & Tables", bold=True)

    floors = client.search_read('restaurant.floor', domain=[],
        fields=['name', 'table_ids', 'pos_config_ids'])

    for floor in floors:
        table_count = len(floor.get('table_ids', []))
        configs_linked = floor.get('pos_config_ids', [])
        typer.secho(f"  {floor['name']}: {table_count} tables, linked to {len(configs_linked)} POS config(s)",
            fg=typer.colors.CYAN)

        if floor.get('table_ids'):
            tables = client.search_read('restaurant.table',
                domain=[['floor_id', '=', floor['id']]],
                fields=['table_number', 'seats'],
                order='table_number')
            total_seats = sum(tb.get('seats', 0) for tb in tables)
            table_nums = [str(tb['table_number']) for tb in tables]
            typer.secho(f"    Tables: {', '.join(table_nums)} ({total_seats} seats total)",
                fg=typer.colors.CYAN)

    typer.secho(f"\nDone. {changes} changes made.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
