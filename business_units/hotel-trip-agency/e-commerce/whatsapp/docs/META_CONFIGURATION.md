# Meta WhatsApp Business - Configuration Reference

Generic guide for configuring WhatsApp Business Cloud API with Odoo 19 SaaS.

## Account Details

- **App UID**: `<YOUR_APP_UID>`
- **Phone Number UID**: `<YOUR_PHONE_UID>`
- **WABA ID**: `<YOUR_WABA_ID>`
- **Phone**: `<YOUR_PHONE_NUMBER>`
- **App Status**: Live (published)

## Console URLs

- App Dashboard: `https://developers.facebook.com/apps/<YOUR_APP_UID>/`
- WhatsApp Config: `https://developers.facebook.com/apps/<YOUR_APP_UID>/whatsapp-business/wa-dev-console/`
- Business Settings: `https://business.facebook.com/settings/`
- System Users: `https://business.facebook.com/settings/system-users/`

## Step-by-step Setup

### 1. Create Meta App

1. Go to `https://developers.facebook.com/apps/`
2. Click **Create App** > Type: **Business**
3. Add the **WhatsApp** product to the app
4. Take note of the **App UID** from the URL

### 2. Register Phone Number

1. In Meta Developer Console > WhatsApp > API Setup
2. Click **Add phone number** and enter your business phone
3. Verify ownership via SMS/call code through the Meta UI
4. Take note of the **Phone Number UID** shown in the console
5. Register the phone via API (Cloud API does NOT have `request_code`/`verify_code` endpoints):

```bash
curl -X POST "https://graph.facebook.com/v25.0/<YOUR_PHONE_UID>/register" \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"messaging_product":"whatsapp","pin":"<YOUR_2FA_PIN>"}'
```

6. Response should be `{"success": true}`
7. Phone status changes to "Conectado" in Meta Business Suite

### 3. Create System User and Generate Permanent Token

**IMPORTANT**: Do NOT use the temporary "API Setup" token for production. It expires in ~24 hours.

1. Go to **Meta Business Suite** > **Settings** > **Business Settings**
2. In the left sidebar, click **System Users** (under "Users")
3. Click **Add** to create a new system user:
   - Name: e.g. "Odoo WhatsApp Integration"
   - Role: **Admin**
4. Click on the created system user
5. Click **Add Assets**:
   - Select your **WhatsApp Business Account**
   - Grant **Full Control**
6. Click **Generate New Token**:
   - Select your app (the one created in step 1)
   - Check these permissions:
     - `whatsapp_business_management`
     - `whatsapp_business_messaging`
   - Click **Generate Token**
7. **Copy the token immediately** - it won't be shown again
8. This is a **permanent token** that does not expire

### 4. Get the App Secret

1. Go to Meta Developer Console > **App Settings** > **Basic**
2. Next to **App Secret**, click **Show**
3. Copy the secret - you'll need it for Odoo's webhook verification

### 5. Configure Webhooks

1. In Meta Developer Console > WhatsApp > Configuration
2. Ensure the **Callback URL** points to your Odoo instance (Odoo configures this automatically when you save the WhatsApp account)
3. Subscribe the `messages` webhook field:
   - Go to Webhook fields table
   - Ensure `messages` has a **green checkmark** (subscribed)
   - If not, click Subscribe

### 6. Subscribe App to WABA

This is a critical step that is often missed. The WABA ID is found in Meta Business Suite > WhatsApp Manager > Settings.

Verify current subscription:
```bash
curl -X GET "https://graph.facebook.com/v25.0/<YOUR_WABA_ID>/subscribed_apps" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

If response is `{"data": []}` (empty), subscribe:
```bash
curl -X POST "https://graph.facebook.com/v25.0/<YOUR_WABA_ID>/subscribed_apps" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

Expected response: `{"success": true}`

### 7. Publish the App (Go Live)

The app must be in **Live mode** for webhooks to work in production.
Meta requires a Privacy Policy URL and Terms of Service URL before publishing.

#### 7.1 Create a Privacy Policy page on your website

If you don't have one, create a `/privacy` page in your Odoo website:

1. Go to **Website > Pages > New Page**
2. Set URL as `/privacy`
3. Add your company's privacy policy content (data collection, usage, third-party sharing, WhatsApp data handling, contact info)
4. **Publish** the page

Minimum content the privacy policy should cover:
- What personal data is collected (name, phone, email, messages)
- How it is used (customer service, tour recommendations, bookings)
- Third-party services involved (WhatsApp/Meta, Odoo)
- Data retention policy
- Contact information for privacy inquiries
- Company legal name, RUC/tax ID, and address

#### 7.2 Configure in Meta and publish

1. Meta Developer Console > **App Settings** > **Basic**
2. Fill in the required fields:
   - **Privacy Policy URL**: `https://<YOUR_ODOO_DOMAIN>/privacy`
   - **Terms of Service URL**: `https://<YOUR_ODOO_DOMAIN>/privacy` (can be the same page)
   - **App Icon**: upload your company logo
   - **Category**: Business and Pages
3. Click **Save Changes**
4. At the top of the page, toggle the app from **Development** to **Live**
5. Confirm in the dialog

**Note**: If the toggle is grayed out, check the **App Review** section for missing requirements. Common issues:
- Privacy Policy URL returns 404 (page not published)
- Missing business verification
- App permissions not configured

### 8. Configure in Odoo

1. Go to **WhatsApp > Configuration > WhatsApp Business Accounts**
2. Create or edit the account with:

| Field | Value | Where to find |
|-------|-------|---------------|
| App UID | `<YOUR_APP_UID>` | Developer Console URL |
| Phone Number UID | `<YOUR_PHONE_UID>` | WhatsApp > API Setup |
| WABA ID | `<YOUR_WABA_ID>` | Business Suite > WhatsApp Manager |
| Token | `<SYSTEM_USER_TOKEN>` | Step 3 (permanent token) |
| App Secret | `<APP_SECRET>` | Step 4 |

3. Save - Odoo will automatically configure the webhook callback URL

## Token Reference

| Token Type | Where to Find | Expiration | Use |
|------------|---------------|------------|-----|
| **System User Token** | Business Settings > System Users > Generate Token | **Never** (permanent) | Production - use in Odoo |
| API Setup Token | Developer Console > WhatsApp > API Setup | ~24 hours | Testing only, do NOT use in production |
| App Secret | Developer Console > App Settings > Basic | Never | Odoo webhook verification |

## Troubleshooting

### Messages not arriving in Odoo
1. Check `messages` webhook field is subscribed (step 5)
2. App must be in **Live** mode, not Development (step 7)
3. WABA must be subscribed (step 6) - `POST /<WABA_ID>/subscribed_apps`
4. Privacy policy URL must be set in app settings

### "Object with ID does not exist" error
- The phone number may not be properly registered
- Run the `/register` endpoint again (step 2)

### "Unsupported post request" / "request_code nonexisting field"
- `request_code` and `verify_code` are **On-Premises API** endpoints (v1)
- They do **NOT exist** in **Cloud API** (which Odoo uses)
- Verify the phone via the Meta UI, then use `/register` only

### Auto-reply appears in Odoo but not on phone
- Verify `message_type='whatsapp_message'` in server action code
- `'comment'` only posts internally in Discuss, does not send to WhatsApp

### Token expired / Invalid token
- If using API Setup token: it expired, generate a System User token instead (step 3)
- If System User token: regenerate from Business Settings > System Users

### Webhook not delivering after app is Live
- Verify WABA subscription (step 6) - this is the most commonly missed step
- Check that both `whatsapp_business_management` and `whatsapp_business_messaging` permissions are on the token
