# WhatsApp Template Setup Guide

## Issue Resolution: Error 63016 - Template Required

The error you encountered occurs because WhatsApp requires approved message templates for outbound campaigns sent outside the 24-hour conversation window.

## Required Steps

### 1. Get Your Template Content SID

1. Go to [Twilio Console > Content Template Builder](https://console.twilio.com/us1/develop/sms/content-template-builder)
2. Find your `outgreet` template in the list
3. Click on the template name
4. Copy the **Content SID** (starts with `HX...`)

### 2. Set Up Messaging Service (if not already done)

1. Go to [Twilio Console > Messaging > Services](https://console.twilio.com/us1/develop/sms/services)
2. Create a new Messaging Service or use existing one
3. Add your WhatsApp sender (+573232524537) to the service
4. Copy the **Service SID** (starts with `MG...`)

### 3. Configure Environment Variables

Add these environment variables to your Heroku app:

```bash
# Set via Heroku CLI or Dashboard
heroku config:set TWILIO_OUTGREET_CONTENT_SID=HXyour_content_sid_here
heroku config:set TWILIO_MESSAGING_SERVICE_SID=MGyour_service_sid_here
```

Or via Heroku Dashboard:
1. Go to your app settings
2. Click "Reveal Config Vars"
3. Add:
   - `TWILIO_OUTGREET_CONTENT_SID`: Your template Content SID
   - `TWILIO_MESSAGING_SERVICE_SID`: Your Messaging Service SID

### 4. Verify Template Status

Ensure your `outgreet` template is **APPROVED** in the Twilio Console:
1. Go to Content Template Builder
2. Check the status column shows "Approved"
3. If it shows "Pending" or "Rejected", you'll need to wait for approval or resubmit

## Template Information

Your approved template:
- **Name**: `outgreet`
- **Content**: 
  ```
  Hola, soy Valeria Mercado de Artek Mar.
  ¡Me encantaría presentarte nuestro nuevo proyecto en Altos de Los Rosales, Barranquilla!
  ¿Te gustaría conocer más detalles?
  ```
- **Category**: MARKETING (or UTILITY)

## How It Works Now

✅ **Before**: Sending freeform messages → Error 63016
✅ **After**: Using approved template → Messages sent successfully

The system will now:
1. Detect outbound campaigns (`campaign_id` present)
2. Use the approved `outgreet` template with Content SID
3. Send via Messaging Service (required for templates)
4. Log successful deliveries

## Testing

Once configured, test with a single number first:
1. Use the "Test Send" button in the campaign interface
2. Check Twilio logs for successful delivery
3. Verify the message is received with the template content

## Important Notes

- Templates are required for messages sent outside 24-hour windows
- Freeform messages only work within 24 hours of user's last message
- Template approval usually takes a few minutes to hours
- Cost is based on template category (Marketing templates cost more)

## Troubleshooting

If you still get errors:
1. Check template is APPROVED status
2. Verify Content SID is correct (starts with HX)
3. Ensure Messaging Service includes your WhatsApp sender
4. Check environment variables are set correctly in Heroku 