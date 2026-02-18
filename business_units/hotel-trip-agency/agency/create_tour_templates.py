#!/usr/bin/env python3
"""
Create/update quotation templates (sale.order.template) with Biblia Operativa
data from scraped WordPress tours.

For each tour:
  - Creates a sale.order.template with x_is_tour=True
  - Populates x_itinerary_line_ids (parsed day-by-day from scraped text)
  - Sets x_inclusions (HTML), x_key_times, x_special_observations
  - Links a sale.order.template.line to the matching product

Prerequisites:
  - Products must already exist (run upload_tours_to_odoo.py first)
  - Biblia Operativa models/fields must be set up (setup_biblia_operativa.py)

Usage:
    python business_units/hotel-trip-agency/agency/create_tour_templates.py --dry-run
    python business_units/hotel-trip-agency/agency/create_tour_templates.py
"""
import argparse
import json
import re
import sys
import os
import time
from html import escape
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from odoo_cli import OdooClient

TOURS_JSON = Path(__file__).parent / "generated" / "wordpress_tours.json"

# ── Itinerary parsing ────────────────────────────────────────────────────

DAY_HEADER_RE = re.compile(
    r'^(?:D[ií]a|DIA|Day)\s*0?(\d+)\s*[:.\-–—]\s*(.*)',
    re.IGNORECASE
)

# Stop words: lines that signal end of itinerary content
STOP_PHRASES = [
    'tours son en servicio',
    'pago al 100%',
    'puede pagar con',
    'precio por persona',
    'precios no son válidos',
]

ACCOMMODATION_KEYWORDS = [
    'campamento', 'hotel', 'alojamiento', 'pernocte',
    'hospedaremos', 'hospedaje', 'lodge', 'refugio',
]

MEAL_MAP = {
    'desayuno': 'Desayuno',
    'almuerzo': 'Almuerzo',
    'cena': 'Cena',
    'box lunch': 'Box Lunch',
    'box lonch': 'Box Lunch',
}


def parse_itinerary(text: str, tour_title: str) -> list[dict]:
    """Parse itinerary text into structured day records for x_itinerary_line."""
    if not text or not text.strip():
        return [{
            'x_sequence': 10,
            'x_day_number': 1,
            'x_title': tour_title,
            'x_description': '',
            'x_accommodation': '',
            'x_meals': '',
        }]

    lines = text.strip().split('\n')
    days = []
    current_day = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Stop if we hit non-itinerary content
        if any(phrase in line.lower() for phrase in STOP_PHRASES):
            break

        match = DAY_HEADER_RE.match(line)
        if match:
            if current_day:
                days.append(current_day)
            day_num = int(match.group(1))
            day_title = match.group(2).strip().rstrip('.')
            current_day = {
                'day_number': day_num,
                'title': day_title or f'Día {day_num}',
                'desc_lines': [],
            }
        elif current_day:
            current_day['desc_lines'].append(line)
        else:
            # No day header yet — accumulate for single-day
            if not current_day:
                current_day = {
                    'day_number': 1,
                    'title': tour_title,
                    'desc_lines': [line],
                }

    if current_day:
        days.append(current_day)

    if not days:
        return [{
            'x_sequence': 10,
            'x_day_number': 1,
            'x_title': tour_title,
            'x_description': text.strip(),
            'x_accommodation': '',
            'x_meals': '',
        }]

    result = []
    for day in days:
        desc = '\n'.join(day['desc_lines']).strip()
        desc_lower = desc.lower()

        # Extract accommodation
        accommodation = ''
        for kw in ACCOMMODATION_KEYWORDS:
            if kw in desc_lower:
                idx = desc_lower.index(kw)
                snippet = desc[max(0, idx):min(len(desc), idx + 80)]
                # Get up to sentence boundary
                for sep in ('.', ',', '\n'):
                    if sep in snippet:
                        snippet = snippet[:snippet.index(sep)]
                        break
                accommodation = snippet.strip()
                break

        # Extract meals
        found_meals = []
        for kw, label in MEAL_MAP.items():
            if kw in desc_lower and label not in found_meals:
                found_meals.append(label)
        meals = ', '.join(found_meals)

        result.append({
            'x_sequence': day['day_number'] * 10,
            'x_day_number': day['day_number'],
            'x_title': day['title'],
            'x_description': desc,
            'x_accommodation': accommodation,
            'x_meals': meals,
        })

    return result


# ── HTML builders ────────────────────────────────────────────────────────

def build_inclusions_html(tour: dict) -> str:
    """Build HTML for x_inclusions from includes/excludes/recommendations."""
    parts = []

    includes = tour.get('includes', [])
    if includes:
        parts.append('<h4>Incluye</h4>')
        parts.append('<ul>')
        for item in includes:
            parts.append(f'  <li>{escape(item)}</li>')
        parts.append('</ul>')

    excludes = tour.get('excludes', [])
    if excludes:
        parts.append('<h4>No Incluye</h4>')
        parts.append('<ul>')
        for item in excludes:
            parts.append(f'  <li>{escape(item)}</li>')
        parts.append('</ul>')

    recs = tour.get('recommendations', [])
    if recs:
        parts.append('<h4>Recomendaciones</h4>')
        parts.append('<ul>')
        for item in recs:
            parts.append(f'  <li>{escape(item)}</li>')
        parts.append('</ul>')

    return '\n'.join(parts)


