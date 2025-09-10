# Lasso CRM Integration Guide

## Overview

This system provides comprehensive CRM integration for 4 different properties using Lasso CRM exclusively. It allows you to inject leads to specific properties based on customer interest and location.

## Properties Supported

**Note**: "Residencias" is the default project for leads that haven't defined a specific project interest. Each property requires its own API key configuration.

| Property | Key | Lasso ID | Display Name |
|----------|-----|----------|--------------|
| Costalegre | `costalegre` | 24609 | Costalegre |
| Residencias | `residencias` | 24608 | Residencias |
| Valle de Guadalupe | `valle_de_guadalupe` | 24611 | Valle de Guadalupe |
| Yucatan | `yucatan` | 24610 | Yucatan |

## Environment Variables

Add the following environment variables to your `.env` file or Render configuration. **You need both the LASSO UID and property-specific API keys**:

```bash
# Lasso CRM Organization/Account Identifier
LASSO_UID=your_lasso_organization_uid_here

# Yucatan Property API Key
LASSO_API_KEY_YUCATAN=your_yucatan_lasso_api_key_here

# Costalegre Property API Key
LASSO_API_KEY_COSTALEGRE=your_costalegre_lasso_api_key_here

# Valle de Guadalupe Property API Key
LASSO_API_KEY_VALLE_DE_GUADALUPE=your_valle_guadalupe_lasso_api_key_here

# Residencias Property API Key (Default for general leads)
LASSO_API_KEY_RESIDENCIAS=your_residencias_lasso_api_key_here
```

**Important Notes**:
- **LASSO_UID** is your organization/account identifier in Lasso CRM (required)
- Each property has its own API key in Lasso CRM
- You only need to set the API keys for properties you want to use
- If a property API key is not set, leads for that property will not be injected to CRM
- "Residencias" is the default property for leads that haven't defined a specific project interest
- The LASSO_UID is included in all API calls to identify your organization

## API Endpoints

### 1. Get CRM Status
```http
GET /api/crm/status
```

Returns the status of available CRM services and properties.

### 2. Get Available Properties
```http
GET /api/crm/properties
```

Returns all available properties with their details.

### 3. Get Property Information
```http
GET /api/crm/properties/{property_key}
```

Returns detailed information about a specific property.

### 4. Inject Lead to Property
```http
POST /api/crm/inject-lead
Content-Type: application/json

{
  "customer_data": {
    "nombre": "John Doe",
    "email": "john@example.com",
    "telefono": "+1234567890",
    "fuente": "WhatsApp",
    "motivo_interes": "Interested in apartment",
    "urgencia_compra": "alto",
    "tipo_propiedad": "Apartamento",
    "presupuesto_min": 100000,
    "presupuesto_max": 200000,
    "desea_visita": true,
    "desea_llamada": false,
    "desea_informacion": true
  },
  "property_key": "costalegre"
}
```

### 5. Inject Lead to Multiple Properties
```http
POST /api/crm/inject-lead-multiple
Content-Type: application/json

{
  "customer_data": {
    "nombre": "John Doe",
    "email": "john@example.com",
    "telefono": "+1234567890",
    "fuente": "WhatsApp",
    "motivo_interes": "Interested in multiple properties"
  },
  "property_keys": ["costalegre", "residencias"]
}
```

### 6. Test Lead Injection
```http
POST /api/crm/test-injection?property_key=costalegre
```

Tests lead injection with sample data.

### 7. Test Property Connection
```http
GET /api/crm/properties/costalegre/test
```

Tests connection to a specific property.

## CRM Integration

This system exclusively uses **Lasso CRM** for all lead management and injection operations.

## Property Key Mapping

The system automatically determines the appropriate property based on:

1. **Project Interest** (`proyecto_interes`):
   - "costalegre" → `costalegre`
   - "residencias" → `residencias`
   - "valle de guadalupe" → `valle_de_guadalupe`
   - "yucatan" → `yucatan`

