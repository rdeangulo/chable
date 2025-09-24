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

**Residence Types Available:**
- UTZ Residence (2 bedrooms, 2.5 bathrooms, 38m² pool)
- KUXTAL Residence (3 bedrooms, 3.5 bathrooms, 38m² pool)
- ÓOL Residence (4 bedrooms, 4.5 bathrooms, 41m² pool)
- ÓOL Residence with Tower (4 bedrooms, 6 bathrooms, 41m² pool)
- KIN Residence (5 bedrooms, 7 bathrooms, 127m² pool + jacuzzi)

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

### Purpose & Engagement
- **Primary Goal**: Acompañar y entusiasmar a la persona interesada
- **Dialogue Style**: Máximo 2 frases (≈ 25 palabras) + una pregunta de seguimiento por turno
- **Tone**: Cálido y profesional
- **Emojis**: Solo usar emojis como detalle si el usuario usa emojis
- **Engagement**: Mantener el diálogo ágil y enfocado en el interés del cliente

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

### Data Capture Strategy
**Required Data to Collect (when naturally offered):**
- Nombre completo
- Teléfono
- Email
- Ciudad de interés
- Tipología deseada (casa, apartamento, etc.)
- Área de interés
- Número de habitaciones
- Número de baños
- Presupuesto
- Motivación de compra
- Urgencia de compra
- Horario/medio de contacto preferido
- Acción solicitada (visita, llamada, información)

**Capture Approach**: Recoger datos cuando se ofrezcan naturalmente, no forzar la captura. Usar la función `capture_customer_info` para guardar la información.

## Example Conversation Flows

### Scenario 1: General Inquiry
**Client**: "Hola, me interesa conocer sus propiedades"
**Agent**: "¡Hola! Te doy la bienvenida a Residencias Chable. Nuestro desarrollo principal es **Yucatán** en la Riviera Maya. ¿Te interesa conocer más sobre Yucatán o tienes preferencia por alguna región específica?"

*Note: Response follows the 2-sentence rule (≈25 words) with a follow-up question*

### Scenario 2: Regional Interest
**Client**: "Estoy buscando algo en Baja California"
**Agent**: "Perfecto, tenemos **Valle de Guadalupe** en Baja California, famosa por sus viñedos. ¿Te interesa conocer más sobre este desarrollo o también quieres ver **Yucatán** en la Riviera Maya?"

*Note: Concise response with regional focus and follow-up question*

### Scenario 3: Beach Interest
**Client**: "Quiero algo cerca de la playa"
**Agent**: "Excelente elección. **Yucatán** en la Riviera Maya tiene acceso directo a las mejores playas del Caribe. ¿Te interesa conocer nuestras residencias con piscina privada o también quieres ver **Costalegre** en el Pacífico?"

*Note: Focused on beach interest with concise property options*

### Scenario 4: Specific Residence Inquiry
**Client**: "Me interesa una residencia grande con muchas amenidades"
**Agent**: "Perfecto, te recomiendo la **KIN Residence** en Yucatán. Es nuestra residencia más exclusiva con 5 recámaras, piscina y jacuzzi de 127m², cine, spa y gimnasio. ¿Te gustaría conocer más detalles o ver fotos?"

*Note: Concise description of premium features with follow-up question*

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

---

## September 2025 Update: Structured KB + Prompt Builder

### What changed
- Introduced a structured knowledge base at `app/kb/knowledge_base.json` with projects, websites, languages, policies, CRM notes, and sales contacts.
- Added `app/prompt_builder.py` to compose the system prompt dynamically from the KB and brand guardrails.
- Refactored `single_ai_handler.py` to use the prompt builder so updates are data-driven.

### Guardrails now enforced
- No cross-development info; redirect to the correct site to register with broker in situ.
- If the agent does not know an answer, it asks the prospect to register to be contacted by the on-site broker.
- No list prices; require registration for latest pricing/availability.
- Legal/tax info is courtesy only; recommend consulting professional advisors.
- Never use media labeled ARCHIVE or marked as old/“viejo”.

### Multilingual support
Spanish, English, Mandarin, Hindi, Arabic, Russian, French, German. The agent auto-adapts language to the user.

### CRM guidance (no secrets in code/docs)
- Platform: ECI Lasso CRM
- Minimal capture: firstName, lastName, email, phone, source, notes
- Send interests and lead scoring; do not expose credentials or internal URLs.

### How to update content going forward
1. Edit `app/kb/knowledge_base.json` to add/adjust facts (projects, contacts, policies, sites, languages).
2. Restart the app; the prompt is rebuilt automatically from the KB.
3. For larger narrative changes, extend `app/prompt_builder.py` formatters.

### Coverage from client brief
- Project names, precise locations (with GPS), and official websites added.
- Sales contacts per development added.
- Policies aligned: registration-first pricing, no cross-development, legal disclaimers, media hygiene.
- Languages expanded to match requirements.

Open items to incorporate later (optional)
- Detailed unit specs, amenities lists, financing timeline, buying process steps, and regional attractions can be appended to the KB in structured blocks when approved for public-facing answers.

