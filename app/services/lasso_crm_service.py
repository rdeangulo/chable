# app/services/lasso_crm_service.py

import os
import logging
import httpx
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class LassoCRMService:
    """Service class for Lasso CRM operations and lead injection."""
    
    # Property mapping with their Lasso CRM IDs
    PROPERTY_MAPPING = {
        "costalegre": {
            "id": 24609,
            "name": "Costalegre",
            "display_name": "Costalegre"
        },
        "residencias": {
            "id": 24608,
            "name": "Residencias",
            "display_name": "Residencias"
        },
        "valle_de_guadalupe": {
            "id": 24611,
            "name": "Valle de Guadalupe",
            "display_name": "Valle de Guadalupe"
        },
        "yucatan": {
            "id": 24610,
            "name": "Yucatan",
            "display_name": "Yucatan"
        }
    }
    
    def __init__(self):
        """Initialize Lasso CRM client and configuration."""
        self.api_key = os.getenv("LASSO_API_KEY")
        self.base_url = "https://api.lasso.com"  # Update with actual Lasso API URL
        
        if not self.api_key:
            logger.warning("LASSO_API_KEY environment variable not set")
    
    def get_property_info(self, property_key: str) -> Optional[Dict[str, Any]]:
        """
        Get property information by key.
        
        Args:
            property_key: Property identifier (e.g., 'costalegre', 'residencias')
            
        Returns:
            Dict with property info or None if not found
        """
        return self.PROPERTY_MAPPING.get(property_key.lower())
    
    def get_all_properties(self) -> List[Dict[str, Any]]:
        """Get all available properties."""
        return list(self.PROPERTY_MAPPING.values())
    
    def normalize_phone_number(self, phone: str) -> str:
        """
        Normalize phone number for Lasso CRM.
        
        Args:
            phone: Raw phone number
            
        Returns:
            Normalized phone number
        """
        if not phone:
            return ""
        
        # Remove common prefixes and non-digits except leading '+'
        phone = str(phone).strip()
        phone = phone.replace("whatsapp:", "")
        
        # Keep leading '+' if present, remove other non-digits
        if phone.startswith('+'):
            digits = '+' + ''.join(filter(str.isdigit, phone[1:]))
        else:
            digits = ''.join(filter(str.isdigit, phone))
        
        # Add country code if missing (assuming Mexico +52)
        if digits and not digits.startswith('+'):
            if len(digits) == 10:  # Mexican phone number without country code
                digits = '+52' + digits
            else:
                digits = '+' + digits
        
        return digits
    
    def prepare_lead_data(self, customer_data: Dict[str, Any], property_key: str) -> Dict[str, Any]:
        """
        Prepare lead data for Lasso CRM injection.
        
        Args:
            customer_data: Customer information
            property_key: Property identifier
            
        Returns:
            Formatted data for Lasso CRM
        """
        property_info = self.get_property_info(property_key)
        if not property_info:
            raise ValueError(f"Unknown property: {property_key}")
        
        # Normalize phone number
        phone = self.normalize_phone_number(customer_data.get("telefono", ""))
        
        # Prepare lead data according to Lasso CRM format
        lead_data = {
            "property_id": property_info["id"],
            "property_name": property_info["name"],
            "contact": {
                "first_name": customer_data.get("nombre", "").split()[0] if customer_data.get("nombre") else "",
                "last_name": " ".join(customer_data.get("nombre", "").split()[1:]) if customer_data.get("nombre") and len(customer_data.get("nombre", "").split()) > 1 else "",
                "email": customer_data.get("email", ""),
                "phone": phone,
                "source": customer_data.get("fuente", "WhatsApp"),
                "lead_source": "WhatsApp Bot",
                "notes": f"Lead from WhatsApp Bot - {customer_data.get('motivo_interes', 'General inquiry')}"
            },
            "lead_details": {
                "interest_level": self._normalize_interest_level(customer_data.get("urgencia_compra", "medio")),
                "budget_min": customer_data.get("presupuesto_min"),
                "budget_max": customer_data.get("presupuesto_max"),
                "property_type": customer_data.get("tipo_propiedad", ""),
                "city_interest": customer_data.get("ciudad_interes", ""),
                "visit_requested": customer_data.get("desea_visita", False),
                "call_requested": customer_data.get("desea_llamada", False),
                "information_requested": customer_data.get("desea_informacion", False)
            },
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "platform": customer_data.get("sender_platform", "WhatsApp"),
                "thread_id": customer_data.get("thread_id"),
                "conversation_summary": customer_data.get("conversation_summary", "")
            }
        }
        
        return lead_data
    
    def _normalize_interest_level(self, interest: str) -> str:
        """Normalize interest level for Lasso CRM."""
        if not interest:
            return "medium"
        
        interest_lower = str(interest).lower()
        if interest_lower in ["alto", "alta", "high", "urgente"]:
            return "high"
        elif interest_lower in ["bajo", "baja", "low"]:
            return "low"
        else:
            return "medium"
    
    async def create_lead(self, customer_data: Dict[str, Any], property_key: str) -> Optional[str]:
        """
        Create a lead in Lasso CRM for the specified property.
        
        Args:
            customer_data: Customer information
            property_key: Property identifier
            
        Returns:
            Lead ID if successful, None otherwise
        """
        if not self.api_key:
            logger.error("LASSO_API_KEY not configured")
            return None
        
        try:
            # Prepare lead data
            lead_data = self.prepare_lead_data(customer_data, property_key)
            
            # Lasso CRM API endpoint (update with actual endpoint)
            endpoint = f"{self.base_url}/api/v1/leads"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=lead_data,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                lead_id = result.get("id") or result.get("lead_id")
                logger.info(f"Successfully created Lasso CRM lead {lead_id} for property {property_key}")
                
                return str(lead_id) if lead_id else None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Lasso CRM API error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating Lasso CRM lead: {e}")
            return None
    
    async def update_lead(self, lead_id: str, customer_data: Dict[str, Any], property_key: str) -> bool:
        """
        Update an existing lead in Lasso CRM.
        
        Args:
            lead_id: Existing lead ID
            customer_data: Updated customer information
            property_key: Property identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.error("LASSO_API_KEY not configured")
            return False
        
        try:
            # Prepare updated lead data
            lead_data = self.prepare_lead_data(customer_data, property_key)
            
            # Lasso CRM API endpoint (update with actual endpoint)
            endpoint = f"{self.base_url}/api/v1/leads/{lead_id}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    endpoint,
                    headers=headers,
                    json=lead_data,
                    timeout=30.0
                )
                
                response.raise_for_status()
                logger.info(f"Successfully updated Lasso CRM lead {lead_id} for property {property_key}")
                
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Lasso CRM API error: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error updating Lasso CRM lead: {e}")
            return False
    
    async def search_lead(self, phone: str, email: str = None) -> Optional[Dict[str, Any]]:
        """
        Search for existing lead in Lasso CRM.
        
        Args:
            phone: Phone number to search
            email: Email to search (optional)
            
        Returns:
            Lead data if found, None otherwise
        """
        if not self.api_key:
            logger.error("LASSO_API_KEY not configured")
            return None
        
        try:
            # Normalize phone number
            normalized_phone = self.normalize_phone_number(phone)
            
            # Lasso CRM search endpoint (update with actual endpoint)
            endpoint = f"{self.base_url}/api/v1/leads/search"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Search criteria
            search_criteria = {
                "phone": normalized_phone
            }
            
            if email:
                search_criteria["email"] = email
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=search_criteria,
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                # Return first match if found
                if result.get("leads") and len(result["leads"]) > 0:
                    return result["leads"][0]
                
                return None
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Lasso CRM search error: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error searching Lasso CRM lead: {e}")
            return None
    
    async def create_or_update_lead(self, customer_data: Dict[str, Any], property_key: str) -> Optional[str]:
        """
        Create a new lead or update existing one in Lasso CRM.
        
        Args:
            customer_data: Customer information
            property_key: Property identifier
            
        Returns:
            Lead ID if successful, None otherwise
        """
        try:
            # First, try to find existing lead
            phone = customer_data.get("telefono", "")
            email = customer_data.get("email", "")
            
            existing_lead = await self.search_lead(phone, email)
            
            if existing_lead:
                # Update existing lead
                lead_id = existing_lead.get("id")
                success = await self.update_lead(lead_id, customer_data, property_key)
                if success:
                    logger.info(f"Updated existing Lasso CRM lead {lead_id} for property {property_key}")
                    return lead_id
                else:
                    logger.error(f"Failed to update existing Lasso CRM lead {lead_id}")
                    return None
            else:
                # Create new lead
                lead_id = await self.create_lead(customer_data, property_key)
                if lead_id:
                    logger.info(f"Created new Lasso CRM lead {lead_id} for property {property_key}")
                    return lead_id
                else:
                    logger.error(f"Failed to create new Lasso CRM lead for property {property_key}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error in create_or_update_lead: {e}")
            return None
    
    def get_property_by_id(self, property_id: int) -> Optional[Dict[str, Any]]:
        """
        Get property information by ID.
        
        Args:
            property_id: Property ID
            
        Returns:
            Property info if found, None otherwise
        """
        for key, info in self.PROPERTY_MAPPING.items():
            if info["id"] == property_id:
                return info
        return None
    
    def validate_property_key(self, property_key: str) -> bool:
        """
        Validate if property key exists.
        
        Args:
            property_key: Property identifier
            
        Returns:
            True if valid, False otherwise
        """
        return property_key.lower() in self.PROPERTY_MAPPING

