# app/routes_crm.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from app.db import get_db
from app.services.crm_manager import CRMManager

logger = logging.getLogger(__name__)

# Create router for CRM endpoints
crm_router = APIRouter(prefix="/api/crm", tags=["crm"])

# Initialize CRM manager
crm_manager = CRMManager()


class LeadInjectionRequest(BaseModel):
    """Request model for lead injection."""
    customer_data: Dict[str, Any]
    property_key: str


class MultiPropertyLeadRequest(BaseModel):
    """Request model for multi-property lead injection."""
    customer_data: Dict[str, Any]
    property_keys: List[str]


@crm_router.get("/status")
async def get_crm_status():
    """Get status of available CRM services."""
    try:
        status = crm_manager.get_crm_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting CRM status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@crm_router.get("/properties")
async def get_available_properties():
    """Get all available properties."""
    try:
        properties = crm_manager.get_available_properties()
        return {
            "success": True,
            "data": {
                "properties": properties,
                "total": len(properties)
            }
        }
    except Exception as e:
        logger.error(f"Error getting properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@crm_router.get("/properties/{property_key}")
async def get_property_info(property_key: str):
    """Get information about a specific property."""
    try:
        property_info = crm_manager.get_property_info(property_key)
        
        if not property_info:
            raise HTTPException(status_code=404, detail=f"Property '{property_key}' not found")
        
        return {
            "success": True,
            "data": property_info
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting property info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@crm_router.post("/inject-lead")
async def inject_lead_to_property(request: LeadInjectionRequest):
    """Inject a lead to a specific property."""
    try:
        # Validate property key
        if not crm_manager.validate_property_key(request.property_key):
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid property key: {request.property_key}"
            )
        
        # Inject lead to Lasso CRM
        result = await crm_manager.inject_lead_to_property(
            request.customer_data,
            request.property_key
        )
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Lead successfully injected to {request.property_key}",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "Lead injection failed",
                "data": result,
                "errors": result.get("errors", [])
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error injecting lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@crm_router.post("/inject-lead-multiple")
async def inject_lead_to_multiple_properties(request: MultiPropertyLeadRequest):
    """Inject a lead to multiple properties."""
    try:
        # Validate property keys
        invalid_keys = []
        for key in request.property_keys:
            if not crm_manager.validate_property_key(key):
                invalid_keys.append(key)
        
        if invalid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid property keys: {invalid_keys}"
            )
        
        # Inject lead to multiple properties in Lasso CRM
        result = await crm_manager.inject_lead_to_multiple_properties(
            request.customer_data,
            request.property_keys
        )
        
        return {
            "success": result.get("success", False),
            "message": f"Lead injection completed: {result['successful_injections']}/{result['total_properties']} successful",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error injecting lead to multiple properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@crm_router.post("/test-injection")
async def test_lead_injection(
    property_key: str = Query(..., description="Property key to test")
):
    """Test lead injection with sample data."""
    try:
        # Validate property key
        if not crm_manager.validate_property_key(property_key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid property key: {property_key}"
            )
        
        # Sample customer data for testing
        test_customer_data = {
            "nombre": "Test Customer",
            "email": "test@example.com",
            "telefono": "+1234567890",
            "fuente": "Test API",
            "motivo_interes": "Test injection",
            "urgencia_compra": "medio",
            "tipo_propiedad": "Apartamento",
            "presupuesto_min": 100000,
            "presupuesto_max": 200000,
            "desea_visita": True,
            "desea_llamada": False,
            "desea_informacion": True,
            "sender_platform": "API Test"
        }
        
        # Inject test lead to Lasso CRM
        result = await crm_manager.inject_lead_to_property(
            test_customer_data,
            property_key
        )
        
        return {
            "success": result.get("success", False),
            "message": f"Test lead injection for {property_key}",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in test injection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@crm_router.get("/properties/{property_key}/test")
async def test_property_connection(property_key: str):
    """Test connection to a specific property."""
    try:
        # Get property info
        property_info = crm_manager.get_property_info(property_key)
        
        if not property_info:
            raise HTTPException(status_code=404, detail=f"Property '{property_key}' not found")
        
        # Test with minimal data
        test_data = {
            "nombre": "Connection Test",
            "email": "test@connection.com",
            "telefono": "+1234567890",
            "fuente": "Connection Test",
            "motivo_interes": "Testing connection"
        }
        
        # Try to inject test lead to Lasso CRM
        result = await crm_manager.inject_lead_to_property(
            test_data,
            property_key
        )
        
        return {
            "success": result.get("success", False),
            "message": f"Connection test for {property_key}",
            "property_info": property_info,
            "test_result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing property connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))

