#!/usr/bin/env python3
"""
Scrape tour content from the old WordPress site (machupicchuafdestiny.com)
and save structured data to JSON for later upload to Odoo.

Strategy: Use elementor-section[data-id] as the primary content unit.
Each section's first text is matched against known headings to identify
the section type, then content is extracted accordingly.

Usage:
    python business_units/hotel-trip-agency/agency/scrape_wordpress_tours.py

Output:
    business_units/hotel-trip-agency/agency/generated/wordpress_tours.json
"""
import json
import os
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://machupicchuafdestiny.com"

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-419,es;q=0.9,en;q=0.8',
}

# Tour slugs from the product-sitemap.xml (only actual tours, no food/drink)
TOUR_SLUGS = [
    "chinchero-maras-moray",
    "city-tour-cusco",
    "circuito-sur",
    "laguna-de-humantay",
    "combinada",
    "palcoyo",
    "valle-sagrado-vip",
    "valle-sagrado-tradicional",
    "walking-tour-cusco",
    "montana-de-7-colores",
    "machupicchu",
    "machu-picchu-by-car-2d-1n",
    "valle-sagrado-conexion-a-machu-picchu",
    "camino-inka-a-machupicchu-2-dias-1-noche",
    "camino-inka-a-machupicchu-4-dias-3-noches",
    "lares-trek-machu-picchu-4-dias-y-3-noches",
    "salkantay-trek-machupicchu-4-dias-3-noches",
    "salkantay-trek-machupicchu-5-dias-4-noches",
    "choquequirao-4-dias-3-noches",
    "queswachca-4-lagunas",
    "los-farallones-de-tecsecocha",
    "waqrapucara",
    "tradicional-cusco-3-d-2-n",
    "cusco-magico-4-dias-3-noches",
    "cusco-tradicional-5-dias-4-noches",
    "ruta-del-sol-cusco-a-puno",
    "pago-a-la-tierra-lectura-hojas-de-coca-ceremonia-andina",
    "puno-01-dia-isla-uros-taquile",
]

# Patterns to identify sections by their text content
SECTION_PATTERNS = [
    (r"detalles del tour", "details_header"),
    (r"qué incluye", "includes"),
    (r"qué no incluye", "excludes"),
    (r"recomendamos llevar", "recommendations"),
    (r"itinerario del tour", "itinerary_header"),
    (r"itinerario", "itinerary_header"),
    (r"salidas", "schedule"),
    (r"condiciones", "conditions"),
    (r"reservas", "booking"),
    (r"precios", "prices"),
    (r"reseñas", "reviews"),
    (r"explora mas tours", "_stop"),
    (r"por que reservar", "_stop"),
    (r"precio por persona", "_sidebar"),
    (r"formulario de reserva", "_sidebar"),
    (r"metodos de pago", "_stop"),
    (r"enlaces rapidos", "_stop"),
]


def fetch_page(slug: str) -> BeautifulSoup:
    """Fetch a tour page and return parsed HTML."""
    url = f"{BASE_URL}/tour/{slug}/"
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'lxml')


def _classify_section(text: str) -> str | None:
    """Match section text against known heading patterns."""
    text_lower = text.lower().strip()
    for pattern, section_type in SECTION_PATTERNS:
        if re.search(pattern, text_lower):
            return section_type
    return None


def _extract_list_items(section: Tag) -> list[str]:
    """Extract list items from icon-list widgets or <li> elements."""
    items = []
    # Try icon-list first
    for li in section.select('.elementor-icon-list-text'):
        text = li.get_text(strip=True)
        if text and len(text) > 2:
            items.append(text)
    # Also check regular <li> elements
    if not items:
        for li in section.select('li'):
            text = li.get_text(strip=True)
            if text and len(text) > 2:
                items.append(text)
    return items


