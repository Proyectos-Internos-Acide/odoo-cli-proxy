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


def fetch_page(slug: str, max_retries: int = 4) -> BeautifulSoup:
    """Fetch a tour page and return parsed HTML, with retry on 429."""
    url = f"{BASE_URL}/tour/{slug}/"
    for attempt in range(max_retries):
        resp = requests.get(url, headers=HEADERS, timeout=30)
        if resp.status_code == 429:
            wait = 2 ** (attempt + 1)  # 2, 4, 8, 16 seconds
            print(f"429, retrying in {wait}s...", end=" ", flush=True)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return BeautifulSoup(resp.text, 'lxml')
    # Final attempt
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, 'lxml')


def _clean_text(text: str) -> str:
    """Fix common text extraction artefacts from WordPress Elementor."""
    if not text:
        return text
    # Add space after sentence-ending punctuation before uppercase letter
    text = re.sub(r'([.!?%])([A-ZÁÉÍÓÚÑ¿¡])', r'\1 \2', text)
    # Fix schedule: "Domingo08:30" → "Domingo, 08:30"
    text = re.sub(r'([a-záéíóúñ])(\d{1,2}[:.]\d{2})', r'\1, \2', text)
    # Fix concatenated words from stripped inline tags: "famosaPlaza" → "famosa Plaza"
    text = re.sub(r'([a-záéíóúñ])([A-ZÁÉÍÓÚÑ][a-záéíóúñ])', r'\1 \2', text)
    # Fix "USDExtranjero" → "USD Extranjero"
    text = re.sub(r'(USD)([A-ZÁÉÍÓÚÑ])', r'\1 \2', text)
    # Fix "Peruanos$." → "Peruanos $."
    text = re.sub(r'([a-záéíóúños])\s*(\$\.?\s*\d)', r'\1 \2', text)
    # Normalize multiple spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def _extract_text_with_spacing(tag: Tag) -> str:
    """Extract text from a tag ensuring spaces around inline elements."""
    parts = []
    for child in tag.descendants:
        if isinstance(child, str):
            parts.append(child)
        elif isinstance(child, Tag) and child.name in ('br',):
            parts.append('\n')
    text = ''.join(parts)
    # Normalize whitespace within lines but preserve line breaks
    lines = text.split('\n')
    lines = [' '.join(l.split()) for l in lines]
    return '\n'.join(l for l in lines if l.strip())


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
        # Get text preserving paragraph breaks and inline spacing
        paragraphs = []
        for child in widget.children:
            if isinstance(child, Tag):
                text = _extract_text_with_spacing(child)
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
        if 'form' in parent_classes or container.select('form, select'):
            continue  # Skip form widgets (country dropdowns, etc.)
        t = _extract_text_with_spacing(container)
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


# ── Section boundary patterns for splitting bleeding descriptions ──────
_SECTION_BOUNDARIES = [
    # (pattern, target_field, is_prefix)
    # Schedule patterns
    (r'^Lunes a Domingo', 'schedule', True),
    (r'^Diarias?\b', 'schedule', True),
    (r'^De lunes a', 'schedule', True),
    # Conditions patterns
    (r'^Tours? son en servicio', 'conditions', True),
    (r'^El tour es ', 'conditions', True),
    (r'^El tour comienza', 'conditions', True),
    (r'^Servicio compartido', 'conditions', True),
    # Booking patterns
    (r'^Pago al 100%', 'booking', True),
    (r'^Reservar con ', 'booking', True),
    # Prices patterns
    (r'^PRECIO POR PERSONA', 'prices', True),
    (r'^Peruanos \$', 'prices', True),
    (r'^Extranjeros? \$', 'prices', True),
    # Recommendations (sometimes at end of description)
    (r'^\*Recomendamos\b', 'recommendations_text', True),
]