def build_observations(tour: dict) -> str:
    """Build x_special_observations from conditions + booking + prices."""
    sections = []

    conditions = tour.get('conditions', '').strip()
    if conditions:
        sections.append(f"Condiciones:\n{conditions}")

    booking = tour.get('booking', '').strip()
    if booking:
        sections.append(f"Reservas:\n{booking}")

    prices = tour.get('prices', '').strip()
    if prices:
        sections.append(f"Precios de referencia:\n{prices}")

    return '\n\n'.join(sections)


# ── Odoo helpers ─────────────────────────────────────────────────────────

def find_tour_products(client) -> dict:
    """Get all tour products keyed by lowercase name."""
    products = client.search_read('product.template',
        domain=[['categ_id.name', 'ilike', 'Tours']],
        fields=['id', 'name', 'product_variant_ids'],
        order='name')
    return {p['name'].lower().strip(): p for p in products}


def find_existing_templates(client) -> dict:
    """Get all quotation templates keyed by lowercase name."""
    templates = client.search_read('sale.order.template',
        domain=[],
        fields=['id', 'name', 'x_is_tour'],
        order='name')
    return {t['name'].lower().strip(): t for t in templates}


# ── Main logic ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Create quotation templates with Biblia Operativa from scraped tours")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview changes without writing to Odoo")
    parser.add_argument('--update-only', action='store_true',
                        help="Only update existing templates")
    parser.add_argument('--create-only', action='store_true',
                        help="Only create new templates")
    args = parser.parse_args()

    # Load scraped data
    with open(TOURS_JSON, 'r', encoding='utf-8') as f:
        tours = json.load(f)
    print(f"Loaded {len(tours)} tours from {TOURS_JSON}")

    # Connect
    client = OdooClient()
    client.connect()
    print(f"Connected to Odoo as uid={client.uid}")

    # Fetch existing data
    products = find_tour_products(client)
    templates = find_existing_templates(client)
    print(f"Found {len(products)} tour products, {len(templates)} templates")

    created = 0
    updated = 0
    skipped = 0

    for tour in tours:
        if 'error' in tour:
            print(f"  [SKIP] {tour['slug']}: scrape error")
            skipped += 1
            continue

        title = tour['title']
        title_key = title.lower().strip()

        # ── Find matching product ──
        product = products.get(title_key)
        if not product:
            print(f"  [SKIP] {title}: no matching product in Odoo")
            skipped += 1
            continue

        product_id = product['id']
        variant_ids = product.get('product_variant_ids', [])
        if not variant_ids:
            print(f"  [SKIP] {title}: product has no variants (broken)")
            skipped += 1
            continue
        variant_id = variant_ids[0]

        # ── Parse itinerary ──
        itinerary_lines = parse_itinerary(
            tour.get('itinerary', ''), title)

        # ── Build Biblia fields ──
        inclusions_html = build_inclusions_html(tour)
        key_times = tour.get('schedule', '').strip()
        observations = build_observations(tour)

        # ── Itinerary commands for o2m ──
        itin_commands = []
        for line in itinerary_lines:
            itin_commands.append((0, 0, line))

        # ── Template line (product link) ──
        template_line_cmd = [(0, 0, {
            'product_id': variant_id,
            'product_uom_qty': 1,
        })]

        # ── Check if template exists ──
        existing_tmpl = templates.get(title_key)

        if existing_tmpl:
            # ── UPDATE ──
            if args.create_only:
                print(f"  [SKIP] {title}: exists, --create-only")
                skipped += 1
                continue

            tmpl_id = existing_tmpl['id']
            days_count = len(itinerary_lines)

            if args.dry_run:
                print(f"  [UPDATE] id={tmpl_id} {title} "
                      f"(days={days_count}, inclusions={len(inclusions_html)} chars)")
            else:
                update_vals = {
                    'x_is_tour': True,
                    'x_inclusions': inclusions_html,
                    'x_key_times': key_times,
                    'x_special_observations': observations,
                    # Clear existing itinerary then recreate
                    'x_itinerary_line_ids': [(5, 0, 0)] + itin_commands,
                }
                client.execute('sale.order.template', 'write',
                               [tmpl_id], update_vals)
                print(f"  [UPDATED] id={tmpl_id} {title} ({days_count} days)")
                time.sleep(0.3)

            updated += 1

        else:
            # ── CREATE ──
            if args.update_only:
                print(f"  [SKIP] {title}: new, --update-only")
                skipped += 1
                continue

            days_count = len(itinerary_lines)

            if args.dry_run:
                print(f"  [CREATE] {title} "
                      f"(days={days_count}, product={product_id})")
            else:
                create_vals = {
                    'name': title,
                    'x_is_tour': True,
                    'number_of_days': 15,
                    'x_inclusions': inclusions_html,
                    'x_key_times': key_times,
                    'x_special_observations': observations,
                    'x_itinerary_line_ids': itin_commands,
                    'sale_order_template_line_ids': template_line_cmd,
                }
                result = client.execute(
                    'sale.order.template', 'create', [create_vals])
                new_id = result[0] if isinstance(result, list) else result
                print(f"  [CREATED] id={new_id} {title} ({days_count} days)")
                time.sleep(0.3)

            created += 1

    # Summary
    print(f"\n{'=' * 60}")
    print(f"TEMPLATE MIGRATION{'  (DRY RUN)' if args.dry_run else ''}:")
    print(f"  Created:  {created}")
    print(f"  Updated:  {updated}")
    print(f"  Skipped:  {skipped}")
    print(f"  Total:    {len(tours)}")

    if args.dry_run:
        print("\nRun without --dry-run to apply changes.")


if __name__ == "__main__":
    main()
