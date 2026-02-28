#!/usr/bin/env python3
"""
Verification script to check optional_product_ids on tour products.
Reads all website-published products in tour categories and reports
how many have optional products set.
"""

import xmlrpc.client
import sys
from collections import defaultdict

# Connection details
URL = "https://machupicchuafdestiny3.odoo.com/"
DB = "machupicchuafdestiny3"
USER = "ayfdestinyeirl@gmail.com"
PASSWORD = "L^yUbD2^+p^2h.#"

# Tour category IDs to check
TOUR_CATEGORY_IDS = [9, 10, 11, 12, 13, 14]

def main():
    # Initialize connection
    print(f"Connecting to {URL} (DB: {DB})...")

    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

    try:
        uid = common.authenticate(DB, USER, PASSWORD, {})
        if not uid:
            print("ERROR: Authentication failed")
            sys.exit(1)
        print(f"Authenticated as user {uid}\n")
    except Exception as e:
        print(f"ERROR: Authentication failed - {e}")
        sys.exit(1)

    # Search for published products in tour categories
    print("Searching for published tour products...")
    domain = [
        ("website_published", "=", True),
        ("public_categ_ids", "in", TOUR_CATEGORY_IDS),
    ]

    product_ids = models.execute_kw(
        DB, uid, PASSWORD, "product.template", "search", [domain]
    )

    print(f"Found {len(product_ids)} published tour products\n")

    if not product_ids:
        print("No products found.")
        return

    # Read product data with optional_product_ids
    print("Reading product details...")
    products = models.execute_kw(
        DB, uid, PASSWORD, "product.template", "read",
        [product_ids],
        {"fields": ["id", "name", "optional_product_ids", "categ_id", "public_categ_ids"]}
    )

    # Analyze results
    with_optional = 0
    without_optional = 0
    products_without = []

    for product in products:
        product_id = product["id"]
        name = product["name"]
        optional_ids = product.get("optional_product_ids", [])

        if optional_ids:
            with_optional += 1
            count = len(optional_ids)
            print(f"✓ {product_id:5d} | {name:50s} | {count} optional product(s)")
        else:
            without_optional += 1
            products_without.append((product_id, name))

    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total products:         {len(products)}")
    print(f"With optional products: {with_optional} ({100*with_optional/len(products):.1f}%)")
    print(f"WITHOUT optional products: {without_optional} ({100*without_optional/len(products):.1f}%)")

    if products_without:
        print("\n" + "="*80)
        print("PRODUCTS WITHOUT OPTIONAL PRODUCTS")
        print("="*80)
        for product_id, name in products_without:
            print(f"  {product_id:5d} | {name}")

    print("\n" + "="*80)

if __name__ == "__main__":
    main()