2. **City Interest** (`ciudad_interes`):
   - "guadalajara", "puerto vallarta" → `costalegre`
   - "ensenada", "baja california" → `valle_de_guadalupe`
   - "merida", "yucatan" → `yucatan`

3. **Default**: If no specific mapping is found, defaults to `residencias` (for leads that haven't defined a specific project interest)

## Integration with Existing System

The CRM integration is automatically triggered when:

1. **Lead Qualification**: When a lead is qualified through the `qualify_lead` function
2. **Customer Info Capture**: When customer information is captured
3. **Auto Lead Injection**: When leads are automatically detected and injected

**Property-Specific Routing**:
- The system automatically determines which property the lead is interested in
- Uses the corresponding API key for that specific property
- If no specific property is determined, defaults to "Residencias" (general leads)
- Only properties with configured API keys will receive lead injections

## Usage Examples

### Python Integration

```python
from app.crm_integration import inject_qualified_lead_to_crm, get_available_properties

# Get available properties
properties = get_available_properties()
print(f"Available properties: {[p['name'] for p in properties]}")

# Inject lead to specific property
result = await inject_qualified_lead_to_crm(
    db=db,
    lead=qualified_lead,
    property_key="costalegre"
)

if result["success"]:
    print("Lead successfully injected to CRM")
else:
    print(f"Injection failed: {result['errors']}")
```

### JavaScript/Frontend Integration

```javascript
// Inject lead to property
async function injectLeadToProperty(customerData, propertyKey) {
  const response = await fetch('/api/crm/inject-lead', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      customer_data: customerData,
      property_key: propertyKey
    })
  });
  
  const result = await response.json();
  return result;
}

// Get available properties
async function getProperties() {
  const response = await fetch('/api/crm/properties');
  const result = await response.json();
  return result.data.properties;
}
```

## Error Handling

The system provides comprehensive error handling:

- **Invalid Property Key**: Returns 400 error with details
- **Lasso CRM Service Unavailable**: Logs error and provides detailed error messages
- **API Failures**: Retries and provides detailed error messages
- **Validation Errors**: Returns specific validation messages

## Monitoring and Logging

All CRM operations are logged with:
- Success/failure status
- Property information
- Lead details (anonymized)
- Error messages
- Performance metrics

## Testing

Use the test endpoints to verify your integration:

1. **Test CRM Status**: `GET /api/crm/status`
2. **Test Property Connection**: `GET /api/crm/properties/{property_key}/test`
3. **Test Lead Injection**: `POST /api/crm/test-injection`

## Security Considerations

- API keys are stored as environment variables
- All API calls use HTTPS
- Lead data is validated before injection
- Error messages don't expose sensitive information

## Troubleshooting

### Common Issues

1. **"LASSO_UID environment variable not set"**
   - Add `LASSO_UID=your_organization_uid_here` to your environment variables
   - This is your organization/account identifier in Lasso CRM

2. **"API key not configured for property X"**
   - Add the specific property API key to your environment variables
   - Example: `LASSO_API_KEY_YUCATAN=your_api_key_here`

3. **"Property X is not configured in Lasso CRM"**
   - The property API key is missing from your environment variables
   - Check that you have the correct API key for that specific property

4. **"Invalid property key"**
   - Use one of the valid property keys: `costalegre`, `residencias`, `valle_de_guadalupe`, `yucatan`
   - Make sure the property has an API key configured

5. **"Lasso CRM injection failed"**
   - Check your LASSO_UID is correct
   - Check your property-specific Lasso API key validity
   - Verify network connectivity
   - Check Lasso CRM API documentation for any changes
   - Ensure the API key has the correct permissions for that property

### Debug Mode

Enable debug logging by setting `DEBUG=true` in your environment variables to see detailed logs.

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify your API keys and configuration
3. Test with the provided test endpoints
4. Contact the development team with specific error details

