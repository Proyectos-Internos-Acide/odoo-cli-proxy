#!/usr/bin/env python3
"""Configure timezone for all Odoo components of a hotel instance.

Usage:
    uv run python hotel-trip-agency/setup_timezone.py [TIMEZONE]

Examples:
    uv run python hotel-trip-agency/setup_timezone.py America/Lima
    uv run python hotel-trip-agency/setup_timezone.py America/Bogota
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import typer
from odoo_cli import OdooClient

app = typer.Typer(help="Configure timezone for all hotel components in Odoo")


@app.command()
def setup(
    timezone: str = typer.Argument("America/Lima", help="Timezone to set (e.g. America/Lima)")
):
    """Set timezone on users, calendars, and resources."""
    client = OdooClient()
    uid = client.connect()
    total = 0

    # 1. Current user
    client.execute('res.users', 'write', [uid], {'tz': timezone})
    typer.secho(f"  User (current): tz={timezone}", fg=typer.colors.GREEN)
    total += 1

    # 2. All users without timezone or with UTC
    users = client.search_read('res.users',
        domain=['|', ['tz', '=', False], ['tz', '=', 'UTC']],
        fields=['id', 'name'])
    if users:
        ids = [u['id'] for u in users]
        client.execute('res.users', 'write', ids, {'tz': timezone})
        for u in users:
            typer.secho(f"  User \"{u['name']}\": tz={timezone}", fg=typer.colors.GREEN)
        total += len(users)

    # 3. Resource calendars
    cals = client.search_read('resource.calendar',
        domain=[['tz', '!=', timezone]],
        fields=['id', 'name'])
    if cals:
        ids = [c['id'] for c in cals]
        client.execute('resource.calendar', 'write', ids, {'tz': timezone})
        for c in cals:
            typer.secho(f"  Calendar \"{c['name']}\": tz={timezone}", fg=typer.colors.GREEN)
        total += len(cals)

    # 4. Resources (rooms, tables, equipment)
    resources = client.search_read('resource.resource',
        domain=[['tz', '!=', timezone]],
        fields=['id', 'name'])
    if resources:
        ids = [r['id'] for r in resources]
        client.execute('resource.resource', 'write', ids, {'tz': timezone})
        for r in resources:
            typer.secho(f"  Resource \"{r['name']}\": tz={timezone}", fg=typer.colors.GREEN)
        total += len(resources)

    typer.secho(f"\nDone. {total} records updated to {timezone}.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
