#!/usr/bin/env python3
"""Run a setup script against the TARGET_MIGRATION instance.

Reads TARGET_MIGRATION_* from .env, overrides ODOO_* env vars,
then executes the specified script as a subprocess.

Usage:
    uv run python business_units/hotel-trip-agency/migrate_to_target.py <script_path>
    uv run python business_units/hotel-trip-agency/migrate_to_target.py hotel/fix_slot_times_automation.py
    uv run python business_units/hotel-trip-agency/migrate_to_target.py agency/setup_custom_fields.py
"""

import os
import sys
import subprocess

from dotenv import load_dotenv

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("Usage: migrate_to_target.py <script_path> [args...]")
        print("  script_path: relative to business_units/hotel-trip-agency/")
        sys.exit(1)

    # Read target credentials
    url = os.getenv('TARGET_MIGRATION_URL', '').strip()
    db = os.getenv('TARGET_MIGRATION_DB', '').strip()
    username = os.getenv('TARGET_MIGRATION_USERNAME', '').strip()
    password = os.getenv('TARGET_MIGRATION_PASSWORD', '').strip()

    if not all([url, db, username, password]):
        print("ERROR: TARGET_MIGRATION_* variables not configured in .env")
        sys.exit(1)

    # Build script path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script_rel = sys.argv[1]
    script_path = os.path.join(base_dir, script_rel)

    if not os.path.exists(script_path):
        print(f"ERROR: Script not found: {script_path}")
        sys.exit(1)

    # Override ODOO_* with TARGET_MIGRATION_* values
    env = os.environ.copy()
    env['ODOO_URL'] = url
    env['ODOO_DB'] = db
    env['ODOO_USER'] = username
    env['ODOO_PASSWORD'] = password

    print(f"{'=' * 64}")
    print(f"  MIGRATION MODE - Running against TARGET")
    print(f"  Target: {db}")
    print(f"  Script: {script_rel}")
    print(f"{'=' * 64}")
    print()

    # Run the script
    cmd = [sys.executable, script_path] + sys.argv[2:]
    result = subprocess.run(cmd, env=env, cwd=os.path.join(base_dir, '..', '..'))
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
