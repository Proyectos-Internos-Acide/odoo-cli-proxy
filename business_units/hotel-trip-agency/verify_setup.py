#!/usr/bin/env python3
"""Verify complete travel agency setup on Odoo instance.

Usage:
    uv run python business_units/hotel-trip-agency/verify_setup.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(__file__))

import typer
from odoo_cli import OdooClient
from defaults.categories import CATEGORIES
from defaults.modules import REQUIRED_MODULES
from hotel.defaults.attributes import HOTEL_ATTR_IDS, HOTEL_ATTR_MODE
from agency.defaults.products import DEFAULT_TIMEZONE

app = typer.Typer(help="Verify travel agency setup")


@app.command()
def verify():
    """Run full verification of travel agency configuration."""
    client = OdooClient()
    client.connect()
    errors = []
    warnings = []

    typer.secho("=" * 60, bold=True)
    typer.secho("  TRAVEL AGENCY SETUP VERIFICATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # ---------------------------------------------------------------
    # 1. Required modules
    # ---------------------------------------------------------------
    typer.secho("\n1. Required modules", bold=True)
    modules = client.search_read('ir.module.module',
        domain=[['name', 'in', list(REQUIRED_MODULES.keys())]],
        fields=['name', 'state'])
    mod_states = {m['name']: m['state'] for m in modules}

    for name, desc in REQUIRED_MODULES.items():
        state = mod_states.get(name, 'not found')
        ok = state == 'installed'
        status = 'PASS' if ok else 'FAIL'
        color = typer.colors.GREEN if ok else typer.colors.RED
        typer.secho(f"  [{status}] {name} ({desc}): {state}", fg=color)
        if not ok:
            errors.append(f"Module {name} not installed")

    # ---------------------------------------------------------------
    # 2. Product attributes
    # ---------------------------------------------------------------
    typer.secho(f"\n2. Hotel attributes (should be {HOTEL_ATTR_MODE})", bold=True)
    attrs = client.search_read('product.attribute',
        domain=[['id', 'in', HOTEL_ATTR_IDS]],
        fields=['name', 'create_variant'])
    for a in attrs:
        ok = a['create_variant'] == HOTEL_ATTR_MODE
        status = 'PASS' if ok else 'WARN'
        color = typer.colors.GREEN if ok else typer.colors.YELLOW
        typer.secho(f"  [{status}] {a['name']}: {a['create_variant']}", fg=color)
        if not ok:
            warnings.append(f"Attr {a['name']} has create_variant={a['create_variant']} (used on products)")

    # ---------------------------------------------------------------
    # 3. Tour products
    # ---------------------------------------------------------------
    typer.secho("\n3. Tour products (service_tracking)", bold=True)
    tours = client.search_read('product.template',
        domain=[['categ_id', '=', CATEGORIES['tours_packages']]],
        fields=['name', 'type', 'service_tracking', 'invoice_policy', 'project_template_id'])
    for t in tours:
        tracking = t.get('service_tracking', 'no')
        has_template = bool(t.get('project_template_id'))
        ok = tracking in ('task_in_project', 'project_only')
        status = 'PASS' if ok else 'FAIL'
        color = typer.colors.GREEN if ok else typer.colors.RED
        tmpl_name = t['project_template_id'][1] if t.get('project_template_id') else 'NONE'
        typer.secho(f"  [{status}] {t['name']}: tracking={tracking}, template={tmpl_name}", fg=color)
        if not ok:
            errors.append(f"Tour {t['name']} has tracking={tracking}")

    # ---------------------------------------------------------------
    # 4. Project template
    # ---------------------------------------------------------------
    typer.secho("\n4. Project template", bold=True)
    templates = client.search_read('project.project',
        domain=[['is_template', '=', True]],
        fields=['name', 'task_count'])
    if templates:
        for t in templates:
            ok = t.get('task_count', 0) > 0
            status = 'PASS' if ok else 'WARN'
            color = typer.colors.GREEN if ok else typer.colors.YELLOW
            typer.secho(f"  [{status}] {t['name']}: {t['task_count']} tasks", fg=color)
    else:
        typer.secho("  [FAIL] No project templates found", fg=typer.colors.RED)
        errors.append("No project templates found")

    # ---------------------------------------------------------------
    # 5. Quotation templates
    # ---------------------------------------------------------------
    typer.secho("\n5. Quotation templates", bold=True)
    qtemplates = client.search_read('sale.order.template',
        domain=[], fields=['name', 'sale_order_template_line_ids'])
    if qtemplates:
        for qt in qtemplates:
            lines = len(qt.get('sale_order_template_line_ids', []))
            typer.secho(f"  [PASS] {qt['name']}: {lines} lines", fg=typer.colors.GREEN)
    else:
        typer.secho("  [WARN] No quotation templates found", fg=typer.colors.YELLOW)
        warnings.append("No quotation templates")

    # ---------------------------------------------------------------
    # 6. Kit/BoM
    # ---------------------------------------------------------------
    typer.secho("\n6. Kit/BoM", bold=True)
    boms = client.search_read('mrp.bom', domain=[],
        fields=['product_tmpl_id', 'type', 'bom_line_ids'])
    if boms:
        for b in boms:
            prod = b.get('product_tmpl_id', [None, ''])[1] if b.get('product_tmpl_id') else '-'
            btype = 'Kit' if b.get('type') == 'phantom' else b.get('type', '-')
            lines = len(b.get('bom_line_ids', []))
            typer.secho(f"  [PASS] {prod}: type={btype}, {lines} components", fg=typer.colors.GREEN)
    else:
        typer.secho("  [WARN] No BoM found", fg=typer.colors.YELLOW)
        warnings.append("No BoM/Kit created")

    # ---------------------------------------------------------------
    # 7. Expense products
    # ---------------------------------------------------------------
    typer.secho("\n7. Expense re-invoicing", bold=True)
    expenses = client.search_read('product.product',
        domain=[['can_be_expensed', '=', True]],
        fields=['name', 'expense_policy'])
    reinvoice_count = 0
    for ex in expenses:
        ok = ex.get('expense_policy') == 'sales_price'
        status = 'PASS' if ok else 'WARN'
        color = typer.colors.GREEN if ok else typer.colors.YELLOW
        typer.secho(f"  [{status}] {ex['name']}: expense_policy={ex.get('expense_policy')}", fg=color)
        if ok:
            reinvoice_count += 1
    typer.secho(f"  {reinvoice_count}/{len(expenses)} products configured for re-invoicing",
        fg=typer.colors.CYAN)

    # ---------------------------------------------------------------
    # 8. Timezone (from previous setup)
    # ---------------------------------------------------------------
    typer.secho("\n8. Timezone", bold=True)
    websites = client.search_read('website', domain=[], fields=['tz'])
    for w in websites:
        tz = w.get('tz', 'NOT SET')
        ok = tz == DEFAULT_TIMEZONE
        status = 'PASS' if ok else 'WARN'
        color = typer.colors.GREEN if ok else typer.colors.YELLOW
        typer.secho(f"  [{status}] Website tz: {tz}", fg=color)

    # ---------------------------------------------------------------
    # 9. CRM Pipeline
    # ---------------------------------------------------------------
    typer.secho("\n9. CRM Pipeline", bold=True)
    stages = client.search_read('crm.stage', domain=[], fields=['name'])
    typer.secho(f"  [PASS] {len(stages)} stages configured", fg=typer.colors.GREEN)

    # ---------------------------------------------------------------
    # 10. Fleet
    # ---------------------------------------------------------------
    typer.secho("\n10. Fleet", bold=True)
    vehicles = client.search_read('fleet.vehicle', domain=[], fields=['name'])
    typer.secho(f"  [INFO] {len(vehicles)} vehicle(s) registered", fg=typer.colors.CYAN)

    # ---------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------
    typer.secho("\n" + "=" * 60, bold=True)
    if errors:
        typer.secho(f"  RESULT: {len(errors)} ERRORS, {len(warnings)} WARNINGS", fg=typer.colors.RED, bold=True)
        for e in errors:
            typer.secho(f"    ERROR: {e}", fg=typer.colors.RED)
        for w in warnings:
            typer.secho(f"    WARN: {w}", fg=typer.colors.YELLOW)
    elif warnings:
        typer.secho(f"  RESULT: PASS with {len(warnings)} WARNINGS", fg=typer.colors.YELLOW, bold=True)
        for w in warnings:
            typer.secho(f"    WARN: {w}", fg=typer.colors.YELLOW)
    else:
        typer.secho("  RESULT: ALL CHECKS PASSED", fg=typer.colors.GREEN, bold=True)
    typer.secho("=" * 60, bold=True)


if __name__ == "__main__":
    app()
