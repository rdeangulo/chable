# 📊 NinaBot Analytics & Outbound Campaign System

This document explains the new real-time analytics and outbound campaign features integrated with Twilio WhatsApp.

## 🚀 Features

### Real-Time Analytics
- **Conversation Tracking**: Live monitoring of all WhatsApp conversations
- **Lead Analytics**: Automatic lead qualification and scoring
- **Response Time Metrics**: Track assistant and agent response times
- **Keyword Analysis**: Monitor which keywords drive the most leads
- **Platform Performance**: Compare performance across WhatsApp, Instagram, etc.
- **Conversion Tracking**: Real conversion rates from conversations to qualified leads

### Outbound Campaigns
- **WhatsApp Marketing**: Send approved template messages via Twilio
- **Contact Management**: Import and manage contact lists
- **Campaign Tracking**: Real-time delivery and response tracking
- **Message Logging**: Complete audit trail of all messages
- **Response Integration**: Automatically convert responses to conversations

## 📋 Heroku Setup Instructions

### 1. Deploy Migration

The new analytics tables are included in the Alembic migration. Deploy to Heroku:

```bash
# Commit the migration
git add .
git commit -m "Add analytics and campaign tables migration"
git push heroku main

# Run the migration on Heroku
heroku run alembic upgrade head
```

### 2. Configure Twilio on Heroku

Set your Twilio credentials as Heroku config vars:

```bash
heroku config:set TWILIO_ACCOUNT_SID=your_account_sid_here
heroku config:set TWILIO_AUTH_TOKEN=your_auth_token_here
heroku config:set TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 3. Optional: Create Sample Data

For testing, you can populate sample analytics data:

```bash
heroku run python populate_sample_analytics.py
```

### 4. Verify Deployment

Check that the tables were created successfully:

```bash
heroku pg:psql -c "\dt"
```

You should see the new tables:
- `campaign_analytics`
- `outbound_campaigns` 
- `campaign_messages`
- `message_logs`
- `analytics_keywords`
- `contact_lists`
- `contact_list_members`

### 5. Set Up Webhook (Optional)

For real-time message status updates, configure a Twilio webhook:

**Webhook URL**: `https://your-heroku-app.herokuapp.com/api/monitor/webhook/twilio`

**Events to Track**:
- Message Status Updates
- Delivery Receipts
- Response Tracking

## 🎯 Using the System

### Analytics Dashboard

1. **Navigate to Analytics**: Click the "Analytics" tab in the monitor interface
2. **View Metrics**: See real-time conversation and lead metrics
3. **Keyword Analysis**: Monitor which terms drive the most engagement
4. **Platform Performance**: Compare WhatsApp vs other channels

### Outbound Campaigns

1. **Create Contact Lists**: 
   - Manual entry: Add phone numbers one by one
   - CSV Upload: Bulk import contacts from spreadsheet
   - API Integration: Import from external systems

2. **Design Campaigns**:
   - Use pre-approved WhatsApp templates
   - Target specific contact lists
   - Schedule delivery times
   - Set throttling to avoid spam

3. **Launch & Monitor**:
   - Real-time delivery tracking
   - Response rate monitoring
   - Automatic lead generation from responses

## 📱 WhatsApp Integration

### Message Template

The system includes a pre-approved template:
```
Hola, soy Valeria Mercado de Artek Mar.
¡Me encantaría presentarte nuestro nuevo proyecto en Altos de Los Rosales, Barranquilla!
¿Te gustaría conocer más detalles?
```

### Response Handling

When recipients respond to campaigns:
1. **Automatic Threading**: Responses create conversation threads
2. **Lead Qualification**: AI analyzes responses for buying intent
3. **Agent Handoff**: High-quality leads can be assigned to agents
4. **CRM Integration**: Qualified leads automatically sync to your CRM

## 📈 Analytics Endpoints

### Real Data API Endpoints

