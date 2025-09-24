# app/services/crm_manager.py

import os
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.services.lasso_crm_service import LassoCRMService

logger = logging.getLogger(__name__)


class CRMManager:
    """CRM manager that handles Lasso CRM integration."""
    
    def __init__(self):
        """Initialize CRM manager with Lasso service."""
        self.lasso_service = LassoCRMService()
        self.lasso_enabled = len(self.lasso_service.configured_properties) > 0
        
        logger.info(f"CRM Manager initialized - Lasso: {self.lasso_enabled} ({len(self.lasso_service.configured_properties)} properties configured)")
    
    def get_available_properties(self) -> List[Dict[str, Any]]:
        """Get all available properties from Lasso CRM."""
        return self.lasso_service.get_all_properties()
    
    def get_property_info(self, property_key: str) -> Optional[Dict[str, Any]]:
        """Get property information by key."""
        return self.lasso_service.get_property_info(property_key)
    
    def validate_property_key(self, property_key: str) -> bool:
        """Validate if property key exists."""
        return self.lasso_service.validate_property_key(property_key)
    
    async def inject_lead_to_property(
        self, 
        customer_data: Dict[str, Any], 
        property_key: str
    ) -> Dict[str, Any]:
        """
        Inject lead to specified property in Lasso CRM.
        
        Args:
            customer_data: Customer information
            property_key: Property identifier
            
        Returns:
            Dict with results from Lasso CRM
        """
        results = {
            "success": False,
            "property_key": property_key,
            "property_info": self.get_property_info(property_key),
            "lasso": None,
            "errors": []
        }
        
        # Validate property key
        if not self.validate_property_key(property_key):
            error_msg = f"Invalid property key: {property_key}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results
        
        # Get property info
        property_info = self.get_property_info(property_key)
        if not property_info:
            error_msg = f"Property info not found for: {property_key}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            return results
        
        results["property_info"] = property_info
        
        # Prepare customer data with property information
        enhanced_customer_data = customer_data.copy()
        enhanced_customer_data.update({
            "proyecto_interes": property_info["name"],
            "property_id": property_info["id"],
            "property_display_name": property_info["display_name"]
        })
        
        # Inject to Lasso CRM
        if self.lasso_enabled:
            # Check if this specific property is configured
            if self.lasso_service.is_property_configured(property_key):
                try:
                    lasso_result = await self._inject_to_lasso(enhanced_customer_data, property_key)
                    results["lasso"] = lasso_result
                    if lasso_result.get("success"):
                        results["success"] = True
                except Exception as e:
                    error_msg = f"Lasso CRM injection error for property {property_key}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    results["lasso"] = {"success": False, "error": error_msg}
            else:
                error_msg = f"Property {property_key} is not configured in Lasso CRM (API key not set)"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["lasso"] = {"success": False, "error": error_msg}
        else:
            error_msg = "Lasso CRM is not configured (no API keys set for any property)"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    
    async def _inject_to_lasso(self, customer_data: Dict[str, Any], property_key: str) -> Dict[str, Any]:
        """Inject lead to Lasso CRM."""
        try:
            # Create or update Lasso CRM lead
            lead_id = await self.lasso_service.create_or_update_lead(customer_data, property_key)
            
            if lead_id:
                property_info = self.get_property_info(property_key)
                return {
                    "success": True,
                    "lead_id": lead_id,
                    "property_id": property_info["id"],
                    "property_name": property_info["name"],
                    "message": f"Successfully created/updated Lasso CRM lead for {property_info['display_name']}"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create/update Lasso CRM lead"
                }
                
        except Exception as e:
            logger.error(f"Lasso CRM injection error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def inject_lead_to_multiple_properties(
        self, 
        customer_data: Dict[str, Any], 
        property_keys: List[str]
    ) -> Dict[str, Any]:
        """
        Inject lead to multiple properties in Lasso CRM.
        
        Args:
            customer_data: Customer information
            property_keys: List of property identifiers
            
        Returns:
            Dict with results for each property
        """
        results = {
            "success": False,
            "total_properties": len(property_keys),
            "successful_injections": 0,
            "failed_injections": 0,
            "property_results": {},
            "errors": []
        }
        
        for property_key in property_keys:
            try:
                property_result = await self.inject_lead_to_property(customer_data, property_key)
                results["property_results"][property_key] = property_result
                
                if property_result.get("success"):
                    results["successful_injections"] += 1
                else:
                    results["failed_injections"] += 1
                    
            except Exception as e:
                error_msg = f"Error injecting to property {property_key}: {str(e)}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                results["property_results"][property_key] = {
                    "success": False,
                    "error": error_msg
                }
                results["failed_injections"] += 1
        
        # Overall success if at least one injection succeeded
        results["success"] = results["successful_injections"] > 0
        
        return results
    
    def get_crm_status(self) -> Dict[str, Any]:
        """Get status of Lasso CRM service."""
        configured_properties = []
        for prop_key, prop_config in self.lasso_service.configured_properties.items():
            configured_properties.append({
                "key": prop_key,
                "name": prop_config["property_info"]["name"],
                "display_name": prop_config["property_info"]["display_name"],
                "id": prop_config["property_info"]["id"],
                "api_key_env": prop_config["property_info"]["api_key_env"]
            })
        
        return {
            "lasso_enabled": self.lasso_enabled,
            "lasso_uid": self.lasso_service.lasso_uid,
            "configured_properties": configured_properties,
            "total_configured_properties": len(configured_properties),
            "available_properties": self.get_available_properties(),
            "total_properties": len(self.get_available_properties())
        }
    
    async def update_lead_to_property(
        self, 
        crm_lead_id: str,
        customer_data: Dict[str, Any], 
        property_key: str
    ) -> Dict[str, Any]:
        """
        Update existing lead in specified property in Lasso CRM.
        
        Args:
            crm_lead_id: Existing CRM lead ID
            customer_data: Updated customer information
            property_key: Property identifier
            
        Returns:
            Dict with results from Lasso CRM
        """
        results = {
            "success": False,
            "errors": [],
            "lasso_result": None
        }
        
        try:
            if not self.lasso_enabled:
                results["errors"].append("Lasso CRM not enabled")
                return results
            
            if not self.lasso_service.validate_property_key(property_key):
                results["errors"].append(f"Invalid property key: {property_key}")
                return results
            
            # Update lead in Lasso CRM
            lasso_result = await self.lasso_service.update_lead(crm_lead_id, customer_data, property_key)
            
            if lasso_result.get("success"):
                results["success"] = True
                results["lasso_result"] = lasso_result
                logger.info(f"Successfully updated lead {crm_lead_id} to {property_key}")
            else:
                error_msg = lasso_result.get("error", "Unknown error")
                results["errors"].append(f"Failed to update lead in Lasso CRM: {error_msg}")
                
        except Exception as e:
            error_msg = f"Error updating lead to property {property_key}: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results

