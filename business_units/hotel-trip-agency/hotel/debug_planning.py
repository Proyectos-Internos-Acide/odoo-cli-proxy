#!/usr/bin/env python3
"""Debug commands for hotel planning timezone issues."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import typer
from typing import Optional
from odoo_cli import OdooClient

app = typer.Typer(help="Debug tools for Hotel/Planning timezone issues")


def get_client():
    try:
        return OdooClient()
    except Exception as e:
        typer.secho(f"Error initializing client: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def timezone():
    """Debug timezone configuration in Odoo (user, company, resource calendars)"""
    client = get_client()
    try:
        uid = client.connect()

        # User timezone
        users = client.search_read(
            'res.users', domain=[['id', '=', uid]],
            fields=['name', 'login', 'tz']
        )
        typer.secho("=== User Timezone ===", fg=typer.colors.BLUE, bold=True)
        for u in users:
            typer.echo(f"  User: {u.get('name')} ({u.get('login')})")
            typer.echo(f"  Timezone: {u.get('tz') or 'NOT SET'}")

        # Company timezone
        companies = client.search_read(
            'res.company', domain=[],
            fields=['name', 'resource_calendar_id']
        )
        typer.secho("\n=== Companies ===", fg=typer.colors.BLUE, bold=True)
        for c in companies:
            typer.echo(f"  Company: {c.get('name')}")
            cal = c.get('resource_calendar_id')
            typer.echo(f"  Resource Calendar: {cal[1] if cal else 'NOT SET'}")

        # Resource calendars with timezone
        calendars = client.search_read(
            'resource.calendar', domain=[],
            fields=['name', 'tz']
        )
        typer.secho("\n=== Resource Calendars ===", fg=typer.colors.BLUE, bold=True)
        for cal in calendars:
            typer.echo(f"  {cal.get('name')}: tz={cal.get('tz') or 'NOT SET'}")

    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def planning(
    limit: int = typer.Option(10, help="Number of slots to show"),
    sale: Optional[str] = typer.Option(None, help="Filter by sale order name (e.g. S00017)")
):
    """Inspect planning.slot records - shows raw UTC dates from DB"""
    client = get_client()
    try:
        domain = []
        if sale:
            domain = [['sale_line_id.order_id.name', '=', sale]]

        slots = client.search_read(
            'planning.slot', domain=domain,
            fields=[
                'display_name', 'resource_id', 'role_id',
                'start_datetime', 'end_datetime', 'allocated_hours',
                'sale_line_id'
            ],
            limit=limit, order='start_datetime desc'
        )

        typer.secho(f"\n=== Planning Slots (raw UTC from DB) ===", fg=typer.colors.BLUE, bold=True)
        typer.echo("-" * 100)
        typer.echo(f"{'ID':<6} {'Resource':<25} {'Start (UTC)':<22} {'End (UTC)':<22} {'Hours':<8} {'Sale Line'}")
        typer.echo("-" * 100)
        for s in slots:
            res = s.get('resource_id')
            res_name = res[1] if res else '-'
            sale_line = s.get('sale_line_id')
            sale_name = sale_line[1] if sale_line else '-'
            typer.echo(
                f"{s['id']:<6} {res_name:<25} "
                f"{s.get('start_datetime', '-'):<22} "
                f"{s.get('end_datetime', '-'):<22} "
                f"{str(s.get('allocated_hours', '-')):<8} "
                f"{sale_name}"
            )
        typer.echo("-" * 100)
        typer.echo(f"Total: {len(slots)} slots")

    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def sale_vs_planning(
    sale_name: str = typer.Argument(..., help="Sale order name (e.g. S00017)")
):
    """Compare sale order dates vs planning slot dates for a specific order"""
    client = get_client()
    try:
        # Get sale order
        orders = client.search_read(
            'sale.order', domain=[['name', '=', sale_name]],
            fields=['name', 'date_order', 'rental_start_date', 'rental_return_date', 'order_line']
        )
        if not orders:
            typer.secho(f"Sale order '{sale_name}' not found", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        order = orders[0]
        typer.secho(f"\n=== Sale Order: {order['name']} ===", fg=typer.colors.BLUE, bold=True)
        typer.echo(f"  Date Order:        {order.get('date_order')}")
        typer.echo(f"  Rental Start:      {order.get('rental_start_date')}")
        typer.echo(f"  Rental Return:     {order.get('rental_return_date')}")

        # Get sale order lines
        line_ids = order.get('order_line', [])
        if line_ids:
            lines = client.search_read(
                'sale.order.line', domain=[['id', 'in', line_ids]],
                fields=['name', 'reservation_begin', 'start_date', 'return_date', 'product_id']
            )
            typer.secho(f"\n=== Sale Order Lines ===", fg=typer.colors.BLUE, bold=True)
            for line in lines:
                product = line.get('product_id')
                typer.echo(f"  Line ID: {line['id']}")
                typer.echo(f"    Product:           {product[1] if product else '-'}")
                typer.echo(f"    reservation_begin: {line.get('reservation_begin')}")
                typer.echo(f"    start_date:        {line.get('start_date')}")
                typer.echo(f"    return_date:       {line.get('return_date')}")

        # Get planning slots linked to this sale
        slots = client.search_read(
            'planning.slot', domain=[['sale_line_id.order_id.name', '=', sale_name]],
            fields=[
                'resource_id', 'start_datetime', 'end_datetime',
                'allocated_hours', 'sale_line_id'
            ],
            order='start_datetime'
        )
        typer.secho(f"\n=== Planning Slots (UTC) ===", fg=typer.colors.BLUE, bold=True)
        for s in slots:
            res = s.get('resource_id')
            typer.echo(f"  Slot ID: {s['id']}")
            typer.echo(f"    Resource:        {res[1] if res else '-'}")
            typer.echo(f"    start_datetime:  {s.get('start_datetime')}")
            typer.echo(f"    end_datetime:    {s.get('end_datetime')}")
            typer.echo(f"    allocated_hours: {s.get('allocated_hours')}")

        typer.secho(f"\n=== Analisis ===", fg=typer.colors.YELLOW, bold=True)
        typer.echo("  Nota: Odoo guarda fechas en UTC en la BD.")
        typer.echo("  Si hay desfase, revisa que el timezone del usuario/empresa sea correcto.")
        typer.echo("  Usa 'timezone' para verificar la configuracion de timezone.")

    except Exception as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
