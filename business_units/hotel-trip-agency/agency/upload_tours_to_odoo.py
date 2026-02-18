#!/usr/bin/env python3
"""
Upload scraped WordPress tour data to Odoo products.

For each tour:
  - If a product.template with matching name exists → update description_ecommerce
  - If no match → create a new product.template (service, tour category)

Reads from: generated/wordpress_tours.json
Writes to:  Odoo (test2 instance via XML-RPC)

Usage:
    # Dry run (preview what would happen)
    python business_units/hotel-trip-agency/agency/upload_tours_to_odoo.py --dry-run

    # Actually create/update products
    python business_units/hotel-trip-agency/agency/upload_tours_to_odoo.py

    # Only update existing products (skip creation)
    python business_units/hotel-trip-agency/agency/upload_tours_to_odoo.py --update-only

    # Only create new products (skip existing)
    python business_units/hotel-trip-agency/agency/upload_tours_to_odoo.py --create-only
"""
import argparse
import base64
import json
import re
import sys
import os
import time
from html import escape
from pathlib import Path

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from odoo_cli import OdooClient

# ── Constants ──
TOURS_JSON = Path(__file__).parent / "generated" / "wordpress_tours.json"
TOUR_CATEGORY_NAME = "Tours y Paquetes turísticos"
PUBLIC_CATEGORY_ADVENTURE = 11  # "Adventure" public ecommerce category

WP_IMAGE_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    ),
}


# Import shared builders from setup_extended_description
from agency.setup_extended_description import (
    build_short_description_html,
    build_extended_description_html,
)


def parse_price_pen(price_str: str) -> float:
    """Parse 'S/120.00' or 'S/1,200.00' to a float."""
    if not price_str:
        return 0.0
    cleaned = re.sub(r'[^\d.,]', '', price_str)
    cleaned = cleaned.replace(',', '')
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def download_image_b64(url: str) -> str | None:
    """Download an image and return base64-encoded content."""
    try:
        resp = requests.get(url, headers=WP_IMAGE_HEADERS, timeout=15)
        resp.raise_for_status()
        if len(resp.content) < 500:  # Skip tiny/broken images
            return None
        return base64.b64encode(resp.content).decode('ascii')
    except requests.RequestException:
        return None


def find_existing_products(client: OdooClient) -> dict:
    """Get all existing tour products from Odoo, keyed by lowercase name."""
    products = client.search_read('product.template',
        domain=[['categ_id.name', 'ilike', 'Tours']],
        fields=['id', 'name', 'description_ecommerce', 'x_extended_description',
                'website_published', 'list_price', 'active'],
        order='name')
    return {p['name'].lower().strip(): p for p in products}


def find_tour_category(client: OdooClient) -> int:
    """Find the 'Tours y Paquetes turísticos' product category ID."""
    cats = client.search_read('product.category',
        domain=[['name', 'ilike', 'Tours y Paquetes']],
        fields=['id', 'name'],
        limit=1)
    if cats:
        return cats[0]['id']
    raise RuntimeError(f"Category '{TOUR_CATEGORY_NAME}' not found in Odoo")


