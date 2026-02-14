#!/usr/bin/env python3
"""Check fleet vehicle availability for a date range.

Shows which vehicles are free and which are busy, with seat occupancy details.

Usage:
    uv run python business_units/hotel-trip-agency/agency/check_fleet_availability.py
    uv run python business_units/hotel-trip-agency/agency/check_fleet_availability.py --start 2026-03-10 --end 2026-03-15
    uv run python business_units/hotel-trip-agency/agency/check_fleet_availability.py --vehicle-id 1
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import typer
from datetime import date, timedelta
from odoo_cli import OdooClient

app = typer.Typer(help="Fleet availability checker for tour operations")


@app.command()
def check(
    start: str = typer.Option(None, help="Start date (YYYY-MM-DD). Default: today"),
    end: str = typer.Option(None, help="End date (YYYY-MM-DD). Default: start + 30 days"),
    vehicle_id: int = typer.Option(None, help="Filter by specific vehicle ID"),
):
    """Check vehicle availability for a date range."""
    client = OdooClient()
    client.connect()

    # Parse dates
    start_date = date.fromisoformat(start) if start else date.today()
    end_date = date.fromisoformat(end) if end else start_date + timedelta(days=30)

    typer.secho("=" * 70, bold=True)
    typer.secho(f"  FLEET AVAILABILITY: {start_date} to {end_date}", bold=True)
    typer.secho("=" * 70, bold=True)

    # ---------------------------------------------------------------
    # 1. Get all vehicles (or specific one)
    # ---------------------------------------------------------------
    domain = [['id', '=', vehicle_id]] if vehicle_id else []
    vehicles = client.search_read('fleet.vehicle', domain=domain,
        fields=['id', 'name', 'license_plate', 'seats', 'driver_id'])

    if not vehicles:
        typer.secho("No vehicles found.", fg=typer.colors.RED)
        raise typer.Exit(1)

    # ---------------------------------------------------------------
    # 2. Get all tasks with vehicle assigned in the date range
    # ---------------------------------------------------------------
    task_domain = [
        ('x_is_fleet_task', '=', True),
        ('x_vehicle_id', '!=', False),
        ('x_tour_start_date', '!=', False),
        ('x_tour_end_date', '!=', False),
        ('x_tour_start_date', '<=', str(end_date)),
        ('x_tour_end_date', '>=', str(start_date)),
    ]
    if vehicle_id:
        task_domain.append(('x_vehicle_id', '=', vehicle_id))

    tasks = client.search_read('project.task', domain=task_domain,
        fields=['id', 'name', 'x_vehicle_id', 'x_driver_id',
                'x_tour_start_date', 'x_tour_end_date', 'x_seats_needed',
                'sale_order_id', 'project_id'])

    # Group tasks by vehicle
    tasks_by_vehicle = {}
    for t in tasks:
        vid = t['x_vehicle_id'][0] if t.get('x_vehicle_id') else None
        if vid:
            tasks_by_vehicle.setdefault(vid, []).append(t)

    # ---------------------------------------------------------------
    # 3. Show results per vehicle
    # ---------------------------------------------------------------
    for v in vehicles:
        vid = v['id']
        capacity = v.get('seats', 0) or 0
        plate = v.get('license_plate', '?')
        driver = v.get('driver_id', [None, '-'])[1] if v.get('driver_id') else '-'

        typer.secho(f"\n{'─' * 70}", fg=typer.colors.BRIGHT_BLACK)
        typer.secho(f"  {v['name']} | Placa: {plate} | Capacidad: {capacity} asientos | Chofer: {driver}",
            bold=True)

        vehicle_tasks = tasks_by_vehicle.get(vid, [])

        if not vehicle_tasks:
            typer.secho(f"  DISPONIBLE todo el periodo", fg=typer.colors.GREEN)
            continue

        # Show each booking
        for t in sorted(vehicle_tasks, key=lambda x: x['x_tour_start_date']):
            so_name = t['sale_order_id'][1] if t.get('sale_order_id') else 'Sin SO'
            project = t['project_id'][1] if t.get('project_id') else '-'
            seats = t.get('x_seats_needed', 0) or 0
            typer.secho(
                f"  OCUPADO {t['x_tour_start_date']} -> {t['x_tour_end_date']} | "
                f"{so_name} | {seats} asientos | {project}",
                fg=typer.colors.RED)

        # Check daily occupancy for overlapping dates
        typer.secho(f"\n  Ocupacion diaria:", fg=typer.colors.CYAN)
        current = start_date
        while current <= end_date:
            day_tasks = [t for t in vehicle_tasks
                         if t['x_tour_start_date'] <= str(current) <= t['x_tour_end_date']]
            if day_tasks:
                day_seats = sum(t.get('x_seats_needed', 0) or 0 for t in day_tasks)
                status = "LLENO" if capacity > 0 and day_seats >= capacity else f"{day_seats}/{capacity}"
                color = typer.colors.RED if capacity > 0 and day_seats >= capacity else typer.colors.YELLOW
                tours = ", ".join(
                    t['sale_order_id'][1] if t.get('sale_order_id') else '?' for t in day_tasks)
                typer.secho(f"    {current}: {status} asientos ({tours})", fg=color)
            current += timedelta(days=1)

    # ---------------------------------------------------------------
    # 4. Summary
    # ---------------------------------------------------------------
    typer.secho(f"\n{'=' * 70}", bold=True)
    total_vehicles = len(vehicles)
    busy_vehicles = len(tasks_by_vehicle)
    free_vehicles = total_vehicles - busy_vehicles
    typer.secho(f"  Resumen: {total_vehicles} vehiculos | {free_vehicles} libres | {busy_vehicles} con reservas",
        fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
