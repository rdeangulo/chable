# app/services/property_selector.py

import os
import json
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models import QualifiedLead
from app.services.twilio_service import TwilioService
from app.services.lasso_crm_service import LassoCRMService

logger = logging.getLogger(__name__)

class PropertySelector:
    """
    Service for handling property selection through WhatsApp interactive messages.
    Provides context to agents and routes to correct CRM based on property selection.
    """
    
    def __init__(self):
        self.twilio_service = TwilioService()
        self.lasso_service = LassoCRMService()
        
        # Property mapping with WhatsApp button data
        self.properties = {
            "yucatan": {
                "name": "The Residences at Chablé Yucatán",
                "short_name": "Yucatán",
                "button_text": "🏛️ Yucatán - 72 residencias",
                "button_payload": "property_yucatan",
                "lasso_project_id": 24610,
                "sales_contact": {
                    "name": "Luisa Carrera",
                    "phone": "+52 556 675 2552",
                    "email": "luisa.carrera@evrealestate.com"
                }
            },
            "valle_de_guadalupe": {
                "name": "The Residences at Chablé Valle de Guadalupe", 
                "short_name": "Valle de Guadalupe",
                "button_text": "🍷 Valle de Guadalupe - 10 residencias",
                "button_payload": "property_valle_guadalupe",
                "lasso_project_id": 24611,
                "sales_contact": {
                    "name": "Marco Ehrenberg",
                    "phone": "+52 624 151 5400",
                    "email": "marco@sirloscabos.com"
                }
            },
            "costalegre": {
                "name": "The Residences at Chablé Costalegre",
                "short_name": "Costalegre", 
                "button_text": "🏖️ Costalegre - 19 residencias",
                "button_payload": "property_costalegre",
                "lasso_project_id": 24612,
                "sales_contact": {
                    "name": "JP Mahony",
                    "phone": "+52 322 152 3292",
                    "email": "jp@jpmrealestate.com"
                }
            },
            "mar_de_cortes": {
                "name": "The Residences at Chablé Mar de Cortés",
                "short_name": "Mar de Cortés",
                "button_text": "🌊 Mar de Cortés - Nuevo desarrollo",
                "button_payload": "property_mar_de_cortes", 
                "lasso_project_id": 24778,
                "sales_contact": {
                    "name": "TBD",
                    "phone": "TBD",
                    "email": "TBD"
                }
            }
        }
    
    def create_property_selection_message(self) -> str:
        """
        Create an interactive WhatsApp message with property selection buttons.
        """
        message = """🏡 *¡Excelente! Te ayudo a encontrar la propiedad perfecta.*

Tenemos 4 desarrollos exclusivos de Chablé Residences:

*Selecciona el proyecto que más te interese:*"""
        
        return message
    
    def create_property_buttons(self) -> List[Dict[str, Any]]:
        """
        Create WhatsApp interactive buttons for property selection.
        """
        buttons = []
        
        for key, property_info in self.properties.items():
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": property_info["button_payload"],
                    "title": property_info["button_text"]
                }
            })
        
        return buttons
    
    async def handle_property_selection(
        self, 
        db: Session, 
        phone_number: str, 
        selected_property: str,
        lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle property selection and provide context to agent.
        
        Args:
            db: Database session
            phone_number: Customer's phone number
            selected_property: Selected property key
            lead_data: Lead information
            
        Returns:
            Dict with result status and next steps
        """
        try:
            if selected_property not in self.properties:
                return {
                    "success": False,
                    "error": f"Invalid property selection: {selected_property}"
                }
            
            property_info = self.properties[selected_property]
            
            # Create context message for agent
            context_message = self._create_agent_context(property_info, lead_data)
            
            # Send context to agent via WhatsApp
            agent_phone = property_info["sales_contact"]["phone"]
            await self._notify_agent(agent_phone, context_message, phone_number)
            
            # Create enhanced lead data with property context
            enhanced_lead_data = {
                **lead_data,
                "proyecto_interes": property_info["name"],
                "property_key": selected_property,
                "lasso_project_id": property_info["lasso_project_id"],
                "sales_contact": property_info["sales_contact"]
            }
            
            # Inject to correct Lasso CRM project
            crm_result = await self._inject_to_crm(enhanced_lead_data, selected_property)
            
            # Send confirmation to customer
            customer_message = self._create_customer_confirmation(property_info)
            await self._send_customer_confirmation(phone_number, customer_message)
            
            return {
                "success": True,
                "property_selected": property_info["name"],
                "agent_notified": True,
                "crm_injected": crm_result.get("success", False),
                "next_steps": f"Un asesor de {property_info['short_name']} se pondrá en contacto contigo pronto."
            }
            
        except Exception as e:
            logger.error(f"Error handling property selection: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_agent_context(self, property_info: Dict[str, Any], lead_data: Dict[str, Any]) -> str:
        """
        Create context message for the sales agent.
        """
        context = f"""🎯 *NUEVO LEAD - {property_info['short_name']}*

*Cliente:* {lead_data.get('nombre', 'N/A')}
*Teléfono:* {lead_data.get('telefono', 'N/A')}
*Email:* {lead_data.get('email', 'N/A')}

*Interés:* {lead_data.get('motivo_interes', 'N/A')}
*Urgencia:* {lead_data.get('urgencia_compra', 'N/A')}
*Presupuesto:* {lead_data.get('presupuesto_min', 'N/A')} - {lead_data.get('presupuesto_max', 'N/A')}

*Proyecto seleccionado:* {property_info['name']}
*Fuente:* WhatsApp Bot

*Acciones requeridas:*
• Contactar al cliente en las próximas 2 horas
• Agendar visita si es necesario
• Seguimiento según urgencia del cliente

*Datos de contacto del cliente:*
{lead_data.get('telefono', 'N/A')}"""

        return context
    
    async def _notify_agent(self, agent_phone: str, context_message: str, customer_phone: str):
        """
        Send context notification to sales agent.
        """
        try:
            # Format agent phone for WhatsApp
            if not agent_phone.startswith('whatsapp:'):
                agent_phone = f'whatsapp:{agent_phone}'
            
            # Send context message to agent
            message_sid = await self.twilio_service.send_message(
                to_number=agent_phone,
                message_body=context_message
            )
            
            if message_sid:
                logger.info(f"Agent notification sent to {agent_phone}: {message_sid}")
            else:
                logger.error(f"Failed to send agent notification to {agent_phone}")
                
        except Exception as e:
            logger.error(f"Error notifying agent: {e}")
    
    async def _inject_to_crm(self, lead_data: Dict[str, Any], property_key: str) -> Dict[str, Any]:
        """
        Inject lead to the correct Lasso CRM project.
        """
        try:
            # Use the Lasso service to inject to correct project
            result = await self.lasso_service.create_lead(
                property_key=property_key,
                lead_data=lead_data
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error injecting to CRM: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_customer_confirmation(self, property_info: Dict[str, Any]) -> str:
        """
        Create confirmation message for customer.
        """
        sales_contact = property_info["sales_contact"]
        
        message = f"""✅ *¡Perfecto! Hemos recibido tu interés en {property_info['short_name']}*

*Tu asesor especializado:*
👤 {sales_contact['name']}
📞 {sales_contact['phone']}
📧 {sales_contact['email']}

*Próximos pasos:*
• Tu asesor se pondrá en contacto contigo en las próximas 2 horas
• Te enviará información detallada del proyecto
• Podrás agendar una visita personalizada

*¿Necesitas algo más mientras tanto?*
Puedo ayudarte con información adicional sobre el proyecto o responder cualquier pregunta que tengas."""
        
        return message
    
    async def _send_customer_confirmation(self, phone_number: str, message: str):
        """
        Send confirmation message to customer.
        """
        try:
            message_sid = await self.twilio_service.send_message(
                to_number=phone_number,
                message_body=message
            )
            
            if message_sid:
                logger.info(f"Customer confirmation sent to {phone_number}: {message_sid}")
            else:
                logger.error(f"Failed to send customer confirmation to {phone_number}")
                
        except Exception as e:
            logger.error(f"Error sending customer confirmation: {e}")
    
    def get_property_info(self, property_key: str) -> Optional[Dict[str, Any]]:
        """
        Get property information by key.
        """
        return self.properties.get(property_key)
    
    def get_all_properties(self) -> Dict[str, Any]:
        """
        Get all available properties.
        """
        return self.properties
