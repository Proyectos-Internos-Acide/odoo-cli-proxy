#!/usr/bin/env python3
"""Setup tour product fields, one2many models, and views.

Creates:
  1. x_is_tour boolean on product.template
  2. 6 html + 4 char translatable fields on product.template
  3. 3 one2many models (include/exclude/recommendation lines) with ACLs
  4. 3 one2many fields on product.template
  5. Backend form views (General Info + Ecommerce tab)
  6. QWeb frontend view for structured tour sections
  7. Sets x_is_tour=True on existing tour products
  8. Migrates data from wordpress_tours.json into new fields

Usage:
    # Full setup: fields + models + views + migration
    uv run python business_units/hotel-trip-agency/agency/setup_tour_product_fields.py

    # Preview migration without applying
    uv run python business_units/hotel-trip-agency/agency/setup_tour_product_fields.py --dry-run

    # Only create fields + models + views (no data migration)
    uv run python business_units/hotel-trip-agency/agency/setup_tour_product_fields.py --no-migrate
"""
import argparse
import json
import sys
import os
import time
from pathlib import Path
import re
from html import escape

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from odoo_cli import OdooClient
from agency.defaults.views import (
    PRODUCT_IS_TOUR_FORM_ARCH,
    PRODUCT_TOUR_FIELDS_FORM_ARCH,
    ECOM_TOUR_SECTIONS_ARCH,
    ECOM_EXTENDED_DESC_ARCH,
    ECOM_TRANSLATIONS_ES,
)
from agency.setup_extended_description import _DAY_RE

TOURS_JSON = Path(__file__).parent / "generated" / "wordpress_tours.json"


# ── Odoo helpers ─────────────────────────────────────────────────────────

def _field_exists(client, model_name, field_name):
    result = client.search_read('ir.model.fields',
        domain=[['model', '=', model_name], ['name', '=', field_name]],
        fields=['id'], limit=1)
    return result[0]['id'] if result else False


def _create_field(client, field_def, model_id):
    existing = _field_exists(client, field_def['model'], field_def['name'])
    if existing:
        print(f"    [EXISTS] {field_def['name']} (id={existing})")
        return existing, False
    vals = {**field_def, 'model_id': model_id, 'store': True}
    result = client.execute('ir.model.fields', 'create', [vals])
    fid = result[0] if isinstance(result, list) else result
    print(f"    [CREATED] {field_def['name']} (id={fid})")
    return fid, True


def _ensure_translatable(client, model_name, field_name):
    field = client.search_read('ir.model.fields',
        domain=[['model', '=', model_name], ['name', '=', field_name]],
        fields=['id', 'translate'])
    if field and not field[0]['translate']:
        client.execute('ir.model.fields', 'write', [field[0]['id']],
                        {'translate': True})
        print(f"    [UPDATED] {field_name} translate=True")


def _create_model(client, name, model_name):
    existing = client.search_read('ir.model',
        domain=[['model', '=', model_name]], fields=['id'])
    if existing:
        print(f"    [EXISTS] {model_name} (id={existing[0]['id']})")
        return existing[0]['id'], False
    result = client.execute('ir.model', 'create', [{
        'name': name,
        'model': model_name,
        'state': 'manual',
    }])
    mid = result[0] if isinstance(result, list) else result
    print(f"    [CREATED] {model_name} (id={mid})")
    return mid, True


def _ensure_acl(client, name, model_id, group_id=1):
    existing = client.search_read('ir.model.access',
        domain=[['name', '=', name]], fields=['id'])
    if existing:
        print(f"    [EXISTS] ACL {name} (id={existing[0]['id']})")
        return existing[0]['id'], False
    result = client.execute('ir.model.access', 'create', [{
        'name': name,
        'model_id': model_id,
        'group_id': group_id,
        'perm_read': True,
        'perm_write': True,
        'perm_create': True,
        'perm_unlink': True,
    }])
    aid = result[0] if isinstance(result, list) else result
    print(f"    [CREATED] ACL {name} (id={aid})")
    return aid, True


