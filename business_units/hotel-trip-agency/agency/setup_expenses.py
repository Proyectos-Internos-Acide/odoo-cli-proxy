#!/usr/bin/env python3
"""Configure expense products for re-invoicing to clients.

Usage:
    uv run python business_units/hotel-trip-agency/agency/setup_expenses.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import typer
from odoo_cli import OdooClient

app = typer.Typer(help="Configure expense re-invoicing for travel agency")


@app.command()
def setup():
    """Set expense_policy on expense products for re-invoicing."""
    client = OdooClient()
    client.connect()
    changes = 0

    typer.secho("=" * 60, bold=True)
    typer.secho("  EXPENSE RE-INVOICING CONFIGURATION", bold=True)
    typer.secho("=" * 60, bold=True)

    # ---------------------------------------------------------------
    # 1. Check expense-eligible products
    # ---------------------------------------------------------------
    typer.secho("\n1. Expense-eligible products", bold=True)

    expenses = client.search_read('product.product',
        domain=[['can_be_expensed', '=', True]],
        fields=['name', 'expense_policy', 'list_price', 'standard_price'])

    for ex in expenses:
        policy = ex.get('expense_policy', 'no')
        typer.secho(
            f"  [{ex['id']:>3}] {ex['name']:<30} | expense_policy={policy} | "
            f"sale_price={ex.get('list_price')} | cost={ex.get('standard_price')}",
            fg=typer.colors.CYAN)

    # ---------------------------------------------------------------
    # 2. Set expense_policy to 'sales_price' for re-invoicing
    # ---------------------------------------------------------------
    typer.secho("\n2. Setting expense_policy='sales_price' on expense products", bold=True)

    to_fix = [ex for ex in expenses if ex.get('expense_policy') != 'sales_price']
    if to_fix:
        for ex in to_fix:
            try:
                client.execute('product.product', 'write', [ex['id']],
                    {'expense_policy': 'sales_price'})
                typer.secho(
                    f"  [FIXED] {ex['name']}: {ex.get('expense_policy', 'no')} -> sales_price",
                    fg=typer.colors.GREEN)
                changes += 1
            except Exception as e:
                typer.secho(f"  [ERROR] {ex['name']}: {str(e)[:80]}", fg=typer.colors.RED)
    else:
        typer.secho("  [OK] All expense products already set to sales_price",
            fg=typer.colors.GREEN)

    # ---------------------------------------------------------------
    # 3. Verify re-invoice setting
    # ---------------------------------------------------------------
    typer.secho("\n3. Verification", bold=True)

    verified = client.search_read('product.product',
        domain=[['can_be_expensed', '=', True]],
        fields=['name', 'expense_policy'])

    all_ok = True
    for v in verified:
        ok = v.get('expense_policy') == 'sales_price'
        status = 'OK' if ok else 'FAIL'
        color = typer.colors.GREEN if ok else typer.colors.RED
        typer.secho(f"  [{status}] {v['name']}: expense_policy={v.get('expense_policy')}", fg=color)
        if not ok:
            all_ok = False

    if all_ok:
        typer.secho("\n  All expense products can be re-invoiced to clients.",
            fg=typer.colors.GREEN, bold=True)
    else:
        typer.secho("\n  Some products could not be configured.",
            fg=typer.colors.YELLOW, bold=True)

    typer.secho(f"\nDone. {changes} changes made.", fg=typer.colors.BLUE, bold=True)
    typer.secho("\nNote: To re-invoice a specific expense, the employee must:", fg=typer.colors.CYAN)
    typer.secho("  1. Create the expense and link it to the project's analytic account", fg=typer.colors.CYAN)
    typer.secho("  2. Mark it as 'To Re-Invoice' when submitting", fg=typer.colors.CYAN)
    typer.secho("  3. The expense will be added to the client's Sale Order", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
