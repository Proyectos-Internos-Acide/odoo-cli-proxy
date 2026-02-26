#!/usr/bin/env python3
"""Setup extended description field and QWeb view for tour products.

Creates:
  1. x_extended_description (html) field on product.template
  2. QWeb inherited view rendering the field below product image, above specifications
  3. Migrates existing tour products: moves long content from description_ecommerce
     to x_extended_description, replaces description_ecommerce with short description

Usage:
    # Full setup: field + view + migration
    uv run python business_units/hotel-trip-agency/agency/setup_extended_description.py

    # Preview migration without applying
    uv run python business_units/hotel-trip-agency/agency/setup_extended_description.py --dry-run

    # Only create field + view (no data migration)
    uv run python business_units/hotel-trip-agency/agency/setup_extended_description.py --no-migrate
"""
import argparse
import json
import sys
import os
import time
from html import escape
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from odoo_cli import OdooClient
from agency.defaults.views import ECOM_EXTENDED_DESC_ARCH, PRODUCT_EXTENDED_DESC_FORM_ARCH

TOURS_JSON = Path(__file__).parent / "generated" / "wordpress_tours.json"


# ── HTML builders ────────────────────────────────────────────────────────

import re

# Patterns for detecting day headers in multi-day tours
_DAY_RE = re.compile(
    r'^(?:D[ií]a|DIA|Day)\s*0?(\d+)\s*[:.\-–—]\s*(.*)',
    re.IGNORECASE,
)
# Patterns for splitting single-day itineraries into steps
_SPLIT_RE = re.compile(
    r'(?<=[.!])\s*(?='                      # after sentence end, before:
    r'(?:\d{1,2}[:.]\d{2})'                 #   time like 9:00, 08.30
    # Spanish transition words
    r'|(?:[Ll]uego\b)'                      #   "luego"
    r'|(?:[Dd]espu[eé]s\b)'                 #   "después"
    r'|(?:[Pp]osteriormente\b)'             #   "posteriormente"
    r'|(?:[Ss]eguiremos\b)'                 #   "seguiremos"
    r'|(?:[Ff]inalmente\b)'                 #   "finalmente"
    r'|(?:[Tt]erminando\b)'                 #   "terminando"
    r'|(?:[Aa]l\s+(?:llegar|terminar)\b)'   #   "al llegar/terminar"
    r'|(?:[Nn]uestro\s+(?:primer|segundo|siguiente)\b)'  # "nuestro primer..."
    # English transition words
    r'|(?:[Tt]hen\b)'                       #   "Then"
    r'|(?:[Aa]fter(?:wards?)?\b)'           #   "After/Afterwards"
    r'|(?:[Nn]ext\b)'                       #   "Next"
    r'|(?:[Ff]inally\b)'                    #   "Finally"
    r'|(?:[Ww]e\s+(?:will|continue)\b)'     #   "We will/continue"
    r'|(?:[Ff]rom\s+there\b)'              #   "From there"
    r')',
)


def _extract_intro(text: str, max_chars: int = 350) -> str:
    """Extract a short intro from text, cutting at sentence boundaries.

    Skips day headers (Day 1:, DÍA 1:, etc.) and time-heavy lines.
    Returns at most max_chars, ending at a sentence boundary.
    """
    lines = text.split('\n')
    intro_lines = []
    found_day_header = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if _DAY_RE.match(line):
            if not intro_lines:
                # Description starts with a day header — skip it and take
                # the content of Day 1 instead
                found_day_header = True
                continue
            else:
                break
        # Skip lines that start with a time marker (e.g., "06:40 HRS")
        if re.match(r'^\d{1,2}[:.]\d{2}\s', line) and not intro_lines:
            continue
        intro_lines.append(line)
        # If we entered from a day header, only grab the first content block
        if found_day_header and len(' '.join(intro_lines)) > 120:
            break

    intro = ' '.join(intro_lines).strip()
    if not intro:
        # Fallback: take the raw text, skipping any leading headers
        raw = ' '.join(text.split())
        # Remove leading "Day N:" patterns
        intro = _DAY_RE.sub('', raw).strip()
        if not intro:
            intro = raw

    # Cut at sentence boundary within max_chars
    if len(intro) <= max_chars:
        return intro

    # Find last sentence end within limit
    truncated = intro[:max_chars]
    last_period = max(truncated.rfind('. '), truncated.rfind('.\n'))
    if last_period > 80:  # at least one meaningful sentence
        return truncated[:last_period + 1]

    # Fallback: cut at last space and add ellipsis
    last_space = truncated.rfind(' ')
    if last_space > 80:
        return truncated[:last_space] + '...'
    return truncated + '...'


