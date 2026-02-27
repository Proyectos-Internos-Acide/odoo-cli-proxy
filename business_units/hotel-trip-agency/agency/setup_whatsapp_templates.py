"""Setup WhatsApp auto-reply system: custom fields, views, automation, and sample templates.

Creates custom fields on whatsapp.template to manage auto-replies from the Odoo UI:
- x_is_auto_reply: marks template as local auto-reply (not sent to Meta)
- x_trigger_condition: when to trigger (first_message, keyword)
- x_trigger_keywords: comma-separated keywords to match

Also creates:
- x_wa_state on discuss.channel: tracks conversation state (menu, awaiting_preferences)
- Option 5: AI-powered tour recommendation (queries product DB + Odoo AI agent)

Updates the base.automation to read auto-reply config from whatsapp.template records.

Usage:
    PYTHONPATH=. python3 business_units/hotel-trip-agency/agency/setup_whatsapp_templates.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env'))

from odoo_cli.target import get_target_client


# ── IDs ───────────────────────────────────────────────────────────────────────
DISCUSS_CHANNEL_MODEL_ID = 228
WA_TEMPLATE_BASE_FORM_VIEW_ID = 4562
WA_ACCOUNT_ID = 2  # "Cuenta whatsapp business"


# ── Custom fields ─────────────────────────────────────────────────────────────
CUSTOM_FIELDS = [
    # discuss.channel state tracking
    {
        'name': 'x_wa_state',
        'field_description': 'WhatsApp Conversation State',
        'ttype': 'selection',
        'model': 'discuss.channel',
        'selection_ids': [
            (0, 0, {'value': 'menu', 'name': 'Menu', 'sequence': 1}),
            (0, 0, {'value': 'awaiting_preferences', 'name': 'Awaiting Preferences', 'sequence': 2}),
        ],
    },
    # whatsapp.template auto-reply fields
    {
        'name': 'x_is_auto_reply',
        'field_description': 'Auto-reply Only',
        'ttype': 'boolean',
        'model': 'whatsapp.template',
    },
    {
        'name': 'x_trigger_condition',
        'field_description': 'Trigger Condition',
        'ttype': 'selection',
        'model': 'whatsapp.template',
        'selection_ids': [
            (0, 0, {'value': 'first_message', 'name': 'First message', 'sequence': 1}),
            (0, 0, {'value': 'keyword', 'name': 'Contains keyword', 'sequence': 2}),
        ],
    },
    {
        'name': 'x_trigger_keywords',
        'field_description': 'Keywords (comma-separated)',
        'ttype': 'char',
        'model': 'whatsapp.template',
    },
    {
        'name': 'x_body_en',
        'field_description': 'Body (English)',
        'ttype': 'text',
        'model': 'whatsapp.template',
    },
]


# ── Inherited form view ──────────────────────────────────────────────────────
FORM_VIEW_ARCH = """<data>
    <xpath expr="//field[@name='template_type']" position="after">
        <field name="x_is_auto_reply"/>
        <field name="x_trigger_condition" invisible="not x_is_auto_reply"/>
        <field name="x_trigger_keywords" invisible="not x_is_auto_reply or x_trigger_condition != 'keyword'" placeholder="1,hola,tours,info"/>
        <field name="x_body_en" invisible="not x_is_auto_reply" placeholder="English version of the auto-reply body"/>
    </xpath>
    <xpath expr="//button[@name='button_submit_template']" position="attributes">
        <attribute name="invisible">not wa_account_id or status != 'draft' or x_is_auto_reply</attribute>
    </xpath>
