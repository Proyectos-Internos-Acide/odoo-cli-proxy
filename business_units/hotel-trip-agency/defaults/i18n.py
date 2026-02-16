"""Internationalization helpers for translatable default values.

The Odoo instance base language is English (en_US). Spanish (es_419) is
installed as an additional language. This means:
- The base column stores the English value
- es_419 translations are stored separately
- XML-RPC without context searches in English (base)

Usage in defaults:
    PRODUCT_NAME = {'es': "Agua", 'en': "Water"}

Usage in setup scripts:
    from defaults.i18n import t, write_translations, search_translatable

    # Create with default language (es) for display
    client.execute('model', 'create', [{'name': t(PRODUCT_NAME)}])

    # Write all translations (sets base=es, then en_US, then es_419)
    write_translations(client, 'model', record_id, {'name': PRODUCT_NAME})

    # Search by translatable name (tries ES first, then EN fallback)
    existing = search_translatable(client, 'model', 'name', PRODUCT_NAME, fields=['id'])
"""

DEFAULT_LANG = 'es'
LANG_CODES = {'es': 'es_419', 'en': 'en_US'}


def t(translatable, lang=None):
    """Extract value for a language from a translatable dict.
    If it's a plain string, return as-is."""
    if isinstance(translatable, dict):
        lang = lang or DEFAULT_LANG
        return translatable.get(lang, next(iter(translatable.values())))
    return translatable


def write_translations(client, model, record_id, fields_map):
    """Write translations for all languages on a record.

    fields_map: {'name': {'es': '...', 'en': '...'}, 'description': {...}}
    Skips fields that are plain strings (not translatable dicts).
    Writes es_419 and en_US translations explicitly.
    """
    for lang, lang_code in LANG_CODES.items():
        translated = {}
        for field, value in fields_map.items():
            if isinstance(value, dict) and lang in value:
                translated[field] = value[lang]
        if translated:
            client.execute(model, 'write', [record_id], translated,
                           context={'lang': lang_code})


def search_translatable(client, model, field, translatable, fields=None,
                        extra_domain=None):
    """Search for a record by a translatable field, trying all languages.

    Returns the first match found (ES first, then EN).
    """
    fields = fields or ['id', 'name']
    base_domain = extra_domain or []

    for lang in [DEFAULT_LANG, 'en']:
        name = t(translatable, lang)
        domain = base_domain + [[field, '=', name]]
        result = client.search_read(model, domain=domain, fields=fields, limit=1)
        if result:
            return result
    return []