def _split_single_day_itinerary(text: str) -> list[str]:
    """Split a single-day itinerary paragraph into readable steps."""
    # First split by our regex (sentence boundaries before time/transition words)
    parts = _SPLIT_RE.split(text)
    steps = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Further split on sentence boundaries if the chunk is still very long
        if len(part) > 400:
            sentences = re.split(r'(?<=[.!])\s+', part)
            steps.extend(s.strip() for s in sentences if s.strip())
        else:
            steps.append(part)
    return steps


def _format_multiday_itinerary(text: str) -> str:
    """Format a multi-day itinerary with day headers and bullet-pointed steps."""
    lines = text.split('\n')
    parts = []
    current_day = None
    current_content = []

    def flush_day():
        if current_day and current_content:
            content = ' '.join(current_content).strip()
            parts.append(f"<h4>{escape(current_day)}</h4>")
            steps = _split_single_day_itinerary(content)
            if len(steps) > 1:
                parts.append("<ul>")
                for step in steps:
                    parts.append(f"  <li>{escape(step)}</li>")
                parts.append("</ul>")
            else:
                parts.append(f"<p>{escape(content)}</p>")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = _DAY_RE.match(line)
        if m:
            flush_day()
            day_num = m.group(1)
            day_title = m.group(2).strip() or ''
            current_day = f"Día {day_num}" + (f": {day_title}" if day_title else '')
            current_content = []
        else:
            current_content.append(line)

    flush_day()
    return '\n'.join(parts)


def build_short_description_html(tour: dict) -> str:
    """Build concise HTML for description_ecommerce (shown next to product image).

    Max ~350 chars: attractive intro + schedule + difficulty.
    """
    parts = []

    desc = tour.get("description", "").strip()
    if desc:
        intro = _extract_intro(desc)
        parts.append(f"<p>{escape(intro)}</p>")

    schedule = tour.get("schedule", "").strip()
    if schedule:
        parts.append(f"<p><strong>Salidas:</strong> {escape(schedule)}</p>")

    difficulty = tour.get("difficulty", "").strip()
    if difficulty:
        parts.append(f"<p><strong>Dificultad:</strong> {escape(difficulty)}</p>")

    return "\n".join(parts)


def build_extended_description_html(tour: dict) -> str:
    """Build detailed HTML for x_extended_description (below image, above specs).

    Itinerary formatted as bullet points per day/step.
    """
    parts = []

    # Itinerary
    itinerary = tour.get("itinerary", "").strip()
    if itinerary:
        parts.append("<h3>Itinerario</h3>")
        is_multiday = bool(_DAY_RE.search(itinerary))
        if is_multiday:
            parts.append(_format_multiday_itinerary(itinerary))
        else:
            # Single-day: split into steps
            steps = _split_single_day_itinerary(itinerary)
            if len(steps) > 1:
                parts.append("<ul>")
                for step in steps:
                    parts.append(f"  <li>{escape(step)}</li>")
                parts.append("</ul>")
            elif steps:
                parts.append(f"<p>{escape(steps[0])}</p>")

    # Includes
    includes = tour.get("includes", [])
    if includes:
        parts.append("<h3>¿Qué incluye?</h3>")
        parts.append("<ul>")
        for item in includes:
            parts.append(f"  <li>{escape(item)}</li>")
        parts.append("</ul>")

    # Excludes
    excludes = tour.get("excludes", [])
    if excludes:
        parts.append("<h3>¿Qué NO incluye?</h3>")
        parts.append("<ul>")
        for item in excludes:
            parts.append(f"  <li>{escape(item)}</li>")
        parts.append("</ul>")

    # Recommendations
    recs = tour.get("recommendations", [])
    if recs:
        parts.append("<h3>Recomendamos llevar</h3>")
        parts.append("<ul>")
        for item in recs:
            parts.append(f"  <li>{escape(item)}</li>")
        parts.append("</ul>")

    # Prices
    prices = tour.get("prices", "").strip()
    if prices:
        parts.append("<h3>Precios</h3>")
        for line in prices.split('\n'):
            line = line.strip()
            if line:
                parts.append(f"<p>{escape(line)}</p>")

    # Conditions
    conditions = tour.get("conditions", "").strip()
    if conditions:
        parts.append("<h3>Condiciones</h3>")
        parts.append("<ul>")
        for sentence in re.split(r'(?<=[.!])\s*', conditions):
            sentence = sentence.strip()
            if sentence:
                parts.append(f"  <li>{escape(sentence)}</li>")
        parts.append("</ul>")

    # Booking
    booking = tour.get("booking", "").strip()
    if booking:
        parts.append("<h3>Reservas</h3>")
        parts.append("<ul>")
        for sentence in re.split(r'(?<=[.!])\s*', booking):
            sentence = sentence.strip()
            if sentence:
                parts.append(f"  <li>{escape(sentence)}</li>")
        parts.append("</ul>")

    return "\n".join(parts)


