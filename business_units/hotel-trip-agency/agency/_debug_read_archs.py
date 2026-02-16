"""
Debug script: read arch XML of specific ir.ui.view records
to write correct xpath expressions.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from odoo_cli import OdooClient


def main():
    client = OdooClient()
    client.connect()
    print("Connected.\n")

    # 1. Read view id=3358 (website_sale.shop_product_buttons)
    print("=" * 80)
    print("VIEW id=3358  (website_sale.shop_product_buttons)")
    print("=" * 80)
    views = client.search_read(
        'ir.ui.view',
        [['id', '=', 3358]],
        fields=['id', 'name', 'key', 'inherit_id', 'arch'],
    )
    if views:
        v = views[0]
        print(f"  name: {v.get('name')}")
        print(f"  key:  {v.get('key')}")
        print(f"  inherit_id: {v.get('inherit_id')}")
        print()
        print(v.get('arch', '(no arch)'))
    else:
        print("  NOT FOUND")

    # 2. Read view id=3367 (website_sale.cta_wrapper)
    print("\n" + "=" * 80)
    print("VIEW id=3367  (website_sale.cta_wrapper)")
    print("=" * 80)
    views = client.search_read(
        'ir.ui.view',
        [['id', '=', 3367]],
        fields=['id', 'name', 'key', 'inherit_id', 'arch'],
    )
    if views:
        v = views[0]
        print(f"  name: {v.get('name')}")
        print(f"  key:  {v.get('key')}")
        print(f"  inherit_id: {v.get('inherit_id')}")
        print()
        print(v.get('arch', '(no arch)'))
    else:
        print("  NOT FOUND")

    # 3. Search for views that inherit from id=3367 (cta_wrapper)
    #    Specifically looking for the booking engine one.
    print("\n" + "=" * 80)
    print("VIEWS INHERITING FROM id=3367  (cta_wrapper)")
    print("=" * 80)
    children = client.search_read(
        'ir.ui.view',
        [['inherit_id', '=', 3367]],
        fields=['id', 'name', 'key', 'inherit_id', 'arch', 'active'],
    )
    if children:
        for v in children:
            print(f"\n--- View id={v['id']}  active={v.get('active')} ---")
            print(f"  name: {v.get('name')}")
            print(f"  key:  {v.get('key')}")
            print()
            print(v.get('arch', '(no arch)'))
    else:
        print("  NO CHILDREN FOUND")

    # Also search for views inheriting from 3358 for completeness
    print("\n" + "=" * 80)
    print("VIEWS INHERITING FROM id=3358  (shop_product_buttons)")
    print("=" * 80)
    children2 = client.search_read(
        'ir.ui.view',
        [['inherit_id', '=', 3358]],
        fields=['id', 'name', 'key', 'inherit_id', 'arch', 'active'],
    )
    if children2:
        for v in children2:
            print(f"\n--- View id={v['id']}  active={v.get('active')} ---")
            print(f"  name: {v.get('name')}")
            print(f"  key:  {v.get('key')}")
            print()
            print(v.get('arch', '(no arch)'))
    else:
        print("  NO CHILDREN FOUND")


if __name__ == '__main__':
    main()