</data>"""

FORM_VIEW_NAME = 'whatsapp.template.form.inherit.auto_reply'


# ── Automation server action code ─────────────────────────────────────────────
# This code runs inside Odoo safe_eval when a message is received on discuss.channel.
# It reads whatsapp.template records marked as auto-reply and responds accordingly.
# When keyword "5" is detected, it enters AI recommendation mode.
SERVER_ACTION_CODE = """if record.channel_type == "whatsapp" and record.whatsapp_channel_active:
    nl = chr(10)
    last_msg = env["whatsapp.message"].search([
        ("mail_message_id.res_id", "=", record.id),
        ("mail_message_id.model", "=", "discuss.channel"),
        ("message_type", "=", "inbound"),
    ], order="id desc", limit=1)
    msg_body = ""
    if last_msg:
        raw = str(last_msg.body or "")
        msg_body = raw.replace("<p>", "").replace("</p>", "").replace("<br>", "").replace("<br/>", "").strip()
    msg_lower = msg_body.lower()
    message_count = env["whatsapp.message"].search_count([
        ("mail_message_id.res_id", "=", record.id),
        ("mail_message_id.model", "=", "discuss.channel"),
        ("message_type", "=", "inbound"),
    ])
    # Detect language by phone country code
    phone = record.whatsapp_number or ""
    spanish_prefixes = ("51", "52", "53", "54", "55", "56", "57", "58", "34", "591", "593", "595", "598", "506", "507", "502", "503", "504", "505", "809", "829", "849")
    is_spanish = False
    for prefix in spanish_prefixes:
        if phone.startswith(prefix):
            is_spanish = True
            break
    wa_state = record.x_wa_state or "menu"
    # --- Tour recommendation: awaiting preferences ---
    if wa_state == "awaiting_preferences" and msg_lower not in ("1", "2", "3", "4", "5"):
        record.write({"x_wa_state": "menu"})
        preferences = msg_body
        pref_lower = preferences.lower()
        # Build tour catalog from published ecommerce products
        tour_cat_ids = env["product.public.category"].search([("name", "=", "Tours")]).ids
        child_cats = env["product.public.category"].search([("parent_id", "in", tour_cat_ids)])
        all_cat_ids = tour_cat_ids + child_cats.ids
        tours = env["product.template"].search([
            ("public_categ_ids", "in", all_cat_ids),
            ("is_published", "=", True),
        ])
        # Keyword-category mapping for matching
        cat_keywords = {
            "aventura": ["aventura", "adventure", "trekking", "hiking", "caminata", "extremo", "adrenalina", "deporte"],
            "cultura": ["cultura", "culture", "historia", "history", "museo", "ruinas", "arqueologia", "tradicion", "colonial"],
            "naturaleza": ["naturaleza", "nature", "paisaje", "landscape", "lago", "laguna", "montana", "montania", "montaña"],
            "machupicchu": ["machu", "picchu", "machupicchu", "machu picchu", "inca", "ciudadela"],
            "relax": ["relax", "tranquilo", "descanso", "spa", "termal"],
        }
        # Score tours by keyword relevance
        scored = []
        for t in tours:
            score = 0
            t_name_lower = (t.name or "").lower()
            t_cats = ", ".join(t.public_categ_ids.mapped("name")).lower()
            t_desc = (t.description_sale or "").lower()
            combined = t_name_lower + " " + t_cats + " " + t_desc
            for cat_name, kws in cat_keywords.items():
                for kw in kws:
                    if kw in pref_lower and kw in combined:
                        score += 2
                    elif kw in pref_lower and cat_name in combined:
                        score += 1
            # Boost if tour name partially matches any word in preferences
            for word in pref_lower.split():
                if len(word) > 3 and word in combined:
                    score += 3
            scored.append((score, t))
        scored.sort(key=lambda x: x[0], reverse=True)
        # Pick top 3 (or all if <= 3)
        top_tours = [t for _, t in scored[:3]] if scored else []
        # If no matches, just show first 3 tours
        if not top_tours:
            top_tours = tours[:3]
        # Build response based on language
        if is_spanish:
            reply_lines = ["Basado en tus preferencias, te recomendamos:", ""]
        else:
            reply_lines = ["Based on your preferences, we recommend:", ""]
        for t in top_tours:
            line = "- " + t.name
            if t.list_price:
                line += " (from $" + str(int(t.list_price)) + " USD ref.)" if not is_spanish else " (desde $" + str(int(t.list_price)) + " USD ref.)"
            reply_lines.append(line)
            if t.description_sale:
                desc = str(t.description_sale)[:100]
                if len(str(t.description_sale)) > 100:
                    desc += "..."
                reply_lines.append("  " + desc)
            reply_lines.append("")
        if is_spanish:
            reply_lines.append("Los precios son referenciales y varian segun temporada y tamanio de grupo.")
            reply_lines.append("")
            reply_lines.append("Te interesa alguno? Escribe su nombre para mas detalles, o escribe 2 para una cotizacion personalizada.")
        else:
            reply_lines.append("Prices are referential and vary by season and group size.")
            reply_lines.append("")
            reply_lines.append("Interested in any? Write its name for more details, or type 2 for a custom quote.")
        record.message_post(body=nl.join(reply_lines), message_type="whatsapp_message", subtype_xmlid="mail.mt_comment")
        # Internal note for advisor with full preferences
        note_lines = [
            "SOLICITUD DE RECOMENDACION DE TOUR",
            "",
            "Cliente: " + (record.whatsapp_partner_id.name if record.whatsapp_partner_id else phone or "Desconocido"),
            "Telefono: " + phone,
            "Idioma: " + ("ES" if is_spanish else "EN"),
            "",
            "Preferencias del cliente:",
            preferences,
            "",
            "Tours recomendados automaticamente:",
        ]
        for t in top_tours:
            note_lines.append("- " + t.name + " ($" + str(int(t.list_price)) + ")")
        record.message_post(body=nl.join(note_lines), message_type="comment", subtype_xmlid="mail.mt_note")
    else:
        # --- Standard auto-reply flow ---
        templates = env["whatsapp.template"].search([
            ("x_is_auto_reply", "=", True),
        ])
        replied = False
        for tpl in templates:
            if replied:
                break
            condition = tpl.x_trigger_condition
            # Choose body based on language
            reply_body = tpl.body
            if not is_spanish and tpl.x_body_en:
                reply_body = tpl.x_body_en
            if condition == "first_message" and message_count <= 1:
                record.message_post(body=reply_body, message_type="whatsapp_message", subtype_xmlid="mail.mt_comment")
                replied = True
            elif condition == "keyword" and tpl.x_trigger_keywords and message_count > 1:
                keywords = [k.strip().lower() for k in tpl.x_trigger_keywords.split(",") if k.strip()]
                if msg_lower in keywords:
                    if msg_lower == "5":
                        record.write({"x_wa_state": "awaiting_preferences"})
                    record.message_post(body=reply_body, message_type="whatsapp_message", subtype_xmlid="mail.mt_comment")
                    replied = True
