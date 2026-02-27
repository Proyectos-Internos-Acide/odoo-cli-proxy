# Website Livechat AI - Setup Guide

## Overview

AI-powered live chat widget on the ecommerce website. Uses Odoo's built-in AI module
with GPT-4o to recommend tours, answer questions, and create CRM leads automatically.

## Architecture

```
Website Visitor  -->  Livechat Widget (JS)  -->  Odoo Livechat Channel
                                                        |
                                                  AI Agent (GPT-4o)
                                                   /          \
                                          System Prompt     Topic: Create Leads
                                          (Tour Catalog)    (CRM integration)
                                                              |
                                                          crm.lead
```

## Prerequisites

### Module Installation (from Odoo UI)
Install `AI Website Livechat` from **Apps** menu. This auto-installs:
- `im_livechat` - Live Chat core
- `website_livechat` - Website integration
- `ai_livechat` - AI capabilities for livechat

### Required Odoo modules (already installed)
- `ai` + `ai_app` - AI core
- `ai_website` - AI website integration

## Key IDs (Production)

| Resource | ID |
|----------|-----|
| Livechat Channel (im_livechat.channel) | 1 |
| Livechat Rule (im_livechat.channel.rule) | 1 |
| AI Agent (ai.agent) | 4 |
| AI Source (ai.agent.source) | 1 |
| Website (website) | 1 |
| AI Topic: Create Leads | 3 |

## Configuration Details

### Livechat Channel
- **Name**: A y F Destiny - Asistente de Tours
- **Button text**: Chatea con nosotros
- **Default message**: Hola! Soy el asistente virtual de A y F Destiny...
- **Colors**: Green (#1B5E20) header and button
- **Auto-popup**: 15 seconds on all pages

### AI Agent
- **Model**: GPT-4o
- **Name**: A y F Destiny - Asistente de Tours
- **Topics**: Create Leads (auto-creates CRM leads)
- **Source**: Ecommerce URL (/shop)
- **System Prompt**: Includes full tour catalog (28 products with prices)

### Conversation Flow
The AI agent follows this flow:
1. **Welcome & gather preferences**: nationality, dates, group size, ages, interests, restrictions, budget
2. **Recommend 1-3 tours**: from the catalog, explaining why each matches
3. **Capture lead**: if interested in booking, collects contact info and creates CRM lead

### Lead Creation
The AI automatically creates leads in CRM > Pipeline when:
- Visitor requests a quote
- Visitor says "contact me", "want to book", etc.
- AI cannot resolve the query with confidence
- Visitor shares contact details proactively

## Operators

At least one operator must be assigned to the livechat channel for the widget to appear.
The AI handles conversations, but Odoo requires an available operator.

**Important**: If testing while logged in as the operator, the chat widget may not appear.
Test in an **incognito window** without logging in.

To manage operators: **Live Chat > Channels > Operators tab**

## Running the Setup Script

```bash
cd /path/to/py-odoo-cli
PYTHONPATH=. python3 business_units/hotel-trip-agency/e-commerce/livechat/setup_livechat_ai.py
```

The script:
1. Verifies `ai_website_livechat` module is installed
2. Configures the livechat channel (name, texts, colors)
3. Adds admin user as operator
4. Creates/updates rule with AI agent
5. Queries all published tour products and builds the system prompt
6. Adds ecommerce as AI data source
7. Verifies website is linked to the channel

The script is idempotent - safe to run multiple times.

## Updating the Tour Catalog

When tours are added/removed/repriced, re-run the setup script to update the AI agent's
system prompt with the latest catalog:

```bash
PYTHONPATH=. python3 business_units/hotel-trip-agency/e-commerce/livechat/setup_livechat_ai.py
```

The script queries `product.template` records published in the Tours ecommerce category
and rebuilds the catalog section of the system prompt.

## Troubleshooting

### Chat widget not appearing
1. Check operator is assigned: **Live Chat > Channels > Operators**
2. Test in incognito (widget hidden for operators)
3. Verify website is linked: `website.channel_id` must point to the livechat channel

### "No human agents available"
- At least one operator must be logged into Odoo and "joined" to the livechat channel
- Go to **Live Chat** app and click "Join" on the channel

### AI not responding
- Check AI agent configuration in **Settings > AI**
- Verify the AI model (GPT-4o) is available and configured
- Check system prompt is not empty
