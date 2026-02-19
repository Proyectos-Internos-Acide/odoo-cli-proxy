#!/usr/bin/env python3
"""Compare source and target Odoo instances for migration readiness.

Connects to both instances (source via ODOO_* env vars, target via
TARGET_MIGRATION_* env vars) and reports what custom configurations
exist in the source but are missing from the target.

Read-only: never writes to either instance.

Usage:
    uv run python business_units/hotel-trip-agency/compare_instances.py
    uv run python business_units/hotel-trip-agency/compare_instances.py --category models
    uv run python business_units/hotel-trip-agency/compare_instances.py --verbose
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from odoo_cli import OdooClient, get_target_client


# ── Helpers ──────────────────────────────────────────────────────────────

def _get_module_record_ids(client, model):
    """Get IDs of records that come from installed modules (have ir.model.data)."""
    data = client.search_read('ir.model.data',
                              [('model', '=', model)],
                              fields=['res_id'])
    return {d['res_id'] for d in data}


def _diff(src_records, tgt_records, key_fn, label_fn=None):
    """Compute diff between source and target record lists.

    Args:
        src_records: list of dicts from source
        tgt_records: list of dicts from target
        key_fn: function(record) -> hashable match key
        label_fn: function(record) -> display string (optional)

    Returns:
        dict with keys: missing, present, extra, src_by_key, tgt_by_key
    """
    if label_fn is None:
        label_fn = lambda r: str(key_fn(r))

    src_by_key = {key_fn(r): r for r in src_records}
    tgt_by_key = {key_fn(r): r for r in tgt_records}

    src_keys = set(src_by_key.keys())
    tgt_keys = set(tgt_by_key.keys())

    return {
        'missing': sorted(src_keys - tgt_keys, key=str),
        'present': sorted(src_keys & tgt_keys, key=str),
        'extra': sorted(tgt_keys - src_keys, key=str),
        'src_by_key': src_by_key,
        'tgt_by_key': tgt_by_key,
        'label_fn': label_fn,
    }


def _print_diff(title, number, diff, verbose=False):
    """Print a comparison section."""
    n_src = len(diff['missing']) + len(diff['present'])
    n_tgt = len(diff['present']) + len(diff['extra'])
    n_missing = len(diff['missing'])

    print(f"\n{number}. {title}")
    print(f"   Source: {n_src} | Target: {n_tgt} | Faltan: {n_missing}")

    if n_missing == 0 and not verbose:
        print("   [OK] Todo sincronizado")
        return n_missing

    label_fn = diff['label_fn']
    src_by_key = diff['src_by_key']

    for key in diff['missing']:
        rec = src_by_key[key]
        print(f"   [FALTA] {label_fn(rec)}")

    if verbose:
        for key in diff['present']:
            rec = src_by_key[key]
            print(f"   [OK]    {label_fn(rec)}")
        for key in diff['extra']:
            rec = diff['tgt_by_key'][key]
            print(f"   [EXTRA] {label_fn(rec)}")

    return n_missing


# ── Comparison Categories ────────────────────────────────────────────────

def compare_models(source, target, verbose=False):
    """Custom models (ir.model with state=manual)."""
    domain = [('state', '=', 'manual')]
    fields = ['model', 'name', 'state']

    src = source.search_read('ir.model', domain, fields=fields)
    tgt = target.search_read('ir.model', domain, fields=fields)

    diff = _diff(src, tgt,
                 key_fn=lambda r: r['model'],
                 label_fn=lambda r: f"{r['model']} ({r['name']})")

    return _print_diff("Modelos Custom (ir.model, state=manual)", 1, diff, verbose)


def compare_fields(source, target, verbose=False):
    """Custom fields (ir.model.fields with x_ prefix, state=manual)."""
    domain = [('name', '=like', 'x_%'), ('state', '=', 'manual')]
    fields = ['model', 'name', 'field_description', 'ttype', 'relation']

    src = source.search_read('ir.model.fields', domain, fields=fields)
    tgt = target.search_read('ir.model.fields', domain, fields=fields)

    diff = _diff(src, tgt,
                 key_fn=lambda r: (r['model'], r['name']),
                 label_fn=lambda r: f"{r['model']}.{r['name']} ({r['ttype']})")

    return _print_diff("Campos Custom (ir.model.fields, x_*)", 2, diff, verbose)


def compare_automations(source, target, verbose=False):
    """Custom automations (base.automation not from modules)."""
    fields = ['name', 'model_id', 'trigger', 'active']

    src_all = source.search_read('base.automation', [], fields=fields)
    tgt_all = target.search_read('base.automation', [], fields=fields)

    src_module_ids = _get_module_record_ids(source, 'base.automation')
    tgt_module_ids = _get_module_record_ids(target, 'base.automation')

    src = [a for a in src_all if a['id'] not in src_module_ids]
    tgt = [a for a in tgt_all if a['id'] not in tgt_module_ids]

    diff = _diff(src, tgt,
                 key_fn=lambda r: r['name'],
                 label_fn=lambda r: f"{r['name']} ({r['model_id'][1]}, {r['trigger']})")

    return _print_diff("Automatizaciones Custom (base.automation)", 3, diff, verbose)


def compare_server_actions(source, target, verbose=False):
    """Custom server actions (state=code, not from modules)."""
    domain = [('state', '=', 'code')]
    fields = ['name', 'model_id', 'state']

    src_all = source.search_read('ir.actions.server', domain, fields=fields)
    tgt_all = target.search_read('ir.actions.server', domain, fields=fields)

    src_module_ids = _get_module_record_ids(source, 'ir.actions.server')
    tgt_module_ids = _get_module_record_ids(target, 'ir.actions.server')

    src = [a for a in src_all if a['id'] not in src_module_ids]
    tgt = [a for a in tgt_all if a['id'] not in tgt_module_ids]

    diff = _diff(src, tgt,
                 key_fn=lambda r: r['name'],
                 label_fn=lambda r: f"{r['name']} ({r['model_id'][1]})")

    return _print_diff("Server Actions Custom (ir.actions.server)", 4, diff, verbose)


def compare_views(source, target, verbose=False):
    """Custom views (ir.ui.view not from modules)."""
    fields = ['name', 'model', 'type', 'inherit_id']

    src_all = source.search_read('ir.ui.view', [], fields=fields)
    tgt_all = target.search_read('ir.ui.view', [], fields=fields)

    src_module_ids = _get_module_record_ids(source, 'ir.ui.view')
    tgt_module_ids = _get_module_record_ids(target, 'ir.ui.view')

    src = [v for v in src_all if v['id'] not in src_module_ids]
    tgt = [v for v in tgt_all if v['id'] not in tgt_module_ids]

    diff = _diff(src, tgt,
                 key_fn=lambda r: r['name'],
                 label_fn=lambda r: f"{r['name']} ({r['model'] or 'qweb'}, {r['type']})")

    return _print_diff("Vistas Custom (ir.ui.view)", 5, diff, verbose)


def compare_acls(source, target, verbose=False):
    """ACLs for custom models (x_ prefix)."""
    domain = [('model_id.model', '=like', 'x_%')]
    fields = ['name', 'model_id', 'group_id',
              'perm_read', 'perm_write', 'perm_create', 'perm_unlink']

    src = source.search_read('ir.model.access', domain, fields=fields)
    tgt = target.search_read('ir.model.access', domain, fields=fields)

    diff = _diff(src, tgt,
                 key_fn=lambda r: r['name'],
                 label_fn=lambda r: (
                     f"{r['name']} ({r['model_id'][1]}) "
                     f"r={'Y' if r['perm_read'] else 'N'} "
                     f"w={'Y' if r['perm_write'] else 'N'} "
                     f"c={'Y' if r['perm_create'] else 'N'} "
                     f"d={'Y' if r['perm_unlink'] else 'N'}"
                 ))

    return _print_diff("ACLs para modelos custom (ir.model.access)", 6, diff, verbose)


def compare_products(source, target, verbose=False):
    """Service products (tour-related)."""
    domain = [('type', '=', 'service'), ('sale_ok', '=', True)]
    fields = ['name', 'default_code', 'type', 'categ_id', 'service_tracking']

    src = source.search_read('product.template', domain, fields=fields)
    tgt = target.search_read('product.template', domain, fields=fields)

    def key_fn(r):
        return r['default_code'] if r['default_code'] else r['name']

    diff = _diff(src, tgt,
                 key_fn=key_fn,
                 label_fn=lambda r: (
                     f"[{r['default_code'] or 'sin ref'}] {r['name']} "
                     f"({r['categ_id'][1] if r['categ_id'] else 'sin cat'})"
                 ))

    return _print_diff("Productos de Servicio (product.template)", 7, diff, verbose)


def compare_templates(source, target, verbose=False):
    """Quotation templates (sale.order.template)."""
    fields = ['name', 'active']

    src = source.search_read('sale.order.template', [], fields=fields)
    tgt = target.search_read('sale.order.template', [], fields=fields)

    diff = _diff(src, tgt,
                 key_fn=lambda r: r['name'],
                 label_fn=lambda r: r['name'])

    return _print_diff("Plantillas de Cotizacion (sale.order.template)", 8, diff, verbose)


def compare_reports(source, target, verbose=False):
    """Custom reports (ir.actions.report not from modules)."""
    fields = ['name', 'report_name', 'model', 'report_type']

    src_all = source.search_read('ir.actions.report', [], fields=fields)
    tgt_all = target.search_read('ir.actions.report', [], fields=fields)

    src_module_ids = _get_module_record_ids(source, 'ir.actions.report')
    tgt_module_ids = _get_module_record_ids(target, 'ir.actions.report')

    src = [r for r in src_all if r['id'] not in src_module_ids]
    tgt = [r for r in tgt_all if r['id'] not in tgt_module_ids]

    diff = _diff(src, tgt,
                 key_fn=lambda r: r['report_name'],
                 label_fn=lambda r: f"{r['name']} ({r['model']}, {r['report_type']})")

    return _print_diff("Reportes Custom (ir.actions.report)", 9, diff, verbose)


# ── Category Registry ────────────────────────────────────────────────────

CATEGORIES = {
    'models': compare_models,
    'fields': compare_fields,
    'automations': compare_automations,
    'server_actions': compare_server_actions,
    'views': compare_views,
    'acls': compare_acls,
    'products': compare_products,
    'templates': compare_templates,
    'reports': compare_reports,
}


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Compare source and target Odoo instances for migration')
    parser.add_argument('--category', '-c',
                        choices=list(CATEGORIES.keys()) + ['all'],
                        default='all',
                        help='Category to compare (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show OK and EXTRA items too')
    args = parser.parse_args()

    # Connect to source
    print("Connecting to source instance...")
    source = OdooClient()
    source.connect()
    print(f"  Source: {source.db} (uid={source.uid})")

    # Connect to target
    print("Connecting to target instance...")
    target = get_target_client()
    if target is None:
        print("\n  ERROR: Target instance not configured.")
        print("  Set TARGET_MIGRATION_URL, TARGET_MIGRATION_DB,")
        print("  TARGET_MIGRATION_USERNAME, TARGET_MIGRATION_PASSWORD in .env")
        sys.exit(1)

    target.connect()
    print(f"  Target: {target.db} (uid={target.uid})")

    # Header
    print("\n" + "=" * 64)
    print("  COMPARACION DE INSTANCIAS")
    print(f"  Source: {source.db}")
    print(f"  Target: {target.db}")
    print("=" * 64)

    # Run comparisons
    if args.category == 'all':
        cats = CATEGORIES
    else:
        cats = {args.category: CATEGORIES[args.category]}

    total_missing = 0
    for name, fn in cats.items():
        try:
            n_missing = fn(source, target, verbose=args.verbose)
            total_missing += n_missing
        except Exception as e:
            print(f"\n  [ERROR] {name}: {e}")

    # Summary
    print("\n" + "=" * 64)
    print(f"  RESUMEN: {total_missing} elementos faltan en target")
    print("=" * 64)


if __name__ == '__main__':
    main()