"""

AUTOMATION_NAME = "WhatsApp: Auto-reply Welcome"


# ── Sample auto-reply templates ───────────────────────────────────────────────
SAMPLE_TEMPLATES = [
    {
        'name': 'Auto: Bienvenida',
        'template_name': 'auto_bienvenida',
        'template_type': 'utility',
        'lang_code': 'es',
        'header_type': 'none',
        'model_id': 90,  # res.partner
        'phone_field': 'phone',
        'wa_account_id': WA_ACCOUNT_ID,
        'x_is_auto_reply': True,
        'x_trigger_condition': 'first_message',
        'body': (
            "Hola! Bienvenido/a a A y F Destiny\n\n"
            "Somos una agencia de viajes especializada en tours por Cusco y Peru.\n\n"
            "En que podemos ayudarte?\n"
            "1. Informacion sobre tours\n"
            "2. Cotizacion personalizada\n"
            "3. Estado de mi reserva\n"
            "4. Hablar con un asesor\n"
            "5. Recomendame un tour segun mis gustos\n\n"
            "Escribenos tu consulta y te atenderemos con gusto."
        ),
        'x_body_en': (
            "Hello! Welcome to A y F Destiny\n\n"
            "We are a travel agency specialized in tours around Cusco and Peru.\n\n"
            "How can we help you?\n"
            "1. Tour information\n"
            "2. Custom quote\n"
            "3. Booking status\n"
            "4. Talk to an advisor\n"
            "5. Recommend a tour based on my preferences\n\n"
            "Send us your question and we'll be happy to assist you."
        ),
    },
    {
        'name': 'Auto: Info Tours',
        'template_name': 'auto_info_tours',
        'template_type': 'utility',
        'lang_code': 'es',
        'header_type': 'none',
        'model_id': 90,
        'phone_field': 'phone',
        'wa_account_id': WA_ACCOUNT_ID,
        'x_is_auto_reply': True,
        'x_trigger_condition': 'keyword',
        'x_trigger_keywords': '1',
        'body': (
            "Estos son nuestros tours mas populares:\n\n"
            "- City Tour Cusco (medio dia)\n"
            "- Valle Sagrado (dia completo)\n"
            "- Machu Picchu (dia completo)\n"
            "- Montana de 7 Colores (dia completo)\n"
            "- Laguna Humantay (dia completo)\n"
            "- Tour al Valle Sur (medio dia)\n\n"
            "Tambien ofrecemos paquetes personalizados de varios dias.\n\n"
            "Quieres mas detalles de alguno? Escribenos el nombre del tour que te interesa."
        ),
        'x_body_en': (
            "These are our most popular tours:\n\n"
            "- City Tour Cusco (half day)\n"
            "- Sacred Valley (full day)\n"
            "- Machu Picchu (full day)\n"
            "- Rainbow Mountain (full day)\n"
            "- Humantay Lagoon (full day)\n"
            "- South Valley Tour (half day)\n\n"
            "We also offer custom multi-day packages.\n\n"
            "Want more details? Write the name of the tour you're interested in."
        ),
    },
    {
        'name': 'Auto: Cotizacion',
        'template_name': 'auto_cotizacion',
        'template_type': 'utility',
        'lang_code': 'es',
        'header_type': 'none',
        'model_id': 90,
        'phone_field': 'phone',
        'wa_account_id': WA_ACCOUNT_ID,
        'x_is_auto_reply': True,
        'x_trigger_condition': 'keyword',
        'x_trigger_keywords': '2',
        'body': (
            "Con gusto te preparamos una cotizacion personalizada!\n\n"
            "Por favor indicanos:\n"
            "- Fechas de viaje\n"
            "- Numero de personas\n"
            "- Tours o destinos de interes\n"
            "- Algun requerimiento especial\n\n"
            "Un asesor te respondera con una propuesta a medida."
        ),
        'x_body_en': (
            "We'd be happy to prepare a custom quote for you!\n\n"
            "Please let us know:\n"
            "- Travel dates\n"
            "- Number of people\n"
            "- Tours or destinations of interest\n"
            "- Any special requirements\n\n"
            "An advisor will get back to you with a tailored proposal."
        ),
    },
    {
        'name': 'Auto: Estado Reserva',
        'template_name': 'auto_estado_reserva',
        'template_type': 'utility',
        'lang_code': 'es',
        'header_type': 'none',
        'model_id': 90,
        'phone_field': 'phone',
        'wa_account_id': WA_ACCOUNT_ID,
        'x_is_auto_reply': True,
        'x_trigger_condition': 'keyword',
        'x_trigger_keywords': '3',
        'body': (
            "Para consultar el estado de tu reserva, por favor indicanos:\n\n"
            "- Tu nombre completo\n"
            "- Numero de reserva (si lo tienes)\n\n"
            "Un asesor verificara tu reserva y te respondera a la brevedad."
        ),
        'x_body_en': (
            "To check your booking status, please provide:\n\n"
            "- Your full name\n"
            "- Booking number (if available)\n\n"
            "An advisor will verify your booking and respond shortly."
        ),
    },
    {
        'name': 'Auto: Hablar con Asesor',
        'template_name': 'auto_hablar_asesor',
        'template_type': 'utility',
        'lang_code': 'es',
        'header_type': 'none',
        'model_id': 90,
        'phone_field': 'phone',
        'wa_account_id': WA_ACCOUNT_ID,
        'x_is_auto_reply': True,
        'x_trigger_condition': 'keyword',
        'x_trigger_keywords': '4',
        'body': (
            "Un asesor se comunicara contigo en breve.\n\n"
            "Nuestro horario de atencion es de lunes a sabado, 8:00 AM a 8:00 PM (hora Peru).\n\n"
            "Si es fuera de horario, te responderemos al inicio del siguiente dia laboral."
        ),
        'x_body_en': (
            "An advisor will contact you shortly.\n\n"
            "Our business hours are Monday to Saturday, 8:00 AM to 8:00 PM (Peru time, UTC-5).\n\n"
            "If outside business hours, we'll respond at the start of the next business day."
        ),
    },
    {
        'name': 'Auto: Recomendar Tour',
        'template_name': 'auto_recomendar_tour',
        'template_type': 'utility',
        'lang_code': 'es',
        'header_type': 'none',
        'model_id': 90,
        'phone_field': 'phone',
        'wa_account_id': WA_ACCOUNT_ID,
        'x_is_auto_reply': True,
        'x_trigger_condition': 'keyword',
        'x_trigger_keywords': '5',
        'body': (
            "Excelente! Para recomendarte el tour ideal, cuentanos en un solo mensaje:\n\n"
            "- Que tipo de experiencia buscas? (aventura, cultura, naturaleza, relax)\n"
            "- Fechas aproximadas de viaje\n"
            "- Cuantas personas viajan?\n"
            "- Nacionalidad e idioma preferido\n"
            "- Edades del grupo\n"
            "- Alguna preferencia o restriccion especial?\n\n"
            "Con esta informacion te daremos una recomendacion personalizada!"
        ),
        'x_body_en': (
            "Great! To recommend the ideal tour, tell us in a single message:\n\n"
            "- What kind of experience are you looking for? (adventure, culture, nature, relax)\n"
            "- Approximate travel dates\n"
            "- How many people are traveling?\n"
            "- Ages of the group\n"
            "- Any special preferences or restrictions?\n\n"
            "With this info we'll give you a personalized recommendation!"
        ),
    },
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _get_model_id(client, model_name):
    result = client.execute('ir.model', 'search_read',
        [('model', '=', model_name)], ['id'], 0, 1)
    return result[0]['id'] if result else False


def _field_exists(client, model_name, field_name):
    result = client.execute('ir.model.fields', 'search_read',
        [('model', '=', model_name), ('name', '=', field_name)], ['id'], 0, 1)
    return result[0]['id'] if result else False


def _create_custom_field(client, field_def):
    model_name = field_def['model']
    field_name = field_def['name']

    existing_id = _field_exists(client, model_name, field_name)
    if existing_id:
        return existing_id, False

    model_id = _get_model_id(client, model_name)
    if not model_id:
        return False, False

    vals = {
        'model_id': model_id,
        'name': field_name,
        'field_description': field_def['field_description'],
        'ttype': field_def['ttype'],
        'store': True,
    }
    if 'selection_ids' in field_def:
        vals['selection_ids'] = field_def['selection_ids']

    result = client.execute('ir.model.fields', 'create', [vals])
    field_id = result[0] if isinstance(result, list) else result
    return field_id, True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    client = get_target_client()
    if not client:
        print("ERROR: TARGET_MIGRATION env vars not configured")
        return
    client.connect()
    print(f"Connected to {client.url} (uid={client.uid})")

    # ── 1. Create custom fields ───────────────────────────────────────────
    print("\n1. Custom fields on whatsapp.template")
    for fdef in CUSTOM_FIELDS:
        fid, is_new = _create_custom_field(client, fdef)
        status = 'CREATED' if is_new else 'OK'
        print(f"  [{status}] {fdef['name']}: {fdef['ttype']}")

    # ── 2. Inherit form view ──────────────────────────────────────────────
    print("\n2. Form view inheritance")
    existing_view = client.execute('ir.ui.view', 'search_read',
        [('name', '=', FORM_VIEW_NAME)], ['id'], 0, 1)

    if existing_view:
        view_id = existing_view[0]['id']
        client.execute('ir.ui.view', 'write', [view_id], {'arch': FORM_VIEW_ARCH})
        print(f"  [UPDATED] View ID={view_id}")
    else:
        result = client.execute('ir.ui.view', 'create', [{
            'name': FORM_VIEW_NAME,
            'model': 'whatsapp.template',
            'inherit_id': WA_TEMPLATE_BASE_FORM_VIEW_ID,
            'type': 'form',
            'arch': FORM_VIEW_ARCH,
            'priority': 99,
        }])
        view_id = result[0] if isinstance(result, list) else result
        print(f"  [CREATED] View ID={view_id}")

    # ── 3. Update automation server action code ───────────────────────────
    print("\n3. Automation server action")
    existing_auto = client.execute('base.automation', 'search_read',
        [('name', '=', AUTOMATION_NAME)], ['id', 'action_server_ids'], 0, 1)

    if existing_auto:
        auto_id = existing_auto[0]['id']
        action_ids = existing_auto[0]['action_server_ids']
        if action_ids:
            client.execute('ir.actions.server', 'write', [action_ids[0]], {
                'code': SERVER_ACTION_CODE,
            })
            print(f"  [UPDATED] Server action ID={action_ids[0]}")
        client.execute('base.automation', 'write', [auto_id], {'active': True})
        print(f"  [OK] Automation ID={auto_id} (active)")
    else:
        action_result = client.execute('ir.actions.server', 'create', [{
            'name': AUTOMATION_NAME,
            'model_id': DISCUSS_CHANNEL_MODEL_ID,
            'state': 'code',
            'code': SERVER_ACTION_CODE,
        }])
        action_id = action_result[0] if isinstance(action_result, list) else action_result
        print(f"  [CREATED] Server action ID={action_id}")

        auto_result = client.execute('base.automation', 'create', [{
            'name': AUTOMATION_NAME,
            'model_id': DISCUSS_CHANNEL_MODEL_ID,
            'trigger': 'on_message_received',
            'action_server_ids': [(6, 0, [action_id])],
            'active': True,
        }])
        auto_id = auto_result[0] if isinstance(auto_result, list) else auto_result
        print(f"  [CREATED] Automation ID={auto_id}")

    # ── 4. Delete old marketing template if exists ────────────────────────
    print("\n4. Cleanup old templates")
    old_tpl = client.execute('whatsapp.template', 'search_read',
        [('template_name', '=', 'bienvenida_cliente')], ['id', 'status'], 0, 1)
    if old_tpl:
        tpl_id = old_tpl[0]['id']
        try:
            client.execute('whatsapp.template', 'unlink', [tpl_id])
            print(f"  [DELETED] bienvenida_cliente (ID={tpl_id})")
        except Exception as e:
            print(f"  [SKIP] Cannot delete bienvenida_cliente: {e}")
    else:
        print("  [OK] No old templates to clean")

    # ── 5. Create sample auto-reply templates ─────────────────────────────
    print("\n5. Sample auto-reply templates")
    for tpl_data in SAMPLE_TEMPLATES:
        template_name = tpl_data['template_name']
        existing = client.execute('whatsapp.template', 'search_read',
            [('template_name', '=', template_name), ('wa_account_id', '=', WA_ACCOUNT_ID)],
            ['id', 'status'], 0, 1)

        if existing:
            tpl_id = existing[0]['id']
            # Only update auto-reply specific fields (avoid triggering Meta uniqueness check)
            update_vals = {}
            for key in ('body', 'x_is_auto_reply', 'x_trigger_condition', 'x_trigger_keywords', 'x_body_en'):
                if key in tpl_data:
                    update_vals[key] = tpl_data[key]
            client.execute('whatsapp.template', 'write', [tpl_id], update_vals)
            print(f"  [UPDATED] {tpl_data['name']} (ID={tpl_id})")
        else:
            result = client.execute('whatsapp.template', 'create', [tpl_data])
            tpl_id = result[0] if isinstance(result, list) else result
            print(f"  [CREATED] {tpl_data['name']} (ID={tpl_id})")

    print("\nDone!")
    print("Go to Odoo > WhatsApp > Templates to see the auto-reply templates.")
    print("Templates marked 'Auto-reply Only' are free (not sent to Meta).")


if __name__ == "__main__":
    main()