def _split_bleeding_description(tour: dict) -> dict:
    """Split a description that contains schedule/conditions/booking/prices.

    Many WordPress pages have all content in one big section, causing the
    scraper to dump everything into the description field. This function
    detects section boundaries within the description text and moves content
    to the correct fields.
    """
    desc = tour.get('description', '')
    if not desc or len(desc) < 300:
        return tour

    # Split on double newlines (paragraph boundaries)
    paragraphs = [p.strip() for p in desc.split('\n') if p.strip()]

    new_desc_parts = []
    current_field = 'description'

    for para in paragraphs:
        # Check if this paragraph starts a new section
        matched_field = None
        for pattern, field, _ in _SECTION_BOUNDARIES:
            if re.search(pattern, para, re.IGNORECASE):
                matched_field = field
                break

        if matched_field:
            current_field = matched_field

        if current_field == 'description':
            new_desc_parts.append(para)
        else:
            # Only write to field if it's currently empty (don't duplicate
            # content that the section classifier already extracted)
            existing = tour.get(current_field, '')
            if isinstance(existing, list):
                if current_field == 'recommendations_text':
                    tour['recommendations_text'] = (
                        (tour.get('recommendations_text', '') + '\n' + para).strip()
                    )
                continue
            if not existing:
                tour[current_field] = para
            elif current_field in ('conditions', 'booking', 'prices'):
                # These fields may have multiple paragraphs from the split
                # but only append if the existing content is short
                if len(existing) < 50:
                    tour[current_field] = existing + '\n' + para

    tour['description'] = '\n'.join(new_desc_parts)

    # Parse recommendations from text if found in description
    recs_text = tour.pop('recommendations_text', '')
    if recs_text and not tour.get('recommendations'):
        recs = [r.strip().lstrip('*•·-').strip()
                for r in recs_text.split('\n') if r.strip()]
        if recs:
            tour['recommendations'] = recs

    return tour


def _handle_description_overlap(tour: dict) -> dict:
    """Clear description when it substantially overlaps with itinerary."""
    desc = tour.get('description', '').strip()
    itin = tour.get('itinerary', '').strip()
    if not desc or not itin:
        return tour

    # Check if itinerary starts with the description text
    if itin.startswith(desc[:200]):
        tour['description'] = ''
        return tour

    # Check if description starts with the itinerary text
    if desc.startswith(itin[:200]):
        tour['description'] = ''
        return tour

    # Check word overlap ratio
    desc_words = set(desc.lower().split())
    itin_words = set(itin.lower().split())
    if desc_words and len(desc_words) > 10:
        overlap = len(desc_words & itin_words) / len(desc_words)
        if overlap > 0.7:
            tour['description'] = ''

    return tour


def _extract_departure_return(tour: dict) -> dict:
    """Extract departure/return info from schedule, conditions, itinerary."""
    details = tour.get('details', {})
    itin = tour.get('itinerary', '')
    conditions = tour.get('conditions', '')
    schedule = tour.get('schedule', '')

    # ── Departure location ──
    # Nearly all tours pick up from hotel
    if not details.get('departure_location'):
        all_text = (itin + ' ' + conditions).lower()
        if any(kw in all_text for kw in [
            'recojo en su hotel', 'recogeremos en su hotel',
            'recogemos en su hotel', 'recojo del hotel',
            'recojo en el hotel', 'pickup at your hotel',
            'hotel pickup', 'recojo en los hoteles',
        ]):
            details['departure_location'] = 'Hotel'

    # ── Departure time ──
    if not details.get('departure_time'):
        # Try from schedule field first (most reliable)
        if schedule:
            m = re.search(
                r'(\d{1,2}[:.]\d{2})\s*(?:am|hrs|a\.?\s*m\.?|horas)',
                schedule, re.IGNORECASE)
            if m:
                details['departure_time'] = m.group(0).strip()
        # Fallback: first time mention in itinerary
        if not details.get('departure_time') and itin:
            m = re.search(
                r'(?:las?\s+)?(\d{1,2}[:.]\d{2})\s*(?:am|hrs|a\.?\s*m\.?)',
                itin[:300], re.IGNORECASE)
            if m:
                details['departure_time'] = m.group(0).strip()

    # ── Return location ──
    if not details.get('return_location'):
        # Pattern: "el servicio culmina en X"
        m = re.search(
            r'(?:servicio\s+)?(?:culmina|termina|finaliza)\s+en\s+(.+?)(?:\.|$)',
            conditions, re.IGNORECASE)
        if m:
            loc = m.group(1).strip()
            # Clean up: remove parenthetical notes
            loc = re.sub(r'\s*\(.*?\)\s*', ' ', loc).strip()
            if 5 < len(loc) < 80:
                details['return_location'] = loc

    # ── Return time ──
    if not details.get('return_time'):
        if itin:
            # Find the LAST pm time in the itinerary
            matches = re.findall(
                r'(?:a\s+(?:eso\s+de\s+)?las?\s+)?(\d{1,2}[:.]\d{2})\s*'
                r'(?:p\.?\s*m\.?|pm)',
                itin, re.IGNORECASE)
            if matches:
                details['return_time'] = matches[-1].replace('.', ':') + ' p.m.'

    # ── Cleanup ──
    # Strip "las " prefix from times
    for key in ('departure_time', 'return_time'):
        val = details.get(key, '')
        if val:
            val = re.sub(r'^(?:las?\s+)', '', val, flags=re.IGNORECASE).strip()
            details[key] = val

    # Remove invalid values (non-time text like "Consulta este Tour")
    for key in ('departure_time', 'return_time'):
        val = details.get(key, '')
        if val and not re.search(r'\d{1,2}[:.]\d{2}', val):
            del details[key]

    # Normalize return_location: strip trailing punctuation
    loc = details.get('return_location', '')
    if loc:
        details['return_location'] = loc.rstrip('.,;:')

    tour['details'] = details
    return tour


