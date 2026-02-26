#!/usr/bin/env python3
"""READ-ONLY diagnostic: inspect automations 26, 27, 28 on x_operator_line.

Checks:
1. Automation active, trigger, trigger_field_ids, model_id, action_server_ids
2. Whether trigger_field_ids actually point to x_cost and x_cost_currency_id
3. Server action code content (full dump)
4. Cross-checks: model existence, financial fields on sale.order
5. All automations targeting x_operator_line

Usage:
    uv run python debug_automations.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odoo_cli import OdooClient


AUTOMATION_IDS = [26, 27, 28]
SEPARATOR = "=" * 80
THIN_SEP = "-" * 70


def print_section(title):
    print(f"\n{SEPARATOR}")
    print(f"  {title}")
    print(SEPARATOR)


def main():
    client = OdooClient()
    client.connect()
    print(f"Connected to: {client.url} (db: {client.db}, uid: {client.uid})")
    print(SEPARATOR)

    # ── 1. Read automations 26, 27, 28 by ID ──────────────────────────────
    print_section("1. AUTOMATIONS 26, 27, 28 - Full details")

    autos = client.search_read(
        'base.automation',
        domain=[['id', 'in', AUTOMATION_IDS]],
        fields=[
            'id', 'name', 'active', 'trigger', 'trigger_field_ids',
            'model_id', 'model_name', 'action_server_ids',
            'record_getter', 'filter_domain', 'filter_pre_domain',
        ],
    )

    # Index by ID for ordered output
    autos_by_id = {a['id']: a for a in autos}

    for aid in AUTOMATION_IDS:
        print(f"\n{THIN_SEP}")
        if aid not in autos_by_id:
            print(f"  AUTOMATION {aid}: *** NOT FOUND ***")
            continue

        auto = autos_by_id[aid]
        print(f"  AUTOMATION {aid}: {auto['name']}")
        print(THIN_SEP)
        print(f"  active:            {auto['active']}")
        print(f"  trigger:           {auto['trigger']}")
        print(f"  model_id:          {auto['model_id']}")
        print(f"  model_name:        {auto.get('model_name', 'N/A')}")
        print(f"  record_getter:     {auto.get('record_getter', 'N/A')}")
        print(f"  filter_domain:     {auto.get('filter_domain', 'N/A')}")
        print(f"  filter_pre_domain: {auto.get('filter_pre_domain', 'N/A')}")

        # ── 1a. Trigger field IDs ──────────────────────────────────────
        trigger_field_ids = auto.get('trigger_field_ids', [])
        print(f"  trigger_field_ids: {trigger_field_ids}")

        if trigger_field_ids:
            fields_data = client.search_read(
                'ir.model.fields',
                domain=[['id', 'in', trigger_field_ids]],
                fields=['id', 'name', 'model', 'field_description', 'ttype', 'store'],
            )
            for f in fields_data:
                stored = f.get('store', 'N/A')
                print(
                    f"    -> Field id={f['id']}: {f['model']}.{f['name']} "
                    f"(ttype={f['ttype']}, stored={stored}) "
                    f'desc="{f["field_description"]}"'
                )

                # Verify it's on x_operator_line
                if f['model'] != 'x_operator_line':
                    print(f"       *** WARNING: field is on model '{f['model']}', "
                          f"expected 'x_operator_line' ***")
        else:
            print(f"    (no trigger fields set)")

        # ── 1b. Server action(s) ──────────────────────────────────────
        action_ids = auto.get('action_server_ids', [])
        print(f"  action_server_ids: {action_ids}")

        if action_ids:
            actions = client.search_read(
                'ir.actions.server',
                domain=[['id', 'in', action_ids]],
                fields=['id', 'name', 'state', 'model_id', 'model_name', 'code'],
            )
            for act in actions:
                print(f"\n    Server Action id={act['id']}")
                print(f"      name:       {act['name']}")
                print(f"      state:      {act['state']}")
                print(f"      model_id:   {act['model_id']}")
                print(f"      model_name: {act.get('model_name', 'N/A')}")

                code = act.get('code', '') or ''
                if code.strip():
                    lines = code.strip().split('\n')
                    print(f"      code ({len(lines)} lines):")
                    for i, line in enumerate(lines, 1):
                        print(f"        {i:3d}| {line}")

                    # Quick signature checks
                    print(f"\n      --- Code signature checks ---")
                    checks = {
                        'x_sale_order_id':          'x_sale_order_id' in code,
                        'x_cost_pen':               'x_cost_pen' in code,
                        'x_total_estimated_cost':   'x_total_estimated_cost' in code,
                        'x_estimated_margin':       'x_estimated_margin' in code,
                        'x_estimated_margin_percent': 'x_estimated_margin_percent' in code,
                        'so.write(...)':            'so.write(' in code,
                        'record.write(...)':        'record.write(' in code,
                        'datetime.date.today()':    'datetime.date.today()' in code,
                        '_convert':                 '_convert' in code,
                        'currency_rate':            'currency_rate' in code,
                    }
                    for label, present in checks.items():
                        status = "FOUND" if present else "MISSING"
                        marker = "  " if present else "**"
                        print(f"      {marker} {label}: {status}")
                else:
                    print(f"      *** CODE IS EMPTY ***")
        else:
            print(f"    *** NO SERVER ACTIONS LINKED ***")

    # ── 2. Cross-check: expected trigger fields exist on x_operator_line ───
    print_section("2. CROSS-CHECK: x_cost and x_cost_currency_id on x_operator_line")

    for fname in ['x_cost', 'x_cost_currency_id']:
        result = client.search_read(
            'ir.model.fields',
            domain=[['model', '=', 'x_operator_line'], ['name', '=', fname]],
            fields=['id', 'name', 'model', 'ttype', 'field_description', 'store'],
        )
        if result:
            f = result[0]
            print(f"  {fname}: id={f['id']}, ttype={f['ttype']}, "
                  f"stored={f.get('store', 'N/A')}, "
                  f'desc="{f["field_description"]}"')
        else:
            print(f"  {fname}: *** NOT FOUND on x_operator_line ***")

    # ── 3. Verify x_operator_line model exists ────────────────────────────
    print_section("3. CHECK: x_operator_line model")

    model = client.search_read(
        'ir.model',
        domain=[['model', '=', 'x_operator_line']],
        fields=['id', 'model', 'name', 'state'],
    )
    if model:
        m = model[0]
        print(f"  Model id={m['id']}: {m['model']} \"{m['name']}\" state={m['state']}")
    else:
        print(f"  *** x_operator_line MODEL NOT FOUND ***")

    # ── 4. List ALL automations targeting x_operator_line ──────────────────
    print_section("4. ALL automations on x_operator_line")

    all_autos = client.search_read(
        'base.automation',
        domain=[['model_name', '=', 'x_operator_line']],
        fields=['id', 'name', 'active', 'trigger', 'trigger_field_ids', 'action_server_ids'],
    )
    if all_autos:
        for a in all_autos:
            status = "ACTIVE" if a['active'] else "INACTIVE"
            print(
                f"  id={a['id']:3d} [{status:8s}] trigger={a['trigger']:12s} "
                f"fields={a['trigger_field_ids']} actions={a['action_server_ids']} "
                f'"{a["name"]}"'
            )
    else:
        print(f"  *** No automations found for x_operator_line ***")

    # ── 5. Check SO financial fields exist ─────────────────────────────────
    print_section("5. CHECK: Financial fields on sale.order")

    fin_fields = [
        'x_total_estimated_cost', 'x_estimated_margin',
        'x_estimated_margin_percent', 'x_total_estimated_cost_cur',
        'x_estimated_margin_cur',
    ]
    for fname in fin_fields:
        result = client.search_read(
            'ir.model.fields',
            domain=[['model', '=', 'sale.order'], ['name', '=', fname]],
            fields=['id', 'name', 'ttype', 'store'],
        )
        if result:
            f = result[0]
            print(f"  {fname}: id={f['id']}, ttype={f['ttype']}, stored={f.get('store', 'N/A')}")
        else:
            print(f"  {fname}: *** NOT FOUND ***")

    # ── 6. Quick sanity: x_sale_order_id on x_operator_line ────────────────
    print_section("6. CHECK: x_sale_order_id field on x_operator_line")

    result = client.search_read(
        'ir.model.fields',
        domain=[['model', '=', 'x_operator_line'], ['name', '=', 'x_sale_order_id']],
        fields=['id', 'name', 'ttype', 'relation', 'store'],
    )
    if result:
        f = result[0]
        print(f"  x_sale_order_id: id={f['id']}, ttype={f['ttype']}, "
              f"relation={f.get('relation', 'N/A')}, stored={f.get('store', 'N/A')}")
    else:
        print(f"  x_sale_order_id: *** NOT FOUND on x_operator_line ***")

    print(f"\n{SEPARATOR}")
    print("  DIAGNOSTIC COMPLETE")
    print(SEPARATOR)


if __name__ == '__main__':
    main()