- `GET /api/monitor/analytics/conversation?days=7` - Conversation analytics
- `GET /api/monitor/analytics/campaigns?days=7` - Campaign performance
- `GET /api/monitor/analytics/keywords?days=7` - Keyword analysis
- `POST /api/monitor/outbound/campaign` - Create and send campaigns
- `GET /api/monitor/outbound/campaigns` - Get campaign history
- `POST /api/monitor/outbound/contact-lists` - Create contact lists

### Data Collection

The system automatically tracks:
- **Message Volume**: All inbound/outbound messages
- **Response Times**: Time between user message and AI response
- **Lead Conversion**: Conversation → Qualified Lead pipeline
- **Campaign Performance**: Delivery rates, open rates, responses
- **Keyword Mentions**: Real estate terms and their conversion rates

## 🔧 Technical Details

### Database Schema

**Message Logging**:
```sql
message_logs (
    id, message_sid, direction, from_number, to_number,
    message_body, message_status, platform, thread_id,
    campaign_id, response_time, created_at
)
```

**Campaign Tracking**:
```sql
outbound_campaigns (
    id, campaign_name, message_template, total_recipients,
    messages_sent, messages_delivered, responses_received,
    leads_generated, campaign_status, created_at
)
```

**Analytics Aggregation**:
```sql
campaign_analytics (
    id, date, total_conversations, qualified_leads,
    avg_response_time, active_conversations, conversion_rate,
    platform_breakdown, created_at
)
```

### Twilio Integration

**TwilioService Class**:
- `send_message()` - Send individual WhatsApp messages
- `send_campaign()` - Send bulk campaign messages with throttling
- `process_webhook()` - Handle status updates from Twilio
- `log_message()` - Record all messages for analytics

**AnalyticsService Class**:
- `get_conversation_analytics()` - Real-time conversation metrics
- `get_campaign_analytics()` - Campaign performance data
- `get_keyword_analytics()` - Keyword mention analysis
- `update_daily_analytics()` - Daily aggregation (run via cron)

### Security Features

- **Number Validation**: Colombian phone number format validation
- **Blocked List**: Automatic prevention of messages to blocked numbers
- **Rate Limiting**: Configurable delays between campaign messages
- **Template Compliance**: Only approved WhatsApp templates can be sent

## 🚨 Compliance Notes

### WhatsApp Business API Compliance

1. **Template Approval**: All marketing messages must use approved templates
2. **Opt-in Requirement**: Only send to contacts who have opted in
3. **24-hour Window**: Non-template messages only within 24h of user message
4. **Rate Limits**: Respect Twilio/WhatsApp rate limits

### Data Privacy

- **Message Logging**: All messages are logged for analytics
- **Contact Management**: Secure storage of phone numbers and contact data
- **GDPR Compliance**: Provide data deletion capabilities for users

## 🆘 Troubleshooting

### Common Issues

**1. "Twilio not configured" Error**
```bash
# Check your Heroku config vars
heroku config
```
Ensure TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_NUMBER are set.

**2. Migration Errors**
```bash
# Check migration status
heroku run alembic current
heroku run alembic history

# Re-run migration if needed
heroku run alembic upgrade head
```

**3. Analytics Not Loading**
```bash
# Check if tables exist
heroku pg:psql -c "\dt analytics*"

# Check application logs
heroku logs --tail
```

**4. Messages Not Sending**
- Ensure WhatsApp number is verified in Twilio console
- Check recipient numbers are in correct format (+57...)
- Verify template is approved in Twilio console

**5. Webhook Not Working**
- Ensure webhook URL uses HTTPS
- Check webhook is configured in Twilio console
- Verify app is accessible publicly

### Support Commands

```bash
# Check app status
heroku ps

# View logs
heroku logs --tail

# Check database
heroku pg:info

# Run one-time scripts
heroku run python your_script.py
```

## 🎉 What's Next

Future enhancements planned:
- **Advanced Charts**: Chart.js integration for visual analytics
- **A/B Testing**: Test different message templates
- **Smart Scheduling**: Optimize send times based on response data
- **Advanced Segmentation**: Target campaigns based on lead characteristics
- **Integration APIs**: Connect with popular CRM systems

---

*For questions or support, check Heroku logs with `heroku logs --tail` or contact the development team.* 