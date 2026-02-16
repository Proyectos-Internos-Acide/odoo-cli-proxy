#!/usr/bin/env python3
"""Standalone Odoo query for previewing report data.

Usage:
    uv run python project_management/scripts/query_odoo.py --start-date 2026-01-26 --end-date 2026-02-01
    uv run python project_management/scripts/query_odoo.py --start-date 2026-01-02 --end-date 2026-02-22
    uv run python project_management/scripts/query_odoo.py --start-date 2026-01-02 --end-date 2026-02-22 --system
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import typer

from helpers.odoo_query import (
    connect,
    query_date_range,
    query_system_overview,
    build_summary_table,
    MODEL_LABELS,
)

app = typer.Typer(help="Query Odoo for configuration data")


@app.command()
def query(
    start_date: str = typer.Option(..., help="Start date YYYY-MM-DD"),
    end_date: str = typer.Option(..., help="End date YYYY-MM-DD"),
    limit: int = typer.Option(5, help="Max records to show per model"),
    system: bool = typer.Option(
        False, help="Also show system overview (modules, POS, websites)"
    ),
):
    """Query Odoo and print summary of records created in the date range."""
    typer.secho("=" * 60, bold=True)
    typer.secho(f"  ODOO QUERY: {start_date} to {end_date}", bold=True)
    typer.secho("=" * 60, bold=True)

    typer.secho("\n  Connecting to Odoo...", fg=typer.colors.BLUE)
    client = connect()
    typer.secho("  [OK] Connected", fg=typer.colors.GREEN)

    # --- Date-range query ---
    typer.secho("  Querying models...", fg=typer.colors.BLUE)
    data = query_date_range(client, start_date, end_date)

    for model_key, records in data.items():
        label = MODEL_LABELS.get(model_key, model_key)
        typer.secho(f"\n  {label}: {len(records)} records", bold=True)
        for rec in records[:limit]:
            name = rec.get("name", rec.get("display_name", "N/A"))
            date = rec.get("create_date", "").split(" ")[0]
            typer.secho(f"    [{rec['id']}] {name}  ({date})")
        if len(records) > limit:
            typer.secho(f"    ... and {len(records) - limit} more")

    summary = build_summary_table(data)
    if summary:
        typer.secho("\n  Configuration Summary by Date:", bold=True)
        for row in summary:
            typer.secho(f"    {row['date']}  {row['items']} items  ({row['detail']})")

    total = sum(len(v) for v in data.values())
    typer.secho(
        f"\n  Total: {total} records across {len(data)} models",
        fg=typer.colors.BLUE,
        bold=True,
    )

    # --- System overview ---
    if system:
        typer.secho("\n" + "=" * 60, bold=True)
        typer.secho("  SYSTEM OVERVIEW", bold=True)
        typer.secho("=" * 60, bold=True)

        overview = query_system_overview(client)

        # Company
        for company in overview.get("company", []):
            typer.secho(f"\n  Company: {company['name']}", bold=True)
            currency = company.get("currency_id")
            if isinstance(currency, (list, tuple)):
                typer.secho(f"    Currency: {currency[1]}")
            country = company.get("country_id")
            if isinstance(country, (list, tuple)):
                typer.secho(f"    Country: {country[1]}")

        # Installed modules
        modules = overview.get("installed_modules", [])
        typer.secho(f"\n  Installed Modules: {len(modules)}", bold=True)
        for mod in modules[:limit]:
            typer.secho(f"    {mod['name']}: {mod.get('shortdesc', '')}")
        if len(modules) > limit:
            typer.secho(f"    ... and {len(modules) - limit} more")

        # POS configs
        pos = overview.get("pos_configs", [])
        if pos:
            typer.secho(f"\n  POS Configurations: {len(pos)}", bold=True)
            for cfg in pos:
                restaurant = cfg.get("module_pos_restaurant", False)
                kind = "Restaurant" if restaurant else "Standard"
                typer.secho(f"    {cfg['name']} ({kind})")

        # Websites
        websites = overview.get("websites", [])
        if websites:
            typer.secho(f"\n  Websites: {len(websites)}", bold=True)
            for site in websites:
                typer.secho(f"    {site['name']}: {site.get('domain', 'N/A')}")

        # Active currencies
        currencies = overview.get("active_currencies", [])
        if currencies:
            typer.secho(f"\n  Active Currencies: {len(currencies)}", bold=True)
            for cur in currencies:
                typer.secho(f"    {cur['name']} ({cur.get('symbol', '')})")

        # Warehouses
        wh = overview.get("warehouses", [])
        if wh:
            typer.secho(f"\n  Warehouses: {len(wh)}", bold=True)
            for w in wh:
                typer.secho(f"    [{w.get('code', '')}] {w['name']}")

        # Accounting journals
        jrnls = overview.get("journals", [])
        if jrnls:
            typer.secho(f"\n  Accounting Journals: {len(jrnls)}", bold=True)
            for j in jrnls:
                typer.secho(f"    [{j.get('code', '')}] {j['name']} ({j.get('type', '')})")

        # Config parameters
        params = overview.get("config_parameters", [])
        if params:
            typer.secho(f"\n  System Parameters: {len(params)}", bold=True)
            for p in params[:limit]:
                val = str(p.get("value", ""))
                if len(val) > 60:
                    val = val[:57] + "..."
                typer.secho(f"    {p['key']} = {val}")
            if len(params) > limit:
                typer.secho(f"    ... and {len(params) - limit} more")


if __name__ == "__main__":
    app()