# ── English HTML builders ────────────────────────────────────────────────
# Mirror the Spanish builders but with English headers/labels.
# The body content (tour descriptions, itinerary text) stays in the original
# language — use tour.get("xxx_en") keys when available in JSON.

def _format_multiday_itinerary_en(text: str) -> str:
    """Format multi-day itinerary with English day headers."""
    lines = text.split('\n')
    parts = []
    current_day = None
    current_content = []

    def flush_day():
        if current_day and current_content:
            content = ' '.join(current_content).strip()
            parts.append(f"<h4>{escape(current_day)}</h4>")
            steps = _split_single_day_itinerary(content)
            if len(steps) > 1:
                parts.append("<ul>")
                for step in steps:
                    parts.append(f"  <li>{escape(step)}</li>")
                parts.append("</ul>")
            else:
                parts.append(f"<p>{escape(content)}</p>")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = _DAY_RE.match(line)
        if m:
            flush_day()
            day_num = m.group(1)
            day_title = m.group(2).strip() or ''
            current_day = f"Day {day_num}" + (f": {day_title}" if day_title else '')
            current_content = []
        else:
            current_content.append(line)

    flush_day()
    return '\n'.join(parts)


def build_short_description_html_en(tour: dict) -> str:
    """Build English HTML for description_ecommerce."""
    parts = []

    # Use English description if available, otherwise Spanish
    desc = tour.get("description_en", tour.get("description", "")).strip()
    if desc:
        intro = _extract_intro(desc)
        parts.append(f"<p>{escape(intro)}</p>")

    schedule = tour.get("schedule_en", tour.get("schedule", "")).strip()
    if schedule:
        parts.append(f"<p><strong>Departures:</strong> {escape(schedule)}</p>")

    difficulty = tour.get("difficulty_en", tour.get("difficulty", "")).strip()
    if difficulty:
        parts.append(f"<p><strong>Difficulty:</strong> {escape(difficulty)}</p>")

    return "\n".join(parts)


def build_extended_description_html_en(tour: dict) -> str:
    """Build English HTML for x_extended_description."""
    parts = []

    # Itinerary
    itinerary = tour.get("itinerary_en", tour.get("itinerary", "")).strip()
    if itinerary:
        parts.append("<h3>Itinerary</h3>")
        is_multiday = bool(_DAY_RE.search(itinerary))
        if is_multiday:
            parts.append(_format_multiday_itinerary_en(itinerary))
        else:
            steps = _split_single_day_itinerary(itinerary)
            if len(steps) > 1:
                parts.append("<ul>")
                for step in steps:
                    parts.append(f"  <li>{escape(step)}</li>")
                parts.append("</ul>")
            elif steps:
                parts.append(f"<p>{escape(steps[0])}</p>")

    # Includes
    includes = tour.get("includes_en", tour.get("includes", []))
    if includes:
        parts.append("<h3>What's included?</h3>")
        parts.append("<ul>")
        for item in includes:
            parts.append(f"  <li>{escape(item)}</li>")
        parts.append("</ul>")

    # Excludes
    excludes = tour.get("excludes_en", tour.get("excludes", []))
    if excludes:
        parts.append("<h3>What's NOT included?</h3>")
        parts.append("<ul>")
        for item in excludes:
            parts.append(f"  <li>{escape(item)}</li>")
        parts.append("</ul>")

    # Recommendations
    recs = tour.get("recommendations_en", tour.get("recommendations", []))
    if recs:
        parts.append("<h3>We recommend bringing</h3>")
        parts.append("<ul>")
        for item in recs:
            parts.append(f"  <li>{escape(item)}</li>")
        parts.append("</ul>")

    # Prices
    prices = tour.get("prices_en", tour.get("prices", "")).strip()
    if prices:
        parts.append("<h3>Prices</h3>")
        for line in prices.split('\n'):
            line = line.strip()
            if line:
                parts.append(f"<p>{escape(line)}</p>")

    # Conditions
    conditions = tour.get("conditions_en", tour.get("conditions", "")).strip()
    if conditions:
        parts.append("<h3>Terms &amp; Conditions</h3>")
        parts.append("<ul>")
        for sentence in re.split(r'(?<=[.!])\s*', conditions):
            sentence = sentence.strip()
            if sentence:
                parts.append(f"  <li>{escape(sentence)}</li>")
        parts.append("</ul>")

    # Booking
    booking = tour.get("booking_en", tour.get("booking", "")).strip()
    if booking:
        parts.append("<h3>Bookings</h3>")
        parts.append("<ul>")
        for sentence in re.split(r'(?<=[.!])\s*', booking):
            sentence = sentence.strip()
            if sentence:
                parts.append(f"  <li>{escape(sentence)}</li>")
        parts.append("</ul>")

    return "\n".join(parts)


