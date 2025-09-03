# Twilio Messaging Service Setup

## Quick Fix for "Messaging Service SID not configured" Error

### Step 1: Create Messaging Service in Twilio

1. Go to [Twilio Console > Messaging > Services](https://console.twilio.com/us1/develop/sms/services)
2. Click "Create Messaging Service"
3. Fill in:
   - **Service Name**: `NinaBot WhatsApp Service`
   - **Use Case**: Select "Conversations" or "Mixed"
4. Click "Create Messaging Service"

### Step 2: Add Your WhatsApp Number to the Service

1. In the Messaging Service you just created, go to **"Senders"** tab
2. Click "Add Senders"
3. Select "WhatsApp Sender"
4. Choose your WhatsApp number: `+573232524537`
5. Click "Add WhatsApp Senders"

### Step 3: Get the Service SID

1. In your Messaging Service dashboard, you'll see the **Service SID** (starts with `MG...`)
2. Copy this SID

### Step 4: Add to Heroku Config

Run this command in your terminal:

```bash
heroku config:set TWILIO_MESSAGING_SERVICE_SID=MGyour_service_sid_here --app residere
```

Replace `MGyour_service_sid_here` with the actual Service SID you copied.

### Step 5: Verify the Setup

After setting the config variable, test the campaign again. The error should be resolved.

## Alternative: Quick Setup via Heroku Dashboard

1. Go to your [Heroku Dashboard](https://dashboard.heroku.com/apps/residere)
2. Click on your app → Settings
3. Click "Reveal Config Vars"
4. Add new config variable:
   - **KEY**: `TWILIO_MESSAGING_SERVICE_SID`
   - **VALUE**: Your Messaging Service SID (starts with `MG...`)
5. Click "Add"

## Why This is Required

WhatsApp Business API requires all template messages to be sent through a Messaging Service. This is a Twilio requirement for WhatsApp campaigns to ensure proper compliance and delivery tracking.

Once configured, your campaigns will work properly! 