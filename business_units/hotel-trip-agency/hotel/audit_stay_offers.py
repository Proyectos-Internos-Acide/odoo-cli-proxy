#!/usr/bin/env python3
"""Audit stay offer variants and their resource assignments in production."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from odoo_cli import OdooClient


def main():
    client = OdooClient(
        url='https://machupicchu-afdestiny-production.odoo.com/',
        db='machupicchu-afdestiny-production',
        username='ayfdestinyeirl@gmail.com',
        password='L^yUbD2^+p^2h.#',
    )
    uid = client.connect()
    print(f"Connected to PRODUCTION as uid={uid}\n")

    # 1. Get all stay offer templates
    templates = client.search_read(
        'product.template',
        domain=[['x_is_a_room_offer', '=', True]],
        fields=['id', 'name', 'product_variant_ids', 'product_variant_count'],
    )
    print(f"Found {len(templates)} stay offer templates\n")

    # 2. Get all variant IDs
    all_variant_ids = []
    for t in templates:
        all_variant_ids.extend(t.get('product_variant_ids', []))

    # 3. Try to read variants - first try with resource_id
    try:
        variants = client.search_read(
            'product.product',
            domain=[['id', 'in', all_variant_ids]],
            fields=['id', 'display_name', 'product_tmpl_id', 'resource_id'],
        )
        has_resource_id = True
    except Exception:
        variants = client.search_read(
            'product.product',
            domain=[['id', 'in', all_variant_ids]],
            fields=['id', 'display_name', 'product_tmpl_id'],
        )
        has_resource_id = False
        print("(product.product does NOT have resource_id field)\n")

    # 4. Get planning roles for room offers
    roles = client.search_read(
        'planning.role',
        domain=[['x_is_a_room_offer', '=', True]],
        fields=['id', 'name', 'resource_ids'],
    )
    print(f"=== Planning Roles (room offers): {len(roles)} ===")
    role_map = {}
    for r in roles:
        res_ids = r.get('resource_ids', [])
        role_map[r['id']] = r
        print(f"  Role '{r['name']}' (id={r['id']}): {len(res_ids)} resources → ids={res_ids}")

    # 5. Get all resources linked to these roles
    all_resource_ids = []
    for r in roles:
        all_resource_ids.extend(r.get('resource_ids', []))
    all_resource_ids = list(set(all_resource_ids))

    resource_map = {}
    if all_resource_ids:
        resources = client.search_read(
            'resource.resource',
            domain=[['id', 'in', all_resource_ids]],
            fields=['id', 'name', 'resource_type'],
        )
        resource_map = {r['id']: r for r in resources}
        print(f"\n=== Resources ({len(resources)}) ===")
        for r in resources:
            print(f"  '{r['name']}' (id={r['id']}, type={r['resource_type']})")

    # 6. Build template → role mapping (by name match)
    template_map = {t['id']: t for t in templates}
    variant_map = {v['id']: v for v in variants}

    # Group variants by template
    variants_by_template = {}
    for v in variants:
        tmpl_id = v['product_tmpl_id'][0] if v.get('product_tmpl_id') else None
        if tmpl_id:
            variants_by_template.setdefault(tmpl_id, []).append(v)

    # 7. For each variant, check planning.slot resource assignments
    print("\n" + "=" * 90)
    print("AUDIT: Stay Offer Variants → Resource Assignment (from planning.slot)")
    print("=" * 90)

    issues = []

    for tmpl in sorted(templates, key=lambda t: t['name']):
        tmpl_id = tmpl['id']
        v_list = variants_by_template.get(tmpl_id, [])
        print(f"\n{'─' * 90}")
        print(f"📦 {tmpl['name']} (template id={tmpl_id}, {len(v_list)} variants)")
        print(f"{'─' * 90}")

        template_resources = {}  # variant_id → set of (res_id, res_name)

        for v in v_list:
            # Get ALL slots for this variant (not just recent)
            slots = client.search_read(
                'planning.slot',
                domain=[['sale_line_id.product_id', '=', v['id']]],
                fields=['resource_id'],
            )
            resources_used = set()
            no_resource_count = 0
            for s in slots:
                res = s.get('resource_id')
                if res:
                    resources_used.add((res[0], res[1]))
                else:
                    no_resource_count += 1

            template_resources[v['id']] = resources_used

            if has_resource_id:
                res = v.get('resource_id')
                configured_res = f"→ configured: {res[1]} (id={res[0]})" if res else "→ configured: NONE"
            else:
                configured_res = ""

            res_names = [r[1] for r in resources_used]
            status = "✅" if len(resources_used) <= 1 else "⚠️  MULTIPLE RESOURCES"
            print(f"  {status} {v['display_name']} (id={v['id']})")
            print(f"     Slots: {len(slots)} total, {no_resource_count} without resource")
            if resources_used:
                print(f"     Resources used: {res_names}")
            if configured_res:
                print(f"     {configured_res}")

        # Check consistency: all variants of same template should use same resource
        all_resources_for_template = set()
        for res_set in template_resources.values():
            all_resources_for_template.update(res_set)

        if len(all_resources_for_template) > 1:
            issue = f"❌ INCONSISTENT: {tmpl['name']} variants point to DIFFERENT resources: {[r[1] for r in all_resources_for_template]}"
            issues.append(issue)
            print(f"\n  {issue}")
        elif len(all_resources_for_template) == 1:
            res_name = list(all_resources_for_template)[0][1]
            # Check if resource name matches expected pattern (room number)
            print(f"\n  ✅ All variants → resource '{res_name}'")
        else:
            print(f"\n  ⚠️  No planning slots found for any variant")

    # Also check if variants have resource_id configured directly
    if has_resource_id:
        print("\n" + "=" * 90)
        print("CONFIGURED resource_id ON VARIANTS (product.product.resource_id)")
        print("=" * 90)
        for tmpl in sorted(templates, key=lambda t: t['name']):
            tmpl_id = tmpl['id']
            v_list = variants_by_template.get(tmpl_id, [])
            print(f"\n📦 {tmpl['name']}")
            resource_names = set()
            for v in v_list:
                res = v.get('resource_id')
                res_name = res[1] if res else 'NONE'
                resource_names.add(res_name)
                print(f"  {v['display_name']}: {res_name}")
            if len(resource_names) > 1:
                issues.append(f"❌ {tmpl['name']}: configured resource_id differs across variants: {resource_names}")

    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    if issues:
        print(f"\n⚠️  Found {len(issues)} issue(s):")
        for i in issues:
            print(f"  {i}")
    else:
        print("\n✅ All stay offer variants are consistent (same resource per template)")


if __name__ == '__main__':
    main()