def _fix_duration(tour: dict) -> dict:
    """Fix unreliable duration values from the scraper.

    The scraper matched any "N día" in short sections, often picking up
    wrong values. Infer duration from the slug/title instead.
    """
    slug = tour.get('slug', '')
    title = tour.get('title', '').lower()

    # Multi-day: look for NdNn or N-dias patterns in slug
    m = re.search(r'(\d+)\s*(?:d|dias|días)', slug)
    if m:
        days = int(m.group(1))
        tour['duration'] = f"{days} día(s)"
        return tour

    # Check title for day count
    m = re.search(r'(\d+)\s*(?:d[ií]as?|days?)', title)
    if m:
        days = int(m.group(1))
        tour['duration'] = f"{days} día(s)"
        return tour

    # Single-day tours: no multi-day indicator → "1 día"
    # But only set if there's itinerary content (avoid setting on empty tours)
    if tour.get('itinerary') or tour.get('description'):
        tour['duration'] = '1 día'

    return tour


def _post_process_tour(tour: dict) -> dict:
    """Apply all post-processing steps to a scraped tour."""
    if 'error' in tour:
        return tour

    # 1. Clean all text fields
    for field in ('description', 'itinerary', 'schedule', 'conditions',
                  'booking', 'prices'):
        if tour.get(field):
            tour[field] = _clean_text(tour[field])

    # Clean list items too
    for field in ('includes', 'excludes', 'recommendations'):
        if tour.get(field):
            tour[field] = [_clean_text(item) for item in tour[field]]

    # Clean detail values
    for key, val in tour.get('details', {}).items():
        if isinstance(val, str):
            tour['details'][key] = _clean_text(val)

    # 2. Split bleeding description into proper sections
    _split_bleeding_description(tour)

    # Re-clean after split (new fields may have concatenation issues)
    for field in ('schedule', 'conditions', 'booking', 'prices'):
        if tour.get(field):
            tour[field] = _clean_text(tour[field])

    # 3. Handle description == itinerary overlap
    _handle_description_overlap(tour)

    # 4. Extract departure/return details from text
    _extract_departure_return(tour)

    # 5. Fix duration
    _fix_duration(tour)

    # 6. Strip form HTML / excessively long description fragments
    desc = tour.get('description', '')
    if len(desc) > 3000:
        # Likely contains form HTML or garbage — truncate at first sane boundary
        # Look for first paragraph break within the first 2000 chars
        cut = desc[:2000].rfind('\n')
        if cut > 200:
            tour['description'] = desc[:cut].strip()
        else:
            tour['description'] = desc[:2000].strip()

    return tour