def main():
    parser = argparse.ArgumentParser(description="Upload WordPress tours to Odoo")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview changes without writing to Odoo")
    parser.add_argument('--update-only', action='store_true',
                        help="Only update existing products, skip creation")
    parser.add_argument('--create-only', action='store_true',
                        help="Only create new products, skip updates")
    parser.add_argument('--with-images', action='store_true',
                        help="Download and upload images from WordPress")
    args = parser.parse_args()

    # Load scraped data
    with open(TOURS_JSON, 'r', encoding='utf-8') as f:
        tours = json.load(f)

    print(f"Loaded {len(tours)} tours from {TOURS_JSON}")

    # Connect to Odoo
    client = OdooClient()
    client.connect()
    print(f"Connected to Odoo as uid={client.uid}")

    # Get existing products and category
    existing = find_existing_products(client)
    categ_id = find_tour_category(client)
    print(f"Found {len(existing)} existing tour products")
    print(f"Tour category ID: {categ_id}")

    # Process each tour
    created = 0
    updated = 0
    skipped = 0

    for tour in tours:
        if 'error' in tour:
            print(f"  [SKIP] {tour['slug']}: scrape error")
            skipped += 1
            continue

        title = tour['title']
        slug = tour['slug']
        short_html = build_short_description_html(tour)
        extended_html = build_extended_description_html(tour)
        price = parse_price_pen(tour.get('price_pen', ''))

        # Try to find existing product by name (case-insensitive)
        existing_product = existing.get(title.lower().strip())

        if existing_product:
            # ── UPDATE existing product ──
            if args.create_only:
                print(f"  [SKIP] {title}: exists (id={existing_product['id']}), --create-only")
                skipped += 1
                continue

            pid = existing_product['id']
            has_desc = bool(existing_product.get('description_ecommerce'))

            if args.dry_run:
                print(f"  [UPDATE] id={pid} {title}"
                      f" (short={len(short_html)}ch, extended={len(extended_html)}ch)")
            else:
                vals = {
                    'description_ecommerce': short_html,
                    'x_extended_description': extended_html,
                }
                # Only update price if current is 0
                if price > 0 and existing_product.get('list_price', 0) == 0:
                    vals['list_price'] = price

                client.execute('product.template', 'write', [pid], vals)
                print(f"  [UPDATED] id={pid} {title}")

                # Upload images if requested and product has no extra images
                if args.with_images and tour.get('images'):
                    _upload_images(client, pid, tour['images'])

            updated += 1

        else:
            # ── CREATE new product ──
            if args.update_only:
                print(f"  [SKIP] {title}: new product, --update-only")
                skipped += 1
                continue

            if args.dry_run:
                print(f"  [CREATE] {title} (price={price},"
                      f" short={len(short_html)}ch, extended={len(extended_html)}ch)")
            else:
                vals = {
                    'name': title,
                    'type': 'service',
                    'sale_ok': True,
                    'purchase_ok': False,
                    'list_price': price,
                    'categ_id': categ_id,
                    'service_tracking': 'project_only',
                    'description_ecommerce': short_html,
                    'x_extended_description': extended_html,
                    'website_published': False,  # Review before publishing
                    'public_categ_ids': [(4, PUBLIC_CATEGORY_ADVENTURE)],
                }

                result = client.execute('product.template', 'create', [vals])
                new_id = result[0] if isinstance(result, list) else result
                print(f"  [CREATED] id={new_id} {title}")

                # Upload images if requested
                if args.with_images and tour.get('images'):
                    _upload_images(client, new_id, tour['images'])

                time.sleep(0.3)

            created += 1

    # Summary
    print(f"\n{'=' * 60}")
    print(f"MIGRATION SUMMARY{'  (DRY RUN)' if args.dry_run else ''}:")
    print(f"  Created:  {created}")
    print(f"  Updated:  {updated}")
    print(f"  Skipped:  {skipped}")
    print(f"  Total:    {len(tours)}")

    if args.dry_run:
        print("\nThis was a dry run. Run without --dry-run to apply changes.")


def _upload_images(client: OdooClient, product_id: int, image_urls: list):
    """Download images from WordPress and attach to the Odoo product."""
    for i, url in enumerate(image_urls):
        b64 = download_image_b64(url)
        if not b64:
            continue

        # First image → main product image
        if i == 0:
            client.execute('product.template', 'write', [product_id],
                           {'image_1920': b64})
            print(f"    [IMG] Main image set")
        else:
            # Extra images → product_template_image_ids
            fname = url.split('/')[-1].split('?')[0]
            client.execute('product.image', 'create', [{
                'product_tmpl_id': product_id,
                'name': fname,
                'image_1920': b64,
            }])
            print(f"    [IMG] Extra image: {fname}")

        time.sleep(0.3)


if __name__ == "__main__":
    main()