def _extract_text_content(section: Tag) -> str:
    """Extract text content from text-editor widgets in a section."""
    texts = []
    for widget in section.select('.elementor-widget-text-editor .elementor-widget-container'):
        # Get text preserving paragraph breaks
        paragraphs = []
        for child in widget.children:
            if isinstance(child, Tag):
                text = child.get_text(strip=True)
                if text:
                    paragraphs.append(text)
            elif isinstance(child, str) and child.strip():
                paragraphs.append(child.strip())
        if paragraphs:
            texts.append('\n'.join(paragraphs))

    return '\n\n'.join(texts) if texts else ""


def _extract_text_from_eael_widgets(section: Tag) -> str:
    """Extract text from Essential Addons widgets (eael_liquid_glass etc.)."""
    texts = []
    for widget in section.select('[class*="eael_liquid_glass"] .elementor-widget-container'):
        text = widget.get_text(strip=True, separator='\n')
        if text and len(text) > 3:
            texts.append(text)
    return '\n'.join(texts) if texts else ""


def _extract_items_from_section(section: Tag) -> list[str]:
    """Extract list items from various widget types in a section."""
    items = _extract_list_items(section)
    if items:
        return items

    # Fallback: try to extract from eael widgets with list-like content
    for widget in section.select('[class*="eael_liquid_glass"] .elementor-widget-container'):
        for li in widget.select('li'):
            text = li.get_text(strip=True)
            if text and len(text) > 2 and text not in items:
                items.append(text)
        # If no <li>, try splitting by lines/bullets
        if not items:
            text = widget.get_text(separator='\n', strip=True)
            for line in text.split('\n'):
                line = line.strip().strip('•·–-').strip()
                if line and len(line) > 2:
                    items.append(line)

    return items


def _get_section_all_text(section: Tag) -> str:
    """Get ALL text content from a section, combining all widget types."""
    # Try text-editor widgets first
    text = _extract_text_content(section)
    if text:
        return text

    # Then try eael widgets
    text = _extract_text_from_eael_widgets(section)
    if text:
        return text

    # Fallback: extract from any .elementor-widget-container that has text
    # but skip heading/icon-list widgets (they are labels, not content)
    texts = []
    for container in section.select('.elementor-widget-container'):
        parent = container.parent
        parent_classes = ' '.join(parent.get('class', []))
        if 'heading' in parent_classes or 'icon-list' in parent_classes:
            continue
        if 'star-rating' in parent_classes or 'nav-menu' in parent_classes:
            continue
        t = container.get_text(strip=True, separator='\n')
        if t and len(t) > 3:
            texts.append(t)

    return '\n'.join(texts) if texts else ""