# ── Odoo helpers ─────────────────────────────────────────────────────────

def _find_parent_view(client, key):
    """Find a QWeb view by its key."""
    result = client.search_read('ir.ui.view',
        domain=[['key', '=', key]],
        fields=['id', 'name'], limit=1)
    if result:
        return result[0]['id'], result[0]['name']
    return None, None


def _upsert_qweb_view(client, name, arch_en, parent_key):
    """Create or update a QWeb inherited view."""
    existing = client.search_read('ir.ui.view',
        domain=[['name', '=', name]],
        fields=['id', 'key'])
    if existing:
        view_id = existing[0]['id']
        vals = {'arch': arch_en}
        if existing[0].get('key') != name:
            vals['key'] = name
        client.execute('ir.ui.view', 'write', [view_id], vals,
                        context={'lang': 'en_US'})
        print(f"  [UPDATED] {name} (id={view_id})")
        return view_id

    parent_id, parent_name = _find_parent_view(client, parent_key)
    if not parent_id:
        print(f"  [ERROR] Parent view '{parent_key}' not found!")
        return None

    print(f"  Parent: {parent_name} (id={parent_id})")
    result = client.execute('ir.ui.view', 'create', [{
        'name': name,
        'key': name,
        'inherit_id': parent_id,
        'type': 'qweb',
        'arch': arch_en,
        'priority': 99,
    }], context={'lang': 'en_US'})
    view_id = result[0] if isinstance(result, list) else result
    print(f"  [CREATED] {name} (id={view_id})")
    return view_id