def _merge_existing_translations(new_tours: list, existing_json_path: str) -> list:
    """Merge existing English translations from previous JSON into new data.

    Keeps _en fields from the old JSON where the Spanish source text hasn't
    changed significantly, so we don't lose good translations.
    """
    if not os.path.exists(existing_json_path):
        return new_tours

    with open(existing_json_path, 'r', encoding='utf-8') as f:
        old_tours = json.load(f)

    old_by_slug = {t['slug']: t for t in old_tours if 'error' not in t}

    EN_FIELDS = [
        ('description', 'description_en'),
        ('itinerary', 'itinerary_en'),
        ('schedule', 'schedule_en'),
        ('conditions', 'conditions_en'),
        ('booking', 'booking_en'),
        ('prices', 'prices_en'),
        ('difficulty', 'difficulty_en'),
    ]
    EN_LIST_FIELDS = [
        ('includes', 'includes_en'),
        ('excludes', 'excludes_en'),
        ('recommendations', 'recommendations_en'),
    ]

    for tour in new_tours:
        if 'error' in tour:
            continue
        old = old_by_slug.get(tour['slug'])
        if not old:
            continue

        # Merge string fields
        for es_key, en_key in EN_FIELDS:
            old_es = old.get(es_key, '').strip()
            new_es = tour.get(es_key, '').strip()
            old_en = old.get(en_key, '')

            if not old_en:
                continue

            # If Spanish text is similar enough, keep the English translation
            if old_es and new_es:
                # Simple similarity: check if they share >60% of words
                old_words = set(old_es.lower().split())
                new_words = set(new_es.lower().split())
                if old_words:
                    similarity = len(old_words & new_words) / max(len(old_words), 1)
                    if similarity > 0.6:
                        tour[en_key] = old_en
                    else:
                        # Text changed significantly — mark for re-translation
                        tour[en_key] = old_en  # Keep old but flag
                        tour[f'_{en_key}_needs_review'] = True
                else:
                    tour[en_key] = old_en
            elif not new_es and old_en:
                # Spanish was cleared (e.g. overlap removal) — drop EN too
                pass
            else:
                tour[en_key] = old_en

        # Merge list fields
        for es_key, en_key in EN_LIST_FIELDS:
            old_es = old.get(es_key, [])
            new_es = tour.get(es_key, [])
            old_en = old.get(en_key, [])

            if not old_en:
                continue

            # If lists are same length and similar content, keep EN
            if len(old_es) == len(new_es) == len(old_en):
                tour[en_key] = old_en
            elif len(new_es) == len(old_en):
                tour[en_key] = old_en
            else:
                # Length mismatch — keep old but flag
                tour[en_key] = old_en
                tour[f'_{en_key}_needs_review'] = True

        # Merge detail translations
        old_details_en = old.get('details_en', {})
        if old_details_en:
            tour.setdefault('details_en', {}).update(old_details_en)

    return new_tours


