# WhatsApp Business API - Setup Guide

## Overview

Integration of WhatsApp Business Cloud API with Odoo 19 SaaS for A & F Destiny travel agency.
Messages within the 24h customer service window are FREE (no Meta template charges).

## Architecture

```
Customer Phone  -->  Meta Cloud API (webhook)  -->  Odoo (discuss.channel)
                                                         |
                                                    base.automation
                                                    (on_message_received)
                                                         |
                                                    Server Action
                                                    (safe_eval code)
                                                         |
                                              whatsapp.template records
                                              (x_is_auto_reply = True)
```

## Prerequisites

### Meta Developer Setup

1. **Create Meta App**: https://developers.facebook.com/apps/
   - Type: Business
   - Add WhatsApp product

2. **Register Phone Number**:
   - Phone: +51 987 318 885
   - Verify via Meta UI (NOT via API - `request_code` endpoint doesn't exist in Cloud API)
   - Register: `POST /{phone_number_id}/register` with `messaging_product` and `pin`

3. **System User Token** (permanent, NOT the temporary API Setup token):
   - Go to: Meta Business Suite > Settings > Business Settings > System Users
   - Create system user with permissions:
     - `whatsapp_business_management`
     - `whatsapp_business_messaging`
   - Generate permanent token

4. **Webhook Configuration**:
   - Subscribe `messages` field in Meta Developer Console > WhatsApp > Configuration
   - App must be in **Live mode** (not Development)
   - Subscribe app to WABA: `POST /{waba_id}/subscribed_apps`

5. **Privacy Policy**:
   - Required by Meta to publish the app
   - Created at `/privacy` on the Odoo website (view ID=2301)

### Odoo Configuration

1. Go to **WhatsApp > Configuration > WhatsApp Business Accounts**
2. Create account with:
   - App UID: 2343881842792492
   - Phone UID: 978937985305831
   - WABA ID: 1183670950508522
   - Token: System User permanent token

## Key IDs (Production)

| Resource | ID |
|----------|-----|
| WhatsApp Account | 2 |
| Automation (base.automation) | 31 |
| Server Action (ir.actions.server) | 1221 |
| Inherited Form View (ir.ui.view) | 4897 |
| Base Form View | 4562 |
| discuss.channel model | 228 |

### Auto-reply Templates

| ID | Name | Trigger | Keywords |
|----|------|---------|----------|
| 16 | Auto: Bienvenida | first_message | - |
| 17 | Auto: Info Tours | keyword | 1 |
| 18 | Auto: Cotizacion | keyword | 2 |
| 19 | Auto: Estado Reserva | keyword | 3 |
| 22 | Auto: Hablar con Asesor | keyword | 4 |
| 21 | Auto: Recomendar Tour | keyword | 5 |

## Custom Fields Created

### On `whatsapp.template`
- `x_is_auto_reply` (boolean) - Marks template as local auto-reply (not sent to Meta)
- `x_trigger_condition` (selection: first_message, keyword) - When to trigger
- `x_trigger_keywords` (char) - Comma-separated keywords to match

### On `discuss.channel`
- `x_wa_state` (selection: menu, awaiting_preferences) - Conversation state tracking

## How Auto-replies Work

1. Customer sends message via WhatsApp
2. Meta webhook delivers to Odoo -> creates `discuss.channel` with `channel_type=whatsapp`
3. `base.automation` triggers `on_message_received`
4. Server action reads last inbound `whatsapp.message`, strips HTML
5. Matches against `whatsapp.template` records with `x_is_auto_reply=True`:
   - **first_message**: responds only on first inbound message
   - **keyword**: matches `msg_body.lower()` against `x_trigger_keywords`
6. Posts reply with `message_type='whatsapp_message'` (critical - `'comment'` only posts internally)

### Option 5 - Tour Recommendation
- Keyword "5" sets `x_wa_state='awaiting_preferences'` on the channel
- Next non-keyword message triggers keyword-based tour matching against published products
- Returns top 3 tours + posts internal note for advisor

## Important Technical Notes

- `message_type='whatsapp_message'` is required to send via WhatsApp (not `'comment'`)
- `safe_eval` restrictions: no `import`, no `Markup`, use `chr(10)` for newlines
- Use `.replace()` for HTML stripping (no `re` module available)
- `create` returns a list in Odoo 19 - extract with `result[0] if isinstance(result, list) else result`
- Responses within 24h customer service window are FREE
- Marketing/Utility templates submitted to Meta COST MONEY

## Running the Setup Script

```bash
cd /path/to/py-odoo-cli
PYTHONPATH=. python3 business_units/hotel-trip-agency/e-commerce/whatsapp/setup_whatsapp_templates.py
```

The script is idempotent - safe to run multiple times.
