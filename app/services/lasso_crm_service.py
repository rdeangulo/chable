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
    
    # Property mapping with their Lasso CRM IDs and API keys
    PROPERTY_MAPPING = {
        "costalegre": {
            "id": 24609,
            "name": "Costalegre",
            "display_name": "Costalegre",
            "api_key_env": "LASSO_API_KEY_COSTALEGRE"
        },
        "residencias": {
            "id": 24608,
            "name": "Residencias",
            "display_name": "Residencias",
            "api_key_env": "LASSO_API_KEY_RESIDENCIAS"
        },
        "valle_de_guadalupe": {
            "id": 24611,
            "name": "Valle de Guadalupe",
            "display_name": "Valle de Guadalupe",
            "api_key_env": "LASSO_API_KEY_VALLE_DE_GUADALUPE"
        },
        "yucatan": {
            "id": 24610,
            "name": "Yucatan",
            "display_name": "Yucatan",
            "api_key_env": "LASSO_API_KEY_YUCATAN"
        },
        "mar_de_cortes": {
            "id": 24778,
            "name": "Mar de Cortes",
            "display_name": "Mar de Cortes",
            "api_key_env": "LASSO_API_KEY_MAR_DE_CORTES"
        }
    }
    
    def __init__(self):
        """Initialize Lasso CRM client and configuration."""
        self.base_url = "https://api.lassocrm.com"  # Correct Lasso CRM API URL
        
        # Get LASSO UID (organization/account identifier)
        self.lasso_uid = os.getenv("LASSO_UID")
        if not self.lasso_uid:
            logger.warning("LASSO_UID environment variable not set")
        
        # Check which properties have API keys configured
        self.configured_properties = {}
        for property_key, property_info in self.PROPERTY_MAPPING.items():
            api_key = os.getenv(property_info["api_key_env"])
            if api_key:
                self.configured_properties[property_key] = {
                    "api_key": api_key,
                    "property_info": property_info
                }
            else:
                logger.warning(f"API key not configured for property {property_key} ({property_info['api_key_env']})")
        
        logger.info(f"Lasso CRM initialized with UID: {self.lasso_uid} and {len(self.configured_properties)} configured properties")
    
    def get_property_info(self, property_key: str) -> Optional[Dict[str, Any]]:
        """
        Get property information by key.
        
        Args:
            property_key: Property identifier (e.g., 'costalegre', 'residencias')
            
        Returns:
            Dict with property info or None if not found
        """
        return self.PROPERTY_MAPPING.get(property_key.lower())
    
    def get_property_api_key(self, property_key: str) -> Optional[str]:
        """
        Get API key for a specific property.
        
        Args:
            property_key: Property identifier
            
        Returns:
            API key string or None if not configured
        """
        if property_key in self.configured_properties:
            return self.configured_properties[property_key]["api_key"]
        return None
    
    def is_property_configured(self, property_key: str) -> bool:
        """
        Check if a property has API key configured.
        
        Args:
            property_key: Property identifier
            
        Returns:
            True if property is configured, False otherwise
        """
        return property_key in self.configured_properties
    
    def get_all_properties(self) -> List[Dict[str, Any]]:
        """Get all configured properties."""
        return [prop_config["property_info"] for prop_config in self.configured_properties.values()]
    
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
        
        # Extract and validate name - ensure we have both first and last name
        full_name = customer_data.get("nombre", "").strip()
        if not full_name:
            # Use phone number as fallback name
            phone_digits = ''.join(filter(str.isdigit, phone))
            full_name = f"Cliente {phone_digits[-4:]}" if phone_digits else "Cliente WhatsApp"
        
        # Split name into first and last name - ensure we have both
        name_parts = full_name.split()
        if len(name_parts) < 2:
            # If we don't have both first and last name, create a complete name
            if len(name_parts) == 1:
                full_name = f"{name_parts[0]} WhatsApp"
                name_parts = full_name.split()
            else:
                phone_digits = ''.join(filter(str.isdigit, phone))
                full_name = f"Cliente {phone_digits[-4:]}" if phone_digits else "Cliente WhatsApp"
                name_parts = full_name.split()
        
        first_name = name_parts[0] if name_parts else "Cliente"
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else "WhatsApp"
        
        # Final validation - ensure we have both first and last name
        if not first_name or not last_name:
            logger.error(f"Invalid name structure: first_name='{first_name}', last_name='{last_name}'")
            first_name = "Cliente"
            last_name = "WhatsApp"
        
        logger.info(f"Lasso CRM lead data - first_name: '{first_name}', last_name: '{last_name}', phone: '{phone}'")
        
        # Prepare lead data according to Lasso CRM format (based on API response example)
        lead_data = {
            "person": {
                "firstName": first_name,
                "lastName": last_name,
                "company": customer_data.get("empresa", ""),
                "contactPreference": "any",
                "gender": customer_data.get("genero", ""),
                "nickname": first_name
            },
            "emails": [
                {
                    "email": customer_data.get("email", ""),
                    "type": "Personal",
                    "primary": True
                }
            ] if customer_data.get("email") else [],
            "phones": [
                {
                    "phone": phone,
                    "type": "Mobile",
                    "primary": True
                }
            ],
            "project": {
                "projectId": property_info["id"],
                "name": property_info["name"]
            },
            "sourceType": {
                "sourceType": "WhatsApp Bot"
            },
            "secondarySourceType": {
                "secondarySourceType": customer_data.get("fuente", "WhatsApp")
            },
            "rating": {
                "rating": self._normalize_interest_level(customer_data.get("urgencia_compra", "medio")).upper()
            },
            "notes": [
                {
                    "note": f"Lead from WhatsApp Bot - {customer_data.get('motivo_interes', 'General inquiry')}"
                }
            ] if customer_data.get("motivo_interes") else []
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
    
    async def create_lead(self, customer_data: Dict[str, Any], property_key: str) -> Dict[str, Any]:
        """
        Create a lead in Lasso CRM for the specified property.
        
        Args:
            customer_data: Customer information
            property_key: Property identifier
            
        Returns:
            Dictionary with success status and details
        """
        # Get API key for this specific property
        api_key = self.get_property_api_key(property_key)
        if not api_key:
            logger.error(f"API key not configured for property {property_key}")
            return {"success": False, "error": "API key not configured", "details": f"No API key for property {property_key}"}
        
        try:
            # Prepare lead data
            lead_data = self.prepare_lead_data(customer_data, property_key)
            
            # Lasso CRM API endpoint
            endpoint = f"{self.base_url}/v1/registrants"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Debug: Log the exact data being sent
            import json
            logger.info(f"🔍 Sending to Lasso CRM: {json.dumps(lead_data, indent=2)}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    headers=headers,
                    json=lead_data,
                    timeout=30.0
                )
                
                # Debug: Log response details
                logger.info(f"🔍 Lasso CRM Response Status: {response.status_code}")
                logger.info(f"🔍 Lasso CRM Response Headers: {dict(response.headers)}")
                logger.info(f"🔍 Lasso CRM Response Body: {response.text}")
                
                response.raise_for_status()
                result = response.json()
                
                lead_id = result.get("id") or result.get("lead_id")
                logger.info(f"Successfully created Lasso CRM lead {lead_id} for property {property_key}")
                
                return {
                    "success": True,
                    "lead_id": str(lead_id) if lead_id else None,
                    "response": result
                }
                
        except httpx.HTTPStatusError as e:
            error_msg = f"Lasso CRM API error: {e.response.status_code} - {e.response.text}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}",
                "details": e.response.text
            }
        except Exception as e:
            error_msg = f"Error creating Lasso CRM lead: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "Unknown error",
                "details": str(e)
            }
    
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
        # Get API key for this specific property
        api_key = self.get_property_api_key(property_key)
        if not api_key:
            logger.error(f"API key not configured for property {property_key}")
            return False
        
        try:
            # Prepare updated lead data
            lead_data = self.prepare_lead_data(customer_data, property_key)
            
            # Lasso CRM API endpoint (update with actual endpoint)
            endpoint = f"{self.base_url}/api/v1/leads/{lead_id}"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
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
    
    async def search_lead(self, phone: str, email: str = None, property_key: str = None) -> Optional[Dict[str, Any]]:
        """
        Search for existing lead in Lasso CRM.
        
        Args:
            phone: Phone number to search
            email: Email to search (optional)
            property_key: Property to search in (optional, searches all if None)
            
        Returns:
            Lead data if found, None otherwise
        """
        # If property_key is specified, search only in that property
        if property_key:
            api_key = self.get_property_api_key(property_key)
            if not api_key:
                logger.error(f"API key not configured for property {property_key}")
                return None
            return await self._search_lead_in_property(phone, email, property_key, api_key)
        
        # If no property specified, search in all configured properties
        for prop_key, prop_config in self.configured_properties.items():
            result = await self._search_lead_in_property(phone, email, prop_key, prop_config["api_key"])
            if result:
                return result
        
        return None
    
    async def _search_lead_in_property(self, phone: str, email: str, property_key: str, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Search for lead in a specific property.
        
        Args:
            phone: Phone number to search
            email: Email to search (optional)
            property_key: Property identifier
            api_key: API key for the property
            
        Returns:
            Lead data if found, None otherwise
        """
        
        try:
            # Normalize phone number
            normalized_phone = self.normalize_phone_number(phone)
            
            # Lasso CRM search endpoint
            endpoint = f"{self.base_url}/v1/registrants/search"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Search criteria
            search_criteria = {
                "lasso_uid": self.lasso_uid,  # Organization identifier
                "phone": normalized_phone,
                "property_id": self.PROPERTY_MAPPING[property_key]["id"]
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
            logger.error(f"Lasso CRM search error for property {property_key}: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error searching Lasso CRM lead in property {property_key}: {e}")
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
            # First, try to find existing lead in this specific property
            phone = customer_data.get("telefono", "")
            email = customer_data.get("email", "")
            
            existing_lead = await self.search_lead(phone, email, property_key)
            
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
        Validate if property key exists and is configured.
        
        Args:
            property_key: Property identifier
            
        Returns:
            True if valid and configured, False otherwise
        """
        return property_key.lower() in self.configured_properties