def extract_tour_data(soup: BeautifulSoup, slug: str) -> dict:
    """Extract structured tour data from a parsed Elementor page."""
    data = {
        "slug": slug,
        "url": f"{BASE_URL}/tour/{slug}/",
        "title": "",
        "price_pen": "",
        "description": "",
        "details": {},
        "includes": [],
        "excludes": [],
        "recommendations": [],
        "itinerary": "",
        "schedule": "",
        "conditions": "",
        "booking": "",
        "prices": "",
        "images": [],
        "duration": "",
        "difficulty": "",
    }

    # ── Title: from the product template's heading ──
    product_tmpl = soup.select_one('[data-elementor-type="product"]')
    if product_tmpl:
        title_el = product_tmpl.select_one('.elementor-heading-title')
        if title_el:
            data["title"] = title_el.get_text(strip=True)

    # If no title from product template, try the page <title>
    if not data["title"]:
        title_tag = soup.select_one('title')
        if title_tag:
            raw = title_tag.get_text(strip=True)
            # Remove site name suffix
            data["title"] = raw.split(' - ')[0].split(' – ')[0].strip()

    # ── Price from product template ──
    if product_tmpl:
        for el in product_tmpl.select('.woocommerce-Price-amount, .elementor-icon-list-text'):
            text = el.get_text(strip=True)
            price_match = re.search(r'S/\s*[\d,]+(?:\.\d{2})?', text)
            if price_match:
                data["price_pen"] = price_match.group(0)
                break

    # ── Process content sections ──
    # Get all top-level sections from the section templates
    all_sections = soup.select('.elementor-section[data-id]')

    # Track content state
    current_content_type = None
    detail_labels = {
        "lugar de salida": "departure_location",
        "lugar de retorno": "return_location",
        "hora de salida": "departure_time",
        "hora de retorno": "return_time",
    }
    pending_detail_label = None

    for section in all_sections:
        section_text = section.get_text(strip=True, separator=' | ')
        if not section_text or len(section_text) < 4:
            continue

        # Try to classify this section
        classification = _classify_section(section_text)

        if classification == "_stop":
            break
        if classification == "_sidebar":
            continue
        if classification == "reviews":
            continue

        # Check if this is a detail label (Lugar de Salida, etc.)
        text_lower = section_text.lower().strip()
        detail_key = None
        for label, key in detail_labels.items():
            if label in text_lower and len(section_text) < 40:
                detail_key = key
                break

        if detail_key:
            pending_detail_label = detail_key
            continue

        # If we have a pending detail label, this section has the value
        if pending_detail_label and not classification:
            value = section_text.strip()
            if len(value) < 100:  # Sanity check
                data["details"][pending_detail_label] = value
                pending_detail_label = None
                continue
            pending_detail_label = None

        # Section classification handling
        if classification == "details_header":
            # The description text is usually in the same section
            desc = _get_section_all_text(section)
            if desc:
                data["description"] = desc
            current_content_type = "details"
            continue

        if classification == "includes":
            items = _extract_items_from_section(section)
            if items:
                data["includes"] = items
            else:
                # Content might be in the next non-heading text
                text = _get_section_all_text(section)
                if text:
                    data["includes"] = [
                        line.strip() for line in text.split('\n')
                        if line.strip() and len(line.strip()) > 2
                    ]
            continue

        if classification == "excludes":
            items = _extract_items_from_section(section)
            if items:
                data["excludes"] = items
            else:
                text = _get_section_all_text(section)
                if text:
                    data["excludes"] = [
                        line.strip() for line in text.split('\n')
                        if line.strip() and len(line.strip()) > 2
                    ]
            continue

        if classification == "recommendations":
            items = _extract_items_from_section(section)
            if items:
                data["recommendations"] = items
            else:
                text = _get_section_all_text(section)
                if text:
                    data["recommendations"] = [
                        line.strip() for line in text.split('\n')
                        if line.strip() and len(line.strip()) > 2
                    ]
            continue

        if classification == "itinerary_header":
            text = _get_section_all_text(section)
            if text:
                data["itinerary"] = text
            continue

        if classification == "schedule":
            text = _get_section_all_text(section)
            if text:
                data["schedule"] = text
            continue

        if classification == "conditions":
            text = _get_section_all_text(section)
            if text:
                data["conditions"] = text
            continue

        if classification == "booking":
            text = _get_section_all_text(section)
            if text:
                data["booking"] = text
            continue

        if classification == "prices":
            text = _get_section_all_text(section)
            if text:
                data["prices"] = text
            continue

        # Unclassified section: if we're in details context and this has
        # long text, it might be part of the description
        if current_content_type == "details" and not classification:
            text = _get_section_all_text(section)
            if text and len(text) > 20:
                if data["description"]:
                    data["description"] += "\n\n" + text
                else:
                    data["description"] = text

    # ── Images (from the full page, excluding logos/icons) ──
    exclude_patterns = ['logo', 'LOGO', 'cropped', 'espana.png', 'estados-unidos',
                        'IZIPAY', 'qrcode', 'cusco-apues', 'blanco-01',
                        'MACHU-PICCHU-AF-DESTINY', 'favicon', 'icon']
    seen_srcs = set()

    for img in soup.select('img'):
        src = img.get('src', '') or img.get('data-src', '')
        if not src or 'wp-content/uploads' not in src:
            continue
        if any(p in src for p in exclude_patterns):
            continue
        if src in seen_srcs:
            continue

        seen_srcs.add(src)
        # Get full-size URL (remove Elementor thumbnail suffix)
        full_src = re.sub(r'-\d+x\d+\.', '.', src)
        data["images"].append(full_src)

    # Also check for background images in style attributes
    for el in soup.select('[data-bg], [style*="background-image"]'):
        bg = el.get('data-bg', '')
        if not bg:
            style = el.get('style', '')
            bg_match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
            if bg_match:
                bg = bg_match.group(1)
        if bg and 'wp-content/uploads' in bg:
            if not any(p in bg for p in exclude_patterns) and bg not in seen_srcs:
                seen_srcs.add(bg)
                data["images"].append(bg)

    # ── Duration & difficulty ──
    # Try to extract from sidebar or section metadata
    for section in all_sections:
        text = section.get_text(strip=True)
        if not data["duration"]:
            dur_match = re.search(r'(\d+)\s*[Dd]ía', text)
            if dur_match and len(text) < 30:
                data["duration"] = f"{dur_match.group(1)} día(s)"
        if not data["difficulty"]:
            for diff in ('Fácil', 'Moderado', 'Difícil', 'Desafiante'):
                if diff in text and len(text) < 30:
                    data["difficulty"] = diff
                    break

    # Clean up: remove headings from includes/excludes that leaked in
    heading_texts = {"¿Qué Incluye?", "¿Qué NO incluye?", "Recomendamos llevar",
                     "Detalles del Tour", "Itinerario del Tour"}
    data["includes"] = [i for i in data["includes"] if i not in heading_texts]
    data["excludes"] = [i for i in data["excludes"] if i not in heading_texts]
    data["recommendations"] = [i for i in data["recommendations"] if i not in heading_texts]

    return data


