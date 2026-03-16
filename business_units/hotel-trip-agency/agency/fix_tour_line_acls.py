#!/usr/bin/env python3
"""Fix 403 error on tour product pages for public/portal users.

The x_tour_include_line, x_tour_exclude_line, and x_tour_recommendation_line
models only have ACLs for internal users (group_user). Public website visitors
get a 403 when viewing tour product pages because they can't read these records.

This script adds read-only ACLs for public and portal users.

Usage:
    uv run python business_units/hotel-trip-agency/agency/fix_tour_line_acls.py
    uv run python business_units/hotel-trip-agency/agency/fix_tour_line_acls.py --target
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from odoo_cli import OdooClient


LINE_MODELS = [
    'x_tour_include_line',
    'x_tour_exclude_line',
    'x_tour_recommendation_line',
]


def get_group_id(client, xml_id):
    """Get res.groups id from XML ID (e.g. 'base.group_public')."""
    module, name = xml_id.split('.')
    result = client.search_read('ir.model.data',
        domain=[['module', '=', module], ['name', '=', name], ['model', '=', 'res.groups']],
        fields=['res_id'], limit=1)
    return result[0]['res_id'] if result else None


def ensure_readonly_acl(client, acl_name, model_id, group_id):
    """Create a read-only ACL if it doesn't exist."""
    existing = client.search_read('ir.model.access',
        domain=[['name', '=', acl_name]], fields=['id'])
    if existing:
        print(f"  [EXISTS] {acl_name} (id={existing[0]['id']})")
        return existing[0]['id']

    result = client.execute('ir.model.access', 'create', [{
        'name': acl_name,
        'model_id': model_id,
        'group_id': group_id,
        'perm_read': True,
        'perm_write': False,
        'perm_create': False,
        'perm_unlink': False,
    }])
    aid = result[0] if isinstance(result, list) else result
    print(f"  [CREATED] {acl_name} (id={aid})")
    return aid


def main():
    parser = argparse.ArgumentParser(description="Fix tour line ACLs for public/portal users")
    parser.add_argument('--target', action='store_true', help="Run against production instance")
    args = parser.parse_args()

    if args.target:
        from odoo_cli.target import get_target_client
        client = get_target_client()
        if not client:
            print("[ERROR] TARGET_MIGRATION_* variables not configured in .env")
            return
        client.connect()
        print(f"Connected to TARGET (production) as uid={client.uid}")
    else:
        client = OdooClient()
        client.connect()
        print(f"Connected to Odoo as uid={client.uid}")

    # Get group IDs
    public_gid = get_group_id(client, 'base.group_public')
    portal_gid = get_group_id(client, 'base.group_portal')
    print(f"Groups: public={public_gid}, portal={portal_gid}")

    if not public_gid or not portal_gid:
        print("[ERROR] Could not find public/portal group IDs")
        return

    for model_name in LINE_MODELS:
        print(f"\n{model_name}:")

        # Get model ID
        model = client.search_read('ir.model',
            domain=[['model', '=', model_name]], fields=['id'], limit=1)
        if not model:
            print(f"  [SKIP] Model not found")
            continue
        model_id = model[0]['id']

        # Add read-only ACL for public users
        ensure_readonly_acl(client,
            f'access_{model_name}_public',
            model_id, public_gid)

        # Add read-only ACL for portal users
        ensure_readonly_acl(client,
            f'access_{model_name}_portal',
            model_id, portal_gid)

    print("\nDone! Tour product pages should now be accessible to public/portal users.")


if __name__ == "__main__":
    main()
