#!/usr/bin/env python3
"""
Fetch published hotel (Lodging) and restaurant products from Odoo.

This script retrieves all published products in the Lodging category and Restaurant
categories, displaying their details including pricing and optional products.
"""

import xmlrpc.client
from typing import List, Dict, Any

# Connection details
URL = "https://machupicchuafdestiny3.odoo.com/"
DB = "machupicchuafdestiny3"
USER = "ayfdestinyeirl@gmail.com"
PASSWORD = "L^yUbD2^+p^2h.#"

# Category IDs
LODGING_CATEGORY_ID = 7
UNCATEGORIZED_ROOM_IDS = [15, 17]
RESTAURANT_CATEGORY_IDS = [1, 2, 3, 4, 5, 6, 8]

def connect_to_odoo():
    """Connect to Odoo via XML-RPC."""
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, USER, PASSWORD, {})
    if not uid:
        raise Exception("Authentication failed")

    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    return models, uid

def fetch_products(models, uid):
    """Fetch all published products from Odoo."""
    domain = [('website_published', '=', True)]
    fields = ['id', 'name', 'list_price', 'public_categ_ids', 'optional_product_ids',
              'description_sale', 'website_url']

    product_ids = models.execute_kw(
        DB, uid, PASSWORD,
        'product.template', 'search',
        [domain]
    )

    if not product_ids:
        return []

    products = models.execute_kw(
        DB, uid, PASSWORD,
        'product.template', 'read',
        [product_ids, fields]
    )

    return products

def categorize_products(products: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorize products into Lodging and Restaurant groups.

    Returns a dict with keys 'lodging' and 'restaurant', each containing a list of products.
    """
    lodging_products = []
    restaurant_products = []

    for product in products:
        product_id = product['id']
        categ_ids = product['public_categ_ids']

        # Check if product is a room (uncategorized rooms or in Lodging category)
        is_lodging = (
            product_id in UNCATEGORIZED_ROOM_IDS or
            any(categ_id == LODGING_CATEGORY_ID for categ_id in categ_ids)
        )

        # Check if product is in Restaurant categories
        is_restaurant = any(categ_id in RESTAURANT_CATEGORY_IDS for categ_id in categ_ids)

        if is_lodging:
            lodging_products.append(product)
        elif is_restaurant:
            restaurant_products.append(product)

    return {
        'lodging': lodging_products,
        'restaurant': restaurant_products
    }

def format_product_info(product: Dict[str, Any]) -> str:
    """Format a single product's information for display."""
    product_id = product['id']
    name = product['name']
    price = product['list_price']
    optional_ids = product['optional_product_ids']

    info = f"  ID: {product_id}\n"
    info += f"  Name: {name}\n"
    info += f"  Price: {price}\n"
    info += f"  Optional Products: {optional_ids if optional_ids else 'None'}\n"

    return info

def display_results(categorized: Dict[str, List[Dict[str, Any]]]):
    """Display the categorized products in a clear format."""

    print("\n" + "="*80)
    print("PUBLISHED HOTEL AND RESTAURANT PRODUCTS")
    print("="*80 + "\n")

    # Lodging Products
    print("LODGING PRODUCTS")
    print("-" * 80)
    lodging = categorized['lodging']
    if lodging:
        print(f"Total: {len(lodging)} products\n")
        for product in sorted(lodging, key=lambda p: p['name']):
            print(format_product_info(product))
    else:
        print("No lodging products found.\n")

    # Restaurant Products
    print("\nRESTAURANT PRODUCTS")
    print("-" * 80)
    restaurant = categorized['restaurant']
    if restaurant:
        print(f"Total: {len(restaurant)} products\n")
        for product in sorted(restaurant, key=lambda p: p['name']):
            print(format_product_info(product))
    else:
        print("No restaurant products found.\n")

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Lodging Products: {len(lodging)}")
    print(f"Restaurant Products: {len(restaurant)}")
    print(f"Total Published Products: {len(lodging) + len(restaurant)}")
    print("="*80 + "\n")

def main():
    """Main function."""
    try:
        print("Connecting to Odoo...")
        models, uid = connect_to_odoo()
        print(f"✓ Connected as UID: {uid}\n")

        print("Fetching published products...")
        products = fetch_products(models, uid)
        print(f"✓ Found {len(products)} published products\n")

        print("Categorizing products...")
        categorized = categorize_products(products)

        display_results(categorized)

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