def _get_model_id(client, model_name):
    result = client.search_read('ir.model',
        domain=[['model', '=', model_name]],
        fields=['id'], limit=1)
    return result[0]['id'] if result else None


def _find_parent_view(client, key):
    result = client.search_read('ir.ui.view',
        domain=[['key', '=', key]],
        fields=['id', 'name'], limit=1)
    if result:
        return result[0]['id'], result[0]['name']
    return None, None


def _upsert_form_view(client, name, arch, parent_model, parent_arch_contains):
    existing = client.search_read('ir.ui.view',
        domain=[['name', '=', name]],
        fields=['id'])
    if existing:
        view_id = existing[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': arch})
        print(f"    [UPDATED] {name} (id={view_id})")
        return view_id

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
        print(f"    [ERROR] No form view of {parent_model} containing"
              f" '{parent_arch_contains}' found!")
        return None

    parent_id = parents[0]['id']
    print(f"    Parent: {parents[0]['name']} (id={parent_id})")

    result = client.execute('ir.ui.view', 'create', [{
        'name': name,
        'model': parent_model,
        'inherit_id': parent_id,
        'type': 'form',
        'arch': arch,
        'priority': 99,
    }])
    view_id = result[0] if isinstance(result, list) else result
    print(f"    [CREATED] {name} (id={view_id})")
    return view_id


def _upsert_qweb_view(client, name, arch_en, parent_key, translations=None):
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
        print(f"    [UPDATED] {name} (id={view_id})")
    else:
        parent_id, parent_name = _find_parent_view(client, parent_key)
        if not parent_id:
            print(f"    [ERROR] Parent view '{parent_key}' not found!")
            return None
        print(f"    Parent: {parent_name} (id={parent_id})")
        result = client.execute('ir.ui.view', 'create', [{
            'name': name,
            'key': name,
            'inherit_id': parent_id,
            'type': 'qweb',
            'arch': arch_en,
            'priority': 99,
        }], context={'lang': 'en_US'})
        view_id = result[0] if isinstance(result, list) else result
        print(f"    [CREATED] {name} (id={view_id})")

    if translations:
        client.execute('ir.ui.view', 'update_field_translations',
                        [view_id], 'arch_db', {'es_419': translations})
        print(f"    [i18n] es_419 translations applied ({len(translations)} terms)")

    return view_id


# ── Step 1: x_is_tour boolean ───────────────────────────────────────────

def setup_is_tour_field(client, pt_model_id):
    print("\n1. Create x_is_tour boolean on product.template")
    _create_field(client, {
        'model': 'product.template',
        'name': 'x_is_tour',
        'field_description': 'Is a Tour',
        'ttype': 'boolean',
        'copied': True,
    }, pt_model_id)


# ── Step 2: Rich-text and char fields ───────────────────────────────────

HTML_FIELDS = [
    ('x_tour_details', 'Tour Details'),
    ('x_tour_itinerary', 'Itinerary'),
    ('x_tour_schedule', 'Departures'),
    ('x_tour_conditions', 'Conditions'),
    ('x_tour_booking_notes', 'Booking Considerations'),
    ('x_tour_pricing_notes', 'Pricing'),
]

CHAR_FIELDS = [
    ('x_tour_departure_location', 'Departure Location'),
    ('x_tour_return_location', 'Return Location'),
    ('x_tour_departure_time', 'Departure Time'),
    ('x_tour_return_time', 'Return Time'),
]


def setup_tour_data_fields(client, pt_model_id):
    print("\n2. Create tour data fields on product.template")

    for name, label in HTML_FIELDS:
        _create_field(client, {
            'model': 'product.template',
            'name': name,
            'field_description': label,
            'ttype': 'html',
            'translate': True,
            'copied': True,
        }, pt_model_id)

    for name, label in CHAR_FIELDS:
        _create_field(client, {
            'model': 'product.template',
            'name': name,
            'field_description': label,
            'ttype': 'char',
            'translate': True,
            'copied': True,
        }, pt_model_id)

    # Ensure all fields are translatable (in case they were created before
    # with translate=False)
    for name, _ in HTML_FIELDS + CHAR_FIELDS:
        _ensure_translatable(client, 'product.template', name)


# ── Step 3: One2many line models ─────────────────────────────────────────

LINE_MODELS = [
    ('x_tour_include_line', 'Tour Include Line'),
    ('x_tour_exclude_line', 'Tour Exclude Line'),
    ('x_tour_recommendation_line', 'Tour Recommendation Line'),
]

O2M_FIELDS = [
    ('x_tour_includes_ids', 'Includes', 'x_tour_include_line'),
    ('x_tour_excludes_ids', 'Excludes', 'x_tour_exclude_line'),
    ('x_tour_recommendations_ids', 'Recommendations', 'x_tour_recommendation_line'),
]


def setup_line_models(client, pt_model_id):
    print("\n3. Create one2many line models")

    for model_name, model_label in LINE_MODELS:
        # Create the model
        mid, created = _create_model(client, model_label, model_name)

        # Create fields on line model
        _create_field(client, {
            'model': model_name,
            'name': 'x_sequence',
            'field_description': 'Sequence',
            'ttype': 'integer',
        }, mid)

        _create_field(client, {
            'model': model_name,
            'name': 'x_name',
            'field_description': 'Name',
            'ttype': 'char',
            'translate': True,
        }, mid)
        # Ensure x_name is translatable (Odoo auto-creates it with translate=False)
        _ensure_translatable(client, model_name, 'x_name')

        _create_field(client, {
            'model': model_name,
            'name': 'x_product_tmpl_id',
            'field_description': 'Product Template',
            'ttype': 'many2one',
            'relation': 'product.template',
            'on_delete': 'cascade',
        }, mid)

        # ACL
        _ensure_acl(client, f'access_{model_name}_all', mid)

    # Create one2many fields on product.template
    print("\n   One2many fields on product.template:")
    for o2m_name, o2m_label, line_model in O2M_FIELDS:
        _create_field(client, {
            'model': 'product.template',
            'name': o2m_name,
            'field_description': o2m_label,
            'ttype': 'one2many',
            'relation': line_model,
            'relation_field': 'x_product_tmpl_id',
            'copied': True,
        }, pt_model_id)


# ── Step 4: Backend views ────────────────────────────────────────────────

def setup_backend_views(client):
    print("\n4. Backend form views")

    # 4a. General Info: x_is_tour checkbox
    print("  4a. General Info — x_is_tour checkbox")
    _upsert_form_view(client,
        name='agency.product_template_is_tour',
        arch=PRODUCT_IS_TOUR_FORM_ARCH,
        parent_model='product.template',
        parent_arch_contains='widget="radio"',
    )

    # 4b. Ecommerce tab: tour fields
    print("  4b. Ecommerce tab — tour data fields")
    _upsert_form_view(client,
        name='agency.product_template_tour_fields',
        arch=PRODUCT_TOUR_FIELDS_FORM_ARCH,
        parent_model='product.template',
        parent_arch_contains='ecom_extended_description',
    )


# ── Step 5: QWeb frontend view ──────────────────────────────────────────

def setup_frontend_views(client):
    print("\n5. QWeb frontend views")

    es_translations = dict(ECOM_TRANSLATIONS_ES)

    # 5a. Tour structured sections (new view, replaces extended_description blob)
    print("  5a. Tour structured sections")
    _upsert_qweb_view(client,
        name='agency_ecommerce.tour_sections',
        arch_en=ECOM_TOUR_SECTIONS_ARCH,
        parent_key='website_sale.product',
        translations=es_translations,
    )

    # 5b. Update existing extended description view
    # (now only shows for tours that have x_extended_description as fallback)
    print("  5b. Update extended description view (updated detection)")
    _upsert_qweb_view(client,
        name='agency_ecommerce.extended_description_tour',
        arch_en=ECOM_EXTENDED_DESC_ARCH,
        parent_key='website_sale.product',
    )


# ── Step 6: Set x_is_tour on existing tours ──────────────────────────────

def set_is_tour_on_existing(client):
    print("\n6. Set x_is_tour=True on existing tour products")

    tour_products = client.search_read('product.template',
        domain=[['categ_id.name', 'ilike', 'Tours']],
        fields=['id', 'name', 'x_is_tour'])

    already = [p for p in tour_products if p.get('x_is_tour')]
    to_set = [p for p in tour_products if not p.get('x_is_tour')]

    if already:
        print(f"    [OK] {len(already)} products already have x_is_tour=True")

    if to_set:
        ids = [p['id'] for p in to_set]
        client.execute('product.template', 'write', ids, {'x_is_tour': True})
        print(f"    [UPDATED] Set x_is_tour=True on {len(to_set)} products:")
        for p in to_set:
            print(f"      - id={p['id']} {p['name']}")
    elif not already:
        print("    [WARN] No tour products found in 'Tours' category")


# ── Step 7: Data migration ──────────────────────────────────────────────

def _add_visual_breaks(text, max_chunk=350):
    """Insert <br/><br/> at sentence boundaries for long text blocks.

    Splits at '. ' followed by uppercase letter/number. Each chunk targets
    ~max_chunk chars. Returns escaped HTML with <br/><br/> separators.
    """
    if not text or len(text) <= max_chunk:
        return escape(text) if text else ''

    # Split at sentence boundaries: period + space + uppercase/number
    parts = re.split(r'(?<=\.) (?=[A-ZÁÉÍÓÚÑ0-9])', text)

    chunks = []
    current = []
    current_len = 0

    for part in parts:
        if current_len + len(part) > max_chunk and current:
            chunks.append(escape(' '.join(current)))
            current = [part]
            current_len = len(part)
        else:
            current.append(part)
            current_len += len(part)

    if current:
        chunks.append(escape(' '.join(current)))

    return '<br/><br/>'.join(chunks)


def _format_multiday_simple(text, lang='es'):
    """Format multi-day itinerary as h4 + p per day (no li splitting).

    This guarantees identical segment counts for EN and ES, which is required
    for the html_translate positional mapping to work correctly.
    """
    lines = text.split('\n')
    parts = []
    current_day = None
    current_content = []
    day_has_title = False

    def flush_day():
        if current_day and current_content:
            content = ' '.join(current_content).strip()
            parts.append(f"<h4>{escape(current_day)}</h4>")
            parts.append(f"<p>{_add_visual_breaks(content)}</p>")

    for line in lines:
        line = line.strip()
        if not line:
            continue
        m = _DAY_RE.match(line)
        if m:
            flush_day()
            day_num = m.group(1)
            day_title = m.group(2).strip().rstrip('.') or ''
            if lang == 'en':
                current_day = f"Day {day_num}" + (f": {day_title}" if day_title else '')
            else:
                current_day = f"Día {day_num}" + (f": {day_title}" if day_title else '')
            current_content = []
            day_has_title = bool(day_title)
        else:
            # If day has no title and this is first content line,
            # and it looks like a route name (short, contains –), use as title
            if (not day_has_title and not current_content and current_day
                    and len(line) < 80 and ('–' in line or '→' in line)):
                current_day += f": {line}"
                day_has_title = True
                continue
            current_content.append(line)

    flush_day()
    return '\n'.join(parts)


def _format_html(text, field_type='default', lang='en'):
    """Format plain text into structured HTML based on field type.

    IMPORTANT: EN and ES must produce the same number of block-level segments
    for html_translate positional mapping to work. This formatter uses:
    - Multi-day itinerary: h4 + p per day (no li splitting)
    - Single-day itinerary: single p
    - Conditions/booking: single p (all lines joined)
    - Prices/details/schedule: p per newline

    Args:
        text: Raw text from wordpress_tours.json.
        field_type: One of 'itinerary', 'conditions', 'booking', 'prices',
                    'details', 'schedule', or 'default'.
        lang: 'en' or 'es' — only affects itinerary day headers.
    """
    if not text:
        return False
    text = text.strip()
    if not text:
        return False

    if field_type == 'itinerary':
        is_multiday = bool(_DAY_RE.search(text))
        if is_multiday:
            return _format_multiday_simple(text, lang)
        else:
            # Single-day: join lines into one block, then add visual breaks
            content = ' '.join(line.strip() for line in text.split('\n') if line.strip())
            return f'<p>{_add_visual_breaks(content)}</p>'

    elif field_type in ('conditions', 'booking'):
        # Single paragraph — guarantees 1 segment regardless of newline
        # differences between EN and ES translations
        content = ' '.join(line.strip() for line in text.split('\n') if line.strip())
        return f'<p>{escape(content)}</p>' if content else False

    elif field_type == 'prices':
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return '\n'.join(f'<p>{escape(l)}</p>' for l in lines)

    else:  # 'details', 'schedule', or 'default'
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        return '\n'.join(f'<p>{escape(l)}</p>' for l in lines)


def _build_html_translation_mapping(client, pid, field_name, es_html):
    """Build {en_source: es_value} mapping for html_translate fields."""
    from html.parser import HTMLParser

    result = client.execute('product.template', 'get_field_translations',
                             [pid], field_name, ['es_419'])
    if not result or not isinstance(result, (list, tuple)) or not result[0]:
        return {}

    source_terms = [t['source'] for t in result[0] if isinstance(t, dict)]
    if not source_terms:
        return {}

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
    extractor._flush()
    es_segments = extractor.segments

    mapping = {}
    for i, en_term in enumerate(source_terms):
        if i < len(es_segments):
            es_term = es_segments[i]
            if en_term != es_term:
                mapping[en_term] = es_term

    return mapping


def migrate_tour_data(client, dry_run=False):
    print(f"\n7. Migrate tour data from wordpress_tours.json"
          f"{'  (DRY RUN)' if dry_run else ''}")

    if not TOURS_JSON.exists():
        print(f"    [ERROR] {TOURS_JSON} not found — cannot migrate")
        return

    with open(TOURS_JSON, 'r', encoding='utf-8') as f:
        tours = json.load(f)

    # Get all tour products
    products = client.search_read('product.template',
        domain=[['x_is_tour', '=', True]],
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
        details = tour.get('details', {})
        details_en = tour.get('details_en', {})

        # Build EN values for char fields
        en_vals = {}
        departure_loc_en = details_en.get('departure_location', details.get('departure_location', ''))
        return_loc_en = details_en.get('return_location', details.get('return_location', ''))
        departure_time_en = details_en.get('departure_time', details.get('departure_time', ''))
        return_time_en = details_en.get('return_time', details.get('return_time', ''))

        if departure_loc_en:
            en_vals['x_tour_departure_location'] = departure_loc_en
        if return_loc_en:
            en_vals['x_tour_return_location'] = return_loc_en
        if departure_time_en:
            en_vals['x_tour_departure_time'] = departure_time_en
        if return_time_en:
            en_vals['x_tour_return_time'] = return_time_en

        # Build EN values for html fields (wrap plain text in <p>)
        desc_en = tour.get('description_en', tour.get('description', ''))
        itin_en = tour.get('itinerary_en', tour.get('itinerary', ''))
        sched_en = tour.get('schedule_en', tour.get('schedule', ''))
        cond_en = tour.get('conditions_en', tour.get('conditions', ''))
        book_en = tour.get('booking_en', tour.get('booking', ''))
        price_en = tour.get('prices_en', tour.get('prices', ''))

        en_vals['x_tour_details'] = _format_html(desc_en, 'details') or False
        en_vals['x_tour_itinerary'] = _format_html(itin_en, 'itinerary', 'en') or False
        en_vals['x_tour_schedule'] = _format_html(sched_en, 'schedule') or False
        en_vals['x_tour_conditions'] = _format_html(cond_en, 'conditions') or False
        en_vals['x_tour_booking_notes'] = _format_html(book_en, 'booking') or False
        en_vals['x_tour_pricing_notes'] = _format_html(price_en, 'prices') or False

        # Build ES values for char fields
        es_char_translations = {}
        departure_loc_es = details.get('departure_location', '')
        return_loc_es = details.get('return_location', '')
        departure_time_es = details.get('departure_time', '')
        return_time_es = details.get('return_time', '')

        if departure_loc_en and departure_loc_es and departure_loc_en != departure_loc_es:
            es_char_translations['x_tour_departure_location'] = (departure_loc_en, departure_loc_es)
        if return_loc_en and return_loc_es and return_loc_en != return_loc_es:
            es_char_translations['x_tour_return_location'] = (return_loc_en, return_loc_es)
        if departure_time_en and departure_time_es and departure_time_en != departure_time_es:
            es_char_translations['x_tour_departure_time'] = (departure_time_en, departure_time_es)
        if return_time_en and return_time_es and return_time_en != return_time_es:
            es_char_translations['x_tour_return_time'] = (return_time_en, return_time_es)

        # Build ES html values
        es_html = {}
        desc_es = tour.get('description', '')
        itin_es = tour.get('itinerary', '')
        sched_es = tour.get('schedule', '')
        cond_es = tour.get('conditions', '')
        book_es = tour.get('booking', '')
        price_es = tour.get('prices', '')

        if desc_es:
            es_html['x_tour_details'] = _format_html(desc_es, 'details')
        if itin_es:
            es_html['x_tour_itinerary'] = _format_html(itin_es, 'itinerary', 'es')
        if sched_es:
            es_html['x_tour_schedule'] = _format_html(sched_es, 'schedule')
        if cond_es:
            es_html['x_tour_conditions'] = _format_html(cond_es, 'conditions')
        if book_es:
            es_html['x_tour_booking_notes'] = _format_html(book_es, 'booking')
        if price_es:
            es_html['x_tour_pricing_notes'] = _format_html(price_es, 'prices')

        # Build includes/excludes/recommendations
        includes_en = tour.get('includes_en', tour.get('includes', []))
        excludes_en = tour.get('excludes_en', tour.get('excludes', []))
        recs_en = tour.get('recommendations_en', tour.get('recommendations', []))
        includes_es = tour.get('includes', [])
        excludes_es = tour.get('excludes', [])
        recs_es = tour.get('recommendations', [])

        if dry_run:
            n_html = sum(1 for v in en_vals.values() if v)
            n_lines = len(includes_en) + len(excludes_en) + len(recs_en)
            print(f"    [MIGRATE] id={pid} {title}"
                  f" (fields={n_html}, lines={n_lines})")
        else:
            # Step 1: Write EN values as base
            write_vals = {k: v for k, v in en_vals.items() if v}
            if write_vals:
                client.execute('product.template', 'write', [pid],
                               write_vals, context={'lang': 'en_US'})

            # Step 2: Apply ES translations for html fields
            n_terms = 0
            for field_name, es_val in es_html.items():
                if es_val and en_vals.get(field_name):
                    mapping = _build_html_translation_mapping(
                        client, pid, field_name, es_val)
                    if mapping:
                        client.execute('product.template',
                                       'update_field_translations',
                                       [pid], field_name,
                                       {'es_419': mapping})
                        n_terms += len(mapping)

            # Step 3: Apply ES translations for char fields
            # char translate=True fields accept a plain string, not a dict
            for field_name, (en_val, es_val) in es_char_translations.items():
                client.execute('product.template',
                               'update_field_translations',
                               [pid], field_name,
                               {'es_419': es_val})
                n_terms += 1

            # Step 4: Create one2many lines (includes)
            _write_line_items(client, pid, 'x_tour_include_line',
                              includes_en, includes_es)

            # Step 5: Create one2many lines (excludes)
            _write_line_items(client, pid, 'x_tour_exclude_line',
                              excludes_en, excludes_es)

            # Step 6: Create one2many lines (recommendations)
            _write_line_items(client, pid, 'x_tour_recommendation_line',
                              recs_en, recs_es)

            n_lines = len(includes_en) + len(excludes_en) + len(recs_en)
            print(f"    [MIGRATED] id={pid} {title}"
                  f" (es_419: {n_terms} terms, {n_lines} lines)")

        migrated += 1

    print(f"\n    Migration: {migrated} migrated, {skipped} skipped")


def _write_line_items(client, pid, model_name, items_en, items_es):
    """Create one2many line records with EN base + ES translations."""
    if not items_en:
        return

    # Delete existing lines for this product
    existing = client.execute(model_name, 'search',
        [('x_product_tmpl_id', '=', pid)])
    if existing:
        client.execute(model_name, 'unlink', existing)

    for i, en_text in enumerate(items_en):
        result = client.execute(model_name, 'create', [{
            'x_product_tmpl_id': pid,
            'x_sequence': (i + 1) * 10,
            'x_name': en_text,
        }], context={'lang': 'en_US'})
        line_id = result[0] if isinstance(result, list) else result

        # Apply ES translation using write + lang context
        es_text = items_es[i] if i < len(items_es) else None
        if es_text and es_text != en_text:
            client.execute(model_name, 'write', [line_id],
                           {'x_name': es_text},
                           context={'lang': 'es_419'})


# ── Step 8: Clear extended description ─────────────────────────────────

def clear_extended_description(client):
    """Clear x_extended_description for all tour products.

    All content is now in structured fields (details, itinerary, includes,
    excludes, recommendations, conditions, booking, pricing).
    The ECOM_EXTENDED_DESC_ARCH view hides automatically when the field is empty.
    """
    print("\n8. Clear x_extended_description (content now in structured fields)")

    products = client.search_read('product.template',
        domain=[['x_is_tour', '=', True], ['x_extended_description', '!=', False]],
        fields=['id', 'name'])

    if not products:
        print("    [OK] No tour products have x_extended_description set")
        return

    ids = [p['id'] for p in products]
    client.execute('product.template', 'write', ids,
                    {'x_extended_description': False})
    print(f"    [CLEARED] x_extended_description on {len(products)} products:")
    for p in products:
        print(f"      - id={p['id']} {p['name']}")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Setup tour product fields, models, views and data")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview migration without writing to Odoo")
    parser.add_argument('--no-migrate', action='store_true',
                        help="Only create fields/models/views, skip data migration")
    parser.add_argument('--target', action='store_true',
                        help="Run against TARGET_MIGRATION (production) instance")
    args = parser.parse_args()

    if args.target:
        from odoo_cli.target import get_target_client
        client = get_target_client()
        if not client:
            print("[ERROR] TARGET_MIGRATION_* variables not configured in .env")
            return
        client.connect()
        print(f"Connected to TARGET (production) as uid={client.uid}")
    else:
        client = OdooClient()
        client.connect()
        print(f"Connected to Odoo as uid={client.uid}")

    pt_model_id = _get_model_id(client, 'product.template')
    if not pt_model_id:
        print("[ERROR] product.template model not found!")
        return

    print(f"product.template model_id={pt_model_id}")

    # ── Steps 1-3: Fields and models ──
    setup_is_tour_field(client, pt_model_id)
    setup_tour_data_fields(client, pt_model_id)
    setup_line_models(client, pt_model_id)

    # ── Steps 4-5: Views ──
    setup_backend_views(client)
    setup_frontend_views(client)

    # ── Step 6: Set x_is_tour on existing ──
    set_is_tour_on_existing(client)

    # ── Step 7: Data migration ──
    if args.no_migrate:
        print("\n7. Data migration skipped (--no-migrate)")
    else:
        migrate_tour_data(client, dry_run=args.dry_run)

    # ── Step 8: Clear extended description ──
    if not args.no_migrate and not args.dry_run:
        clear_extended_description(client)
    elif args.dry_run:
        print("\n8. Clear extended description skipped (dry run)")

    print("\n" + "=" * 70)
    print("  TOUR PRODUCT FIELDS SETUP COMPLETE")
    print("=" * 70)
    print("\nVerification:")
    print("  1. Open product form → General Info shows 'Is a Tour' checkbox")
    print("  2. Existing tour products have x_is_tour=True")
    print("  3. Open tour in ecommerce tab → new sections visible")
    print("  4. Uncheck x_is_tour → sections disappear")
    print("  5. Visit /shop → tours show 'from' + 'Quote' button")
    print("  6. Click tour → structured sections with data")
    print("  7. Switch to English → sections display in English")
    print("\nNext: Run setup_ecommerce.py to update QWeb detection logic")


if __name__ == "__main__":
    main()
