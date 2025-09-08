# Agent Training Update - Yucatan Focus Strategy

## Overview

The AI agent has been updated to focus primarily on **Yucatan** while still promoting all 4 properties when appropriate. This strategic approach ensures maximum lead generation for the primary property while capturing interest in other developments.

## Updated System Prompt

### English Version
The agent now mentions **4 exclusive developments** with Yucatan as the primary focus:

> "Answer questions about our four exclusive developments: Yucatán (PRIMARY FOCUS), Valle de Guadalupe, Costalegre, and Residencias. Always prioritize Yucatán as the main recommendation, but mention other properties when clients show interest in different locations or have specific regional preferences."

### Spanish Version
The Spanish prompt includes detailed property information and sales strategy:

```
PROPIEDADES DISPONIBLES (4 desarrollos exclusivos):
- YUCATÁN (ENFOQUE PRINCIPAL) - Riviera Maya, México
- Valle de Guadalupe - Baja California, México
- Costalegre - Jalisco, México
- Residencias - Ubicación general

ESTRATEGIA DE VENTAS:
- SIEMPRE prioriza Yucatán como la recomendación principal
- Menciona otros desarrollos cuando el cliente muestre interés en diferentes ubicaciones
- Adapta las recomendaciones según las preferencias regionales del cliente
- Si preguntan por ubicaciones específicas, menciona el desarrollo correspondiente
```

## Property Mapping Strategy

### Primary Focus: Yucatan
The agent prioritizes **Yucatan** as the main recommendation, but routes leads to **Residencias** when no specific property preference is detected (for leads that haven't defined a specific project interest).

### Regional Mapping
Enhanced city mapping to better route leads to appropriate properties:

#### Yucatan (Primary Focus) - Riviera Maya Region
- Yucatan, Yucatán
- Merida, Mérida
- Riviera Maya
- Cancun, Cancún
- Playa del Carmen
- Tulum
- Cozumel
- Quintana Roo
- Caribe, Caribbean

#### Costalegre - Jalisco Region
- Costalegre
- Guadalajara
- Puerto Vallarta, Vallarta
- Jalisco


#### Valle de Guadalupe - Baja California Region
- Guadalupe
- Ensenada
- Baja California
- Valle
- Vino, Wine

## Lead Routing Logic

### Automatic Property Detection
1. **Project Interest** (`proyecto_interes`): Direct mapping to property
2. **City Interest** (`ciudad_interes`): Regional mapping to appropriate property
3. **Default**: Routes to **Yucatan** (primary focus)

### CRM Integration
- All leads are automatically routed to the appropriate property in Lasso CRM
- Default routing goes to Residencias when no specific preference is detected (general leads)
- Specific projects (Yucatan, Valle de Guadalupe, Costalegre) are assigned to their respective CRMs
- Multi-property injection available for leads interested in multiple developments

## Conversation Flow Strategy

### Initial Contact
1. **Welcome** with focus on Yucatan as the premier development
2. **Ask about location preferences** to identify regional interest
3. **Mention other properties** when relevant to client's needs

### Information Sharing
1. **Primary**: Always lead with Yucatan information
2. **Secondary**: Mention other properties based on:
   - Client's location preferences
   - Budget considerations
   - Lifestyle preferences (beach, wine country, etc.)

### Lead Qualification
1. **Capture interest level** for Yucatan
2. **Identify secondary interests** in other properties
3. **Route to appropriate CRM** based on primary interest
4. **Flag for multi-property follow-up** if applicable

## Example Conversation Flows

### Scenario 1: General Inquiry
**Client**: "Hola, me interesa conocer sus propiedades"
**Agent**: "¡Hola! Te doy la bienvenida a Residencias Chable. Nuestro desarrollo principal es **Yucatán** en la Riviera Maya, una ubicación privilegiada en el Caribe mexicano. ¿Te interesa conocer más sobre Yucatán o tienes preferencia por alguna región específica de México?"

### Scenario 2: Regional Interest
**Client**: "Estoy buscando algo en Baja California"
**Agent**: "Perfecto, tenemos **Valle de Guadalupe** en Baja California, una región famosa por sus viñedos y clima mediterráneo. Te puedo enviar información específica sobre este desarrollo. ¿También te interesa conocer sobre **Yucatán** en la Riviera Maya como opción adicional?"

### Scenario 3: Beach Interest
**Client**: "Quiero algo cerca de la playa"
**Agent**: "Excelente elección. **Yucatán** en la Riviera Maya es perfecto para ti, con acceso directo a las mejores playas del Caribe. También tenemos **Costalegre** en Jalisco con hermosas playas del Pacífico. ¿Te interesa conocer ambos desarrollos?"

## CRM Integration Benefits

### Automatic Lead Routing
- **Yucatan leads** → Yucatan CRM (Primary focus)
- **Regional leads** → Appropriate property CRM
- **General/undefined leads** → Residencias CRM (Default for leads without specific project interest)
- **Multi-interest leads** → Multiple property CRMs

### Lead Quality Improvement
- Better qualification based on location preferences
- Reduced lead waste through proper routing
- Increased conversion through targeted follow-up

### Sales Team Efficiency
- Leads pre-qualified by property interest
- Regional sales teams get appropriate leads
- Yucatan team gets maximum lead volume

## Monitoring and Optimization

### Key Metrics to Track
1. **Yucatan lead volume** (should be highest)
2. **Regional lead distribution** across other properties
3. **Multi-property interest** rates
4. **Conversion rates** by property

### Optimization Opportunities
1. **Adjust city mappings** based on lead quality
2. **Refine conversation flows** based on conversion data
3. **Update property descriptions** based on client feedback
4. **Enhance regional targeting** for underperforming properties

## Implementation Status

✅ **System Prompt Updated** - Yucatan focus implemented
✅ **Property Mapping Enhanced** - All 5 properties supported
✅ **CRM Integration Ready** - Automatic routing configured
✅ **Default Routing** - Yucatan as primary focus
✅ **Regional Mapping** - Comprehensive city-to-property mapping

## Next Steps

1. **Deploy** the updated system
2. **Monitor** lead distribution and quality
3. **Optimize** based on performance data
4. **Train** sales team on new lead routing
5. **Adjust** strategy based on results

The agent is now strategically positioned to maximize Yucatan leads while capturing interest in all 4 properties! 🎯