def _upsert_form_view(client, name, arch, parent_model, parent_arch_contains):
    """Create or update an inherited backend form view.

    Finds the parent view by searching for a form view of `parent_model`
    whose arch contains `parent_arch_contains`.
    """
    existing = client.search_read('ir.ui.view',
        domain=[['name', '=', name]],
        fields=['id'])
    if existing:
        view_id = existing[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': arch})
        print(f"  [UPDATED] {name} (id={view_id})")
        return view_id

    # Find parent view
    parents = client.search_read('ir.ui.view',
        domain=[
            ['model', '=', parent_model],
            ['type', '=', 'form'],
            ['arch_db', 'ilike', parent_arch_contains],
        ],
        fields=['id', 'name'],
        order='priority asc',
        limit=1)
    if not parents:
        print(f"  [ERROR] No form view of {parent_model} containing"
              f" '{parent_arch_contains}' found!")
        return None

    parent_id = parents[0]['id']
    parent_name = parents[0]['name']
    print(f"  Parent: {parent_name} (id={parent_id})")

    result = client.execute('ir.ui.view', 'create', [{
        'name': name,
        'model': parent_model,
        'inherit_id': parent_id,
        'type': 'form',
        'arch': arch,
        'priority': 99,
    }])
    view_id = result[0] if isinstance(result, list) else result
    print(f"  [CREATED] {name} (id={view_id})")
    return view_id


def create_field(client):
    """Create x_extended_description (html) field on product.template."""
    # Find product.template model id
    model = client.search_read('ir.model',
        domain=[['model', '=', 'product.template']],
        fields=['id'], limit=1)
    if not model:
        print("  [ERROR] product.template model not found!")
        return False

    model_id = model[0]['id']

    # Check if field already exists
    existing = client.search_read('ir.model.fields',
        domain=[['model', '=', 'product.template'],
                ['name', '=', 'x_extended_description']],
        fields=['id'])
    if existing:
        print(f"  [EXISTS] x_extended_description (id={existing[0]['id']})")
        return True

    result = client.execute('ir.model.fields', 'create', [{
        'model_id': model_id,
        'name': 'x_extended_description',
        'field_description': 'Extended Description',
        'ttype': 'html',
        'copied': True,
    }])
    field_id = result[0] if isinstance(result, list) else result
    print(f"  [CREATED] x_extended_description (id={field_id})")
    return True


def ensure_translatable(client):
    """Ensure x_extended_description is translatable."""
    field = client.search_read('ir.model.fields',
        domain=[['model', '=', 'product.template'],
                ['name', '=', 'x_extended_description']],
        fields=['id', 'translate'])
    if field and not field[0]['translate']:
        client.execute('ir.model.fields', 'write', [field[0]['id']],
                        {'translate': True})
        print(f"  [UPDATED] x_extended_description translate=True")
    elif field:
        print(f"  [OK] x_extended_description already translatable"
              f" ({field[0]['translate']})")


def _build_translation_mapping(client, pid, field_name, es_html):
    """Build {en_source: es_value} mapping for update_field_translations.

    After writing EN HTML to the field, Odoo's html_translate extracts
    source terms. We call get_field_translations() to discover them,
    then extract matching ES terms from the ES HTML in the same order.
    """
    from html.parser import HTMLParser

    # Get the source terms Odoo extracted from the EN HTML
    result = client.execute('product.template', 'get_field_translations',
                             [pid], field_name, ['es_419'])
    if not result or not isinstance(result, (list, tuple)) or not result[0]:
        return {}

    source_terms = [t['source'] for t in result[0] if isinstance(t, dict)]
    if not source_terms:
        return {}

    # Extract text segments from ES HTML in document order.
    # Odoo's html_translate extracts text from block-level elements,
    # keeping inline tags (<strong>, <em>, <a>, etc.) as part of the term.
    class SegmentExtractor(HTMLParser):
        BLOCK_TAGS = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'td', 'th', 'dt', 'dd', 'div'}
        INLINE_TAGS = {'strong', 'em', 'b', 'i', 'a', 'span', 'small', 'code', 'br'}

        def __init__(self):
            super().__init__()
            self.segments = []
            self._in_block = False
            self._current = []
            self._tag_stack = []

        def handle_starttag(self, tag, attrs):
            if tag in self.BLOCK_TAGS:
                self._flush()
                self._in_block = True
            elif tag in self.INLINE_TAGS and self._in_block:
                # Keep inline tags as part of the segment
                attr_str = ''
                for k, v in attrs:
                    attr_str += f' {k}="{v}"'
                self._current.append(f'<{tag}{attr_str}>')
            self._tag_stack.append(tag)

        def handle_endtag(self, tag):
            if tag in self.INLINE_TAGS and self._in_block:
                self._current.append(f'</{tag}>')
            elif tag in self.BLOCK_TAGS:
                self._flush()
                self._in_block = False
            if self._tag_stack and self._tag_stack[-1] == tag:
                self._tag_stack.pop()

        def handle_data(self, data):
            if self._in_block:
                self._current.append(data)

        def _flush(self):
            text = ''.join(self._current).strip()
            if text:
                self.segments.append(text)
            self._current = []

    extractor = SegmentExtractor()
    extractor.feed(es_html)
    extractor._flush()  # flush any remaining
    es_segments = extractor.segments

    # Build mapping: pair source_terms (EN) with es_segments (ES) by position
    mapping = {}
    for i, en_term in enumerate(source_terms):
        if i < len(es_segments):
            es_term = es_segments[i]
            if en_term != es_term:  # Only add if different
                mapping[en_term] = es_term

    return mapping


