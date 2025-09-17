# Lasso CRM Lead Injection Scripts

This directory contains Python scripts to directly inject leads into the Lasso CRM system for the Yucatan project.

## 📁 Files Overview

### 1. `inject_lead_to_lasso.py` - Main Lead Injection Script
Interactive script that prompts for lead information and injects it directly to Lasso CRM.

### 2. `test_lasso_connection.py` - API Connection Tester
Tests the connection to Lasso CRM API and attempts to create a test lead.

### 3. `test_auth_methods.py` - Authentication Tester
Tests different authentication methods to find the correct one for the API.


## 🔑 API Key Configuration

**Environment Variable Required:**
- **LASSO_API_KEY_YUCATAN**: Your Lasso CRM API key for the Yucatan project

**Project Information:**
- **Project ID**: 24610 (Yucatan)
- **Client ID**: 2589

## 🚀 Usage Instructions

### Option 1: Interactive Lead Injection
```bash
# Set your API key first
export LASSO_API_KEY_YUCATAN="your_api_key_here"
python inject_lead_to_lasso.py
```

This will prompt you for:
- Full Name (required)
- Phone Number (required)
- Email (required)
- Source (default: WhatsApp Bot)
- Reason for Interest
- Purchase Urgency
- Property Type
- Budget (min/max)
- City of Interest
- Project Interest (default: Yucatan)
- Contact Preferences

### Option 2: Test API Connection
```bash
# Set your API key first
export LASSO_API_KEY_YUCATAN="your_api_key_here"
python test_lasso_connection.py
```

This will test the API connection and attempt to create a test lead.

### Option 3: Test Authentication Methods
```bash
# Set your API key first
export LASSO_API_KEY_YUCATAN="your_api_key_here"
python test_auth_methods.py
```

This will test different authentication methods to find the working one.

## 🔧 Current Status

**API Connection**: ✅ Connected (Health endpoint returns 200 OK)
**Authentication**: ❌ 401 Unauthorized (Token may need different permissions or endpoint)

## 📋 API Endpoints Tested

1. `https://api.lassocrm.com/v1/registrants` - Main registrants endpoint
2. `https://api.lassocrm.com/v1/health` - Health check (✅ Working)
3. `https://api.lassocrm.com/v1/lead-capture` - Lead capture endpoint (❌ 404)

## 🔍 Authentication Methods Tested

1. **Bearer Token**: `Authorization: Bearer {JWT_TOKEN}`
2. **API Key Header**: `X-API-Key: {JWT_TOKEN}`
3. **Alternative API Key**: `API-Key: {JWT_TOKEN}`
4. **Auth Token**: `X-Auth-Token: {JWT_TOKEN}`

## 📊 Lead Data Structure

The script creates leads with the following structure:

```json
{
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "source": "WhatsApp Bot",
  "projectId": 24610,
  "notes": "Comprehensive lead notes...",
  "customFields": {
    "Motivo de Interés": "visita",
    "Urgencia de Compra": "esta_semana",
    "Tipo de Propiedad": "residencia de lujo"
  },
  "tags": ["WhatsApp Bot", "Yucatan", "Urgencia-esta_semana"]
}
```

## 🛠️ Troubleshooting

### Issue: 401 Unauthorized
**Possible Solutions:**
1. The JWT token may be for a specific lead capture system, not the general API
2. The token might need different permissions
3. The endpoint URL might be different for lead capture

### Issue: 404 Not Found
**Possible Solutions:**
1. The endpoint URL might be incorrect
2. The API version might be different
3. The lead capture might use a different endpoint structure

## 📞 Next Steps

1. **Contact Lasso Support**: The JWT token appears to be for "lassoLeadCapture" which might be a specific system
2. **Verify Endpoint**: Confirm the correct API endpoint for lead capture
3. **Check Permissions**: Ensure the token has the right permissions for lead creation
4. **Alternative Integration**: Consider using Lasso's webhook or form integration instead

## 🔗 Integration with Main System

The scripts are designed to work alongside the main WhatsApp bot system:

1. **Automatic Integration**: The main system already has CRM integration in `app/crm_integration.py`
2. **Manual Testing**: Use these scripts to test and debug CRM integration
3. **Direct Injection**: Use for manual lead injection when needed

## 📝 Example Usage

```python
# Import the injector class
from inject_lead_to_lasso import LassoLeadInjector

# Initialize with your API key
injector = LassoLeadInjector(
    api_key="your_jwt_token_here",
    project_id=24610,
    client_id=2589
)

# Create lead data
lead_data = {
    "nombre": "Juan Pérez",
    "telefono": "+573001234567",
    "email": "juan@example.com",
    "fuente": "WhatsApp Bot",
    "motivo_interes": "visita",
    "urgencia_compra": "esta_semana",
    "proyecto_interes": "Yucatan"
}

# Inject the lead
result = await injector.inject_lead(lead_data)
print(result)
```

## ⚠️ Important Notes

1. **API Key Security**: Never commit API keys to version control
2. **Rate Limiting**: Be aware of API rate limits
3. **Error Handling**: Always implement proper error handling
4. **Data Validation**: Validate lead data before sending
5. **Testing**: Test with non-production data first

## 📚 References

- [Lasso CRM API Documentation](https://lassocrm.com/integrations/)
- [Lasso Developer Platform](https://platform.lassocrm.com/)
- [JWT Token Information](https://jwt.io/)