def scrape_all_tours() -> list:
    """Scrape all WordPress tours and return structured data."""
    tours = []
    total = len(TOUR_SLUGS)

    for i, slug in enumerate(TOUR_SLUGS, 1):
        print(f"[{i}/{total}] Scraping: {slug}...", end=" ", flush=True)
        try:
            soup = fetch_page(slug)
            tour_data = extract_tour_data(soup, slug)

            # Apply post-processing
            tour_data = _post_process_tour(tour_data)

            has_content = bool(
                tour_data["description"] or tour_data["itinerary"]
                or tour_data["includes"]
            )
            status = "OK" if has_content else "MINIMAL"
            details = tour_data.get('details', {})
            detail_keys = [k for k in details if details[k]]
            print(f"{status} - {tour_data['title']}"
                  f" (details: {detail_keys or 'none'})")

            tours.append(tour_data)
            time.sleep(3.0)  # Be gentle with the server

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

    # Merge existing English translations
    output_dir = Path(__file__).parent / "generated"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "wordpress_tours.json"

    # Safety: don't overwrite if all tours failed
    error_count = sum(1 for t in tours if 'error' in t)
    if error_count == len(tours):
        print(f"\n[ABORT] All {len(tours)} tours failed — NOT overwriting JSON")
        return
    if error_count > len(tours) * 0.5:
        print(f"\n[WARN] {error_count}/{len(tours)} tours failed — NOT overwriting JSON")
        return

    print(f"\nMerging English translations from existing JSON...")
    tours = _merge_existing_translations(tours, str(output_file))

    # Count merged translations
    n_en = sum(1 for t in tours if t.get('description_en'))
    n_review = sum(1 for t in tours
                   if any(t.get(f'_{k}_needs_review')
                          for k in ('description_en', 'itinerary_en',
                                    'conditions_en', 'booking_en',
                                    'prices_en', 'includes_en',
                                    'excludes_en', 'recommendations_en')))
    print(f"  Merged EN translations: {n_en} tours")
    if n_review:
        print(f"  Flagged for review: {n_review} tours (text changed)")

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

    # Count details
    n_details = sum(1 for t in ok_tours
                    if any(t.get('details', {}).get(k)
                           for k in ('departure_location', 'return_location',
                                     'departure_time', 'return_time')))

    print(f"\n{'=' * 60}")
    print(f"RESULTS:")
    print(f"  Total:          {len(tours)}")
    print(f"  With content:   {len(ok_tours)}")
    print(f"  With details:   {n_details}")
    print(f"  Minimal:        {len(minimal_tours)}")
    print(f"  Errors:         {len(error_tours)}")
    print(f"\nSaved to: {output_file}")

    for t in ok_tours:
        inc = len(t.get('includes', []))
        details = t.get('details', {})
        d_keys = ', '.join(k for k in ('departure_location', 'departure_time',
                                        'return_location', 'return_time')
                           if details.get(k))
        desc_len = len(t.get('description', ''))
        itin_len = len(t.get('itinerary', ''))
        print(f"  [OK] {t['title']}: inc={inc}, desc={desc_len}ch, "
              f"itin={itin_len}ch, details=[{d_keys}]")

    for t in minimal_tours:
        print(f"  [--] {t['slug']}: title={t.get('title', 'N/A')}")


def reprocess():
    """Re-apply post-processing to existing JSON without re-scraping."""
    output_dir = Path(__file__).parent / "generated"
    output_file = output_dir / "wordpress_tours.json"

    if not output_file.exists():
        print(f"[ERROR] {output_file} not found")
        return

    print("=" * 60)
    print("Re-processing existing wordpress_tours.json")
    print("=" * 60)

    with open(output_file, 'r', encoding='utf-8') as f:
        tours = json.load(f)

    # Strip existing _en fields before re-processing (they'll be re-merged)
    en_backup = {}
    for t in tours:
        if 'error' in t:
            continue
        slug = t['slug']
        en_backup[slug] = {}
        for key in list(t.keys()):
            if key.endswith('_en') or key == 'details_en':
                en_backup[slug][key] = t.pop(key)

    print(f"\nPost-processing {len(tours)} tours...\n")
    for tour in tours:
        if 'error' in tour:
            continue
        _post_process_tour(tour)
        slug = tour['slug']
        details = tour.get('details', {})
        d_keys = [k for k in details if details[k]]
        desc_len = len(tour.get('description', ''))
        itin_len = len(tour.get('itinerary', ''))
        print(f"  {tour['title']}: desc={desc_len}ch, itin={itin_len}ch, "
              f"details={d_keys}")

    # Restore EN translations
    for tour in tours:
        if 'error' in tour:
            continue
        en = en_backup.get(tour['slug'], {})
        for key, val in en.items():
            tour[key] = val

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tours, f, ensure_ascii=False, indent=2)

    # Summary
    n_details = sum(1 for t in tours if 'error' not in t and
                    any(t.get('details', {}).get(k)
                        for k in ('departure_location', 'return_location',
                                  'departure_time', 'return_time')))
    n_empty_desc = sum(1 for t in tours if 'error' not in t
                       and not t.get('description'))
    print(f"\n{'=' * 60}")
    print(f"  Tours with details: {n_details}/{len(tours)}")
    print(f"  Tours with empty description (overlap cleared): {n_empty_desc}")
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    import sys
    if '--reprocess' in sys.argv:
        reprocess()
    else:
        main()