def migrate_descriptions(client, dry_run=False):
    """Migrate tour products: write en_US base + es_419 translations.

    Uses update_field_translations() for proper html_translate support:
    1. Write EN HTML as base (context=en_US)
    2. Get source terms via get_field_translations()
    3. Map EN→ES terms from the ES HTML
    4. Apply via update_field_translations()
    """
    if not TOURS_JSON.exists():
        print(f"  [ERROR] {TOURS_JSON} not found — cannot migrate")
        return

    with open(TOURS_JSON, 'r', encoding='utf-8') as f:
        tours = json.load(f)

    # Get all tour products from Odoo
    products = client.search_read('product.template',
        domain=[['categ_id.name', 'ilike', 'Tours']],
        fields=['id', 'name'],
        order='name')
    product_map = {p['name'].lower().strip(): p for p in products}

    migrated = 0
    skipped = 0

    for tour in tours:
        if 'error' in tour:
            skipped += 1
            continue

        title = tour['title']
        product = product_map.get(title.lower().strip())
        if not product:
            print(f"    [SKIP] {title}: no matching product")
            skipped += 1
            continue

        pid = product['id']

        # Build Spanish HTML
        short_es = build_short_description_html(tour)
        extended_es = build_extended_description_html(tour)
        # Build English HTML
        short_en = build_short_description_html_en(tour)
        extended_en = build_extended_description_html_en(tour)

        if not extended_es.strip():
            print(f"    [SKIP] {title}: no extended content")
            skipped += 1
            continue

        if dry_run:
            print(f"    [MIGRATE] id={pid} {title}"
                  f" (es: short={len(short_es)}ch ext={len(extended_es)}ch,"
                  f" en: short={len(short_en)}ch ext={len(extended_en)}ch)")
        else:
            # Step 1: Write EN HTML as base
            client.execute('product.template', 'write', [pid], {
                'description_ecommerce': short_en,
                'x_extended_description': extended_en,
            }, context={'lang': 'en_US'})

            # Step 2-3: Build ES translation mappings
            short_map = _build_translation_mapping(
                client, pid, 'description_ecommerce', short_es)
            extended_map = _build_translation_mapping(
                client, pid, 'x_extended_description', extended_es)

            # Step 4: Apply ES translations
            if short_map:
                client.execute('product.template', 'update_field_translations',
                               [pid], 'description_ecommerce',
                               {'es_419': short_map})
            if extended_map:
                client.execute('product.template', 'update_field_translations',
                               [pid], 'x_extended_description',
                               {'es_419': extended_map})

            n_terms = len(short_map) + len(extended_map)
            print(f"    [MIGRATED] id={pid} {title} "
                  f"(en_US base + es_419 {n_terms} terms)")
            time.sleep(0.3)

        migrated += 1

    print(f"\n  Migration: {migrated} migrated, {skipped} skipped")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Setup extended description field + QWeb view for tour products")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview migration without writing to Odoo")
    parser.add_argument('--no-migrate', action='store_true',
                        help="Only create field + view, skip data migration")
    args = parser.parse_args()

    client = OdooClient()
    client.connect()
    print(f"Connected to Odoo as uid={client.uid}")

    # ── 1. Create field + ensure translatable ──
    print("\n1. Create x_extended_description field on product.template")
    if not create_field(client):
        return
    ensure_translatable(client)

    # ── 2a. Create QWeb view (website) ──
    print("\n2a. Create QWeb view: extended description section (website)")
    _upsert_qweb_view(client,
        name='agency_ecommerce.extended_description_tour',
        arch_en=ECOM_EXTENDED_DESC_ARCH,
        parent_key='website_sale.product',
    )

    # ── 2b. Create backend form view (product.template ecommerce tab) ──
    print("\n2b. Backend form view: add x_extended_description to ecommerce tab")
    _upsert_form_view(client,
        name='agency.product_template_extended_desc',
        arch=PRODUCT_EXTENDED_DESC_FORM_ARCH,
        parent_model='product.template',
        parent_arch_contains='description_ecommerce',
    )

    # ── 3. Migrate data ──
    if args.no_migrate:
        print("\n3. Data migration skipped (--no-migrate)")
    else:
        print(f"\n3. Migrate tour descriptions{'  (DRY RUN)' if args.dry_run else ''}")
        migrate_descriptions(client, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("EXTENDED DESCRIPTION SETUP COMPLETE")
    print("=" * 60)
    print("\nVerification:")
    print("  - Go to a tour product in /shop → short description next to image")
    print("  - Below the image section, extended description with itinerary/details")
    print("  - Specifications section below the extended description")


if __name__ == "__main__":
    main()