def scrape_all_tours() -> list:
    """Scrape all WordPress tours and return structured data."""
    tours = []
    total = len(TOUR_SLUGS)

    for i, slug in enumerate(TOUR_SLUGS, 1):
        print(f"[{i}/{total}] Scraping: {slug}...", end=" ", flush=True)
        try:
            soup = fetch_page(slug)
            tour_data = extract_tour_data(soup, slug)

            has_content = bool(
                tour_data["description"] or tour_data["itinerary"]
                or tour_data["includes"]
            )
            status = "OK" if has_content else "MINIMAL"
            print(f"{status} - {tour_data['title']}")

            tours.append(tour_data)
            time.sleep(0.8)

        except requests.RequestException as e:
            print(f"ERROR: {e}")
            tours.append({
                "slug": slug,
                "url": f"{BASE_URL}/tour/{slug}/",
                "error": str(e),
            })

    return tours


def main():
    print("=" * 60)
    print("WordPress Tour Scraper - machupicchuafdestiny.com")
    print("=" * 60)
    print(f"\nScraping {len(TOUR_SLUGS)} tours...\n")

    tours = scrape_all_tours()

    # Save to JSON
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "wordpress_tours.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tours, f, ensure_ascii=False, indent=2)

    # Summary
    ok_tours = [t for t in tours if 'error' not in t and (
        t.get('description') or t.get('itinerary') or t.get('includes')
    )]
    minimal_tours = [t for t in tours if 'error' not in t and not (
        t.get('description') or t.get('itinerary') or t.get('includes')
    )]
    error_tours = [t for t in tours if 'error' in t]

    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  Total:        {len(tours)}")
    print(f"  With content: {len(ok_tours)}")
    print(f"  Minimal:      {len(minimal_tours)}")
    print(f"  Errors:       {len(error_tours)}")
    print(f"\nSaved to: {output_file}")

    for t in ok_tours:
        inc = len(t.get('includes', []))
        imgs = len(t.get('images', []))
        print(f"  [OK] {t['title']}: includes={inc}, images={imgs}, "
              f"price={t.get('price_pen', 'N/A')}")

    for t in minimal_tours:
        print(f"  [--] {t['slug']}: title={t.get('title', 'N/A')}")


if __name__ == "__main__":
    main()
