"""Setup Website Livechat with AI Agent for tour recommendations.

Configures the im_livechat channel, creates a rule with the AI agent,
customizes the system prompt with the full tour catalog, and adds
the ecommerce as a data source.

Prerequisites:
    - Module `ai_website_livechat` must be installed from Odoo Apps UI
      (this auto-installs: im_livechat, website_livechat, ai_livechat)

Usage:
    PYTHONPATH=. python3 business_units/hotel-trip-agency/e-commerce/livechat/setup_livechat_ai.py
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '.env'))

from odoo_cli.target import get_target_client


# ── IDs ───────────────────────────────────────────────────────────────────────
LIVECHAT_AI_AGENT_ID = 4  # "Livechat AI Agent" created by ai_livechat module
WEBSITE_ID = 1


# ── Livechat channel config ─────────────────────────────────────────────────
LIVECHAT_CONFIG = {
    'name': 'A y F Destiny - Asistente de Tours',
    'button_text': 'Chatea con nosotros',
    'default_message': 'Hola! Soy el asistente virtual de A y F Destiny. En que puedo ayudarte?',
    'header_background_color': '#1B5E20',
    'button_background_color': '#1B5E20',
    'title_color': '#FFFFFF',
    'button_text_color': '#FFFFFF',
}


# ── AI Agent system prompt ───────────────────────────────────────────────────
SYSTEM_PROMPT_TEMPLATE = '''## Identity
- You are the virtual travel assistant of **A y F Destiny**, a travel agency based in Cusco, Peru.
- You specialize in tours throughout Cusco and Peru.
- Always respond in the same language the customer uses (Spanish by default, English if they write in English).
- Your name is "Asistente A y F Destiny".

## Conversation Flow
When a visitor starts a conversation or asks about tours, follow this flow:

### Step 1: Welcome and gather preferences
Greet warmly and ask for the following information (you can ask in 1-2 messages, not all at once):
1. **Nationality and language** - "De donde nos visitas? / Where are you visiting from?"
2. **Travel dates** - "Que fechas tienes planeadas para tu viaje?"
3. **Group composition** - "Cuantas personas viajan? Hay ninos o adultos mayores?"
4. **Ages** - "Cuales son las edades del grupo?"
5. **Interests** - "Que tipo de experiencia buscan? (aventura, cultura, naturaleza, relax, Machu Picchu)"
6. **Special requirements** - "Tienen alguna restriccion alimentaria, de movilidad, o requerimiento especial?"
7. **Budget** - "Tienen un presupuesto aproximado en mente?"

You do NOT need to ask all questions before making a recommendation. Adapt based on what the visitor shares. If they already mention some preferences, skip those questions.

### Step 2: Recommend tours
Based on the collected preferences, recommend 1-3 tours from the catalog below. For each recommendation:
- Explain WHY it matches their preferences
- Include the reference price
- Mention duration (if in the name: medio dia, dia completo, 2D/1N, etc.)
- Suggest complementary tours if applicable

### Step 3: Capture lead
If the visitor shows interest in booking or wants a detailed quote:
- Collect their name, email, and phone number
- Create a lead using the Lead Creation tools
- Let them know an advisor will contact them with a personalized quote

## Important Rules
- Prices are REFERENTIAL and vary by season and group size. Always mention this.
- Do NOT invent tours that are not in the catalog.
- If unsure about something, say so and offer to connect with a human advisor.
- Be concise but warm. Use short paragraphs.
- For multi-day packages (like Cusco Magico 4D/3N), explain what is included if you know.
- Recommend the "Cotizacion personalizada" path for groups > 6 people or complex itineraries.

## Tour Catalog
{catalog}

## Contact Information
- Company: A y F Destiny E.I.R.L.
- Location: Cusco, Peru
- Website: https://machupicchu-afdestiny-production.odoo.com
- Hours: Monday to Saturday, 8:00 AM to 8:00 PM (Peru time, UTC-5)
- WhatsApp: +51 987 318 885
'''


def _build_tour_catalog(client):
    """Query published tour products and build a text catalog."""
    tour_cat_ids = client.execute(
        'product.public.category', 'search', [('name', '=', 'Tours')])
    child_cats = client.execute(
        'product.public.category', 'search', [('parent_id', 'in', tour_cat_ids)])
    all_cat_ids = tour_cat_ids + child_cats

    tours = client.execute('product.template', 'search_read', [
        ('public_categ_ids', 'in', all_cat_ids),
        ('is_published', '=', True),
    ], ['name', 'list_price', 'public_categ_ids', 'description_sale'])

    cat_data = client.execute(
        'product.public.category', 'search_read',
        [('id', 'in', all_cat_ids)], ['name'])
    cat_map = {c['id']: c['name'] for c in cat_data}

    lines = []
    for t in tours:
        cats = [cat_map.get(cid, '') for cid in t.get('public_categ_ids', [])]
        cat_str = ', '.join([c for c in cats if c])
        desc = (t.get('description_sale') or '')[:80]
        line = f"- {t['name']} (USD {int(t['list_price'])})"
        if cat_str:
            line += f" [{cat_str}]"
        if desc:
            line += f" - {desc}"
        lines.append(line)

    return '\n'.join(lines), len(tours)


def main():
    client = get_target_client()
    if not client:
        print("ERROR: TARGET_MIGRATION env vars not configured")
        return
    client.connect()
    print(f"Connected to {client.url} (uid={client.uid})")

    # ── 1. Check if livechat module is installed ─────────────────────────
    print("\n1. Checking module installation")
    modules = client.execute('ir.module.module', 'search_read',
        [('name', '=', 'ai_website_livechat')], ['state'], 0, 1)
    if not modules or modules[0]['state'] != 'installed':
        print("  [ERROR] Module 'ai_website_livechat' is not installed!")
        print("  Install it from: Odoo > Apps > search 'AI Website Livechat'")
        return
    print("  [OK] ai_website_livechat is installed")

    # ── 2. Configure livechat channel ────────────────────────────────────
    print("\n2. Livechat channel")
    channels = client.execute('im_livechat.channel', 'search', [])
    if channels:
        channel_id = channels[0]
        client.execute('im_livechat.channel', 'write', [channel_id], LIVECHAT_CONFIG)
        print(f"  [UPDATED] Channel ID={channel_id}")
    else:
        result = client.execute('im_livechat.channel', 'create', [LIVECHAT_CONFIG])
        channel_id = result[0] if isinstance(result, list) else result
        print(f"  [CREATED] Channel ID={channel_id}")

    # ── 3. Add operator (admin user) ─────────────────────────────────────
    print("\n3. Operators")
    lc = client.execute('im_livechat.channel', 'search_read',
        [('id', '=', channel_id)], ['user_ids'])
    if client.uid not in lc[0].get('user_ids', []):
        client.execute('im_livechat.channel', 'write',
            [channel_id], {'user_ids': [(4, client.uid)]})
        print(f"  [ADDED] User {client.uid} as operator")
    else:
        print(f"  [OK] User {client.uid} already an operator")

    # ── 4. Create/update rule with AI agent ──────────────────────────────
    print("\n4. Livechat rule")
    existing_rules = client.execute('im_livechat.channel.rule', 'search_read',
        [('channel_id', '=', channel_id)], ['id', 'ai_agent_id'], 0, 1)

    if existing_rules:
        rule_id = existing_rules[0]['id']
        client.execute('im_livechat.channel.rule', 'write', [rule_id], {
            'action': 'auto_popup',
            'auto_popup_timer': 15,
            'ai_agent_id': LIVECHAT_AI_AGENT_ID,
            'regex_url': '',
        })
        print(f"  [UPDATED] Rule ID={rule_id}")
    else:
        result = client.execute('im_livechat.channel.rule', 'create', [{
            'channel_id': channel_id,
            'action': 'auto_popup',
            'auto_popup_timer': 15,
            'ai_agent_id': LIVECHAT_AI_AGENT_ID,
            'regex_url': '',
        }])
        rule_id = result[0] if isinstance(result, list) else result
        print(f"  [CREATED] Rule ID={rule_id}")

    # ── 5. Build tour catalog and update AI agent prompt ─────────────────
    print("\n5. AI Agent system prompt")
    catalog, tour_count = _build_tour_catalog(client)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(catalog=catalog)

    client.execute('ai.agent', 'write', [LIVECHAT_AI_AGENT_ID], {
        'system_prompt': system_prompt,
        'name': 'A y F Destiny - Asistente de Tours',
    })
    print(f"  [UPDATED] Agent ID={LIVECHAT_AI_AGENT_ID} ({tour_count} tours, {len(system_prompt)} chars)")

    # ── 6. Add ecommerce as data source ──────────────────────────────────
    print("\n6. AI Agent data source")
    existing_sources = client.execute('ai.agent.source', 'search_read',
        [('agent_id', '=', LIVECHAT_AI_AGENT_ID)], ['id', 'url'], 0, 5)
    shop_url = 'https://machupicchu-afdestiny-production.odoo.com/shop'
    has_shop = any(s.get('url') == shop_url for s in existing_sources)

    if has_shop:
        print(f"  [OK] Ecommerce source already exists")
    else:
        try:
            result = client.execute('ai.agent.source', 'create', [{
                'agent_id': LIVECHAT_AI_AGENT_ID,
                'type': 'url',
                'url': shop_url,
                'name': 'Ecommerce - Tours',
            }])
            src_id = result[0] if isinstance(result, list) else result
            print(f"  [CREATED] Source ID={src_id}")
        except Exception as e:
            print(f"  [SKIP] Source creation failed: {e}")

    # ── 7. Verify website link ───────────────────────────────────────────
    print("\n7. Website link")
    websites = client.execute('website', 'search_read',
        [('id', '=', WEBSITE_ID)], ['channel_id'])
    if websites and websites[0].get('channel_id'):
        print(f"  [OK] Website linked to channel: {websites[0]['channel_id']}")
    else:
        client.execute('website', 'write', [WEBSITE_ID], {'channel_id': channel_id})
        print(f"  [LINKED] Website {WEBSITE_ID} -> Channel {channel_id}")

    print("\nDone!")
    print(f"Livechat is active on your website with AI agent (GPT-4o).")
    print(f"Test in incognito: https://machupicchu-afdestiny-production.odoo.com/shop")
    print(f"The chat button should appear in the bottom-right corner after 15 seconds.")


if __name__ == "__main__":
    main()
