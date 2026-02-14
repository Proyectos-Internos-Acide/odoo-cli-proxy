#!/usr/bin/env python3
"""Patch the 'Fix Slot Times' automation to prevent crashes.

Fixes two bugs in the booking_engine.industry_fix_slot_times automation:
1. Timezone naive datetime conversion (double UTC offset)
2. AttributeError when start_datetime/end_datetime is False

This patch MUST be applied on every new instance that uses the hotel/booking
engine modules with sale_planning. Without it, confirming any sale order that
creates planning slots without dates will crash.

Usage:
    uv run python business_units/hotel-trip-agency/hotel/fix_slot_times_automation.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

import typer
from odoo_cli import OdooClient

app = typer.Typer(help="Patch Fix Slot Times automation")

# The corrected code for server action "Fix Slot Times"
# Key fixes:
#   - Guard for False datetimes (products without rental dates)
#   - Proper timezone conversion using dateutil.tz
#   - Atomic write of both fields to avoid constraint violations
#   - Sensible defaults (12:00 check-in, 11:00 check-out)
FIXED_CODE = """
tz = env.ref('website.default_website').tz
tz_info = dateutil.tz.gettz(tz)
for record in records:
    if not record.sale_line_id: continue
    if not record.role_id.x_is_a_room_offer: continue
    if not record.start_datetime or not record.end_datetime: continue
    pickup_time = record.sale_line_id.product_id.pickup_time or 12.0
    return_time = record.sale_line_id.product_id.return_time or 11.0
    # Convert to local timezone to get the correct local date
    start_local = record.start_datetime.astimezone(tz=dateutil.tz.UTC).astimezone(tz=tz_info)
    end_local = record.end_datetime.astimezone(tz=dateutil.tz.UTC).astimezone(tz=tz_info)
    expected_start_time = f"{int(pickup_time):02d}:{int(pickup_time % 1 * 60):02d}:00"
    if record.start_datetime and start_local.strftime('%H:%M:%S') != expected_start_time:
        start_local = start_local.replace(hour=int(pickup_time), minute=int(pickup_time % 1 * 60), second=0)
    expected_end_time = f"{int(return_time):02d}:{int(return_time % 1 * 60):02d}:00"
    if record.end_datetime and end_local.strftime('%H:%M:%S') != expected_end_time:
        end_local = end_local.replace(hour=int(return_time), minute=int(return_time % 1 * 60), second=0)
    if start_local >= end_local:
        end_local = end_local + datetime.timedelta(days=1)
    # Convert back to UTC for storage
    start_utc = start_local.astimezone(dateutil.tz.UTC)
    end_utc = end_local.astimezone(dateutil.tz.UTC)
    # Write both fields at once to avoid constraint violation
    record.write({
        'start_datetime': start_utc.replace(tzinfo=None),
        'end_datetime': end_utc.replace(tzinfo=None),
    })
for record in records:
    if not record.sale_line_id: continue
    if not record.start_datetime or not record.end_datetime: continue
    nights = 0
    if record.sale_line_id.planning_slot_ids:
        nights = sum(record.sale_line_id.planning_slot_ids.mapped('x_nights'))
    record.sale_line_id.update({
        'start_date': record.start_datetime,
        'return_date': record.end_datetime,
        'x_nights': nights,
    })
    record.sale_line_id._reset_price_unit()
"""


@app.command()
def patch():
    """Apply the Fix Slot Times patch to the current Odoo instance."""
    client = OdooClient()
    client.connect()

    typer.secho("=" * 60, bold=True)
    typer.secho("  PATCH: Fix Slot Times Automation", bold=True)
    typer.secho("=" * 60, bold=True)

    # Find the automation
    typer.secho("\n1. Finding automation...", bold=True)
    automation = client.search_read('base.automation',
        domain=[['name', '=', 'Fix Slot Times']],
        fields=['id', 'name', 'action_server_ids'])

    if not automation:
        typer.secho("  [SKIP] 'Fix Slot Times' automation not found.", fg=typer.colors.YELLOW)
        typer.secho("  This instance may not have the booking engine module.", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    server_action_id = automation[0]['action_server_ids'][0]
    typer.secho(f"  [OK] Found automation (id={automation[0]['id']}), "
                f"server action (id={server_action_id})", fg=typer.colors.GREEN)

    # Read current code
    typer.secho("\n2. Checking current code...", bold=True)
    sa = client.search_read('ir.actions.server',
        domain=[['id', '=', server_action_id]],
        fields=['code'])
    current_code = sa[0]['code'] if sa else ''

    guard = 'if not record.start_datetime or not record.end_datetime: continue'
    if guard in current_code:
        typer.secho("  [OK] Patch already applied (guard clause present)", fg=typer.colors.GREEN)
        raise typer.Exit(0)

    # Apply patch
    typer.secho("\n3. Applying patch...", bold=True)
    client.execute('ir.actions.server', 'write', [server_action_id],
                   {'code': FIXED_CODE})

    # Verify
    typer.secho("\n4. Verifying...", bold=True)
    sa_check = client.search_read('ir.actions.server',
        domain=[['id', '=', server_action_id]],
        fields=['code'])
    if guard in sa_check[0].get('code', ''):
        typer.secho("  [OK] Patch verified successfully", fg=typer.colors.GREEN)
    else:
        typer.secho("  [ERROR] Patch verification failed", fg=typer.colors.RED)
        raise typer.Exit(1)

    typer.secho("\nDone. The automation will no longer crash when confirming "
                "sale orders with non-rental service products.", fg=typer.colors.BLUE, bold=True)


if __name__ == "__main__":
    app()
