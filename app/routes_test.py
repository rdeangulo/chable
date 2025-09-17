# app/routes_test.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db_session
from app.services.crm_manager import CRMManager
from app.services.lasso_crm_service import LassoCRMService
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/test/crm-status")
async def test_crm_status():
    """Test CRM configuration status"""
    try:
        crm_manager = CRMManager()
        lasso_service = LassoCRMService()
        
        status = crm_manager.get_crm_status()
        
        return {
            "success": True,
            "crm_status": status,
            "lasso_uid": lasso_service.lasso_uid,
            "configured_properties": len(status.get("configured_properties", [])),
            "available_properties": len(status.get("available_properties", []))
        }
    except Exception as e:
        logger.error(f"Error testing CRM status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CRM test error: {str(e)}")

@router.get("/test/crm-properties")
async def test_crm_properties():
    """Test CRM property validation"""
    try:
        crm_manager = CRMManager()
        lasso_service = LassoCRMService()
        
        properties = ["yucatan", "costalegre", "valle_de_guadalupe", "residencias"]
        results = {}
        
        for prop in properties:
            is_valid = crm_manager.validate_property_key(prop)
            is_configured = lasso_service.is_property_configured(prop)
            api_key = lasso_service.get_property_api_key(prop)
            
            results[prop] = {
                "valid": is_valid,
                "configured": is_configured,
                "has_api_key": bool(api_key),
                "api_key_env": lasso_service.PROPERTY_MAPPING.get(prop, {}).get("api_key_env")
            }
        
        return {
            "success": True,
            "property_tests": results
        }
    except Exception as e:
        logger.error(f"Error testing CRM properties: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Property test error: {str(e)}")

@router.post("/test/crm-lead-injection")
async def test_crm_lead_injection(
    property_key: str = "yucatan",
    db: Session = Depends(get_db_session)
):
    """Test CRM lead injection"""
    try:
        crm_manager = CRMManager()
        
        # Test customer data
        test_customer_data = {
            "nombre": "Test User CRM",
            "telefono": "+573001234567",
            "email": "test.crm@example.com",
            "ciudad_interes": "Mérida",
            "tipo_propiedad": "residencia",
            "presupuesto_min": 500000,
            "presupuesto_max": 800000,
            "motivo_interes": "compra",
            "urgencia_compra": "alta",
            "desea_llamada": True,
            "desea_visita": True,
            "fuente": "Test API",
            "sender_platform": "Test",
            "thread_id": "test_thread_crm",
            "conversation_summary": "Test lead injection from API"
        }
        
        # Test lead injection
        result = await crm_manager.inject_lead_to_property(test_customer_data, property_key)
        
        return {
            "success": True,
            "injection_result": result,
            "test_data": test_customer_data
        }
    except Exception as e:
        logger.error(f"Error testing CRM lead injection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lead injection test error: {str(e)}")

@router.get("/test/crm-phone-normalization")
async def test_phone_normalization():
    """Test phone number normalization"""
    try:
        lasso_service = LassoCRMService()
        
        test_phones = [
            "+573001234567",
            "whatsapp:+573001234567",
            "3001234567",
            "+52 300 123 4567",
            "300-123-4567"
        ]
        
        results = {}
        for phone in test_phones:
            normalized = lasso_service.normalize_phone_number(phone)
            results[phone] = normalized
        
        return {
            "success": True,
            "phone_normalization_tests": results
        }
    except Exception as e:
        logger.error(f"Error testing phone normalization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Phone normalization test error: {str(e)}")

@router.get("/test/crm-full")
async def test_crm_full(db: Session = Depends(get_db_session)):
    """Run full CRM integration test"""
    try:
        crm_manager = CRMManager()
        lasso_service = LassoCRMService()
        
        # Test 1: CRM Status
        status = crm_manager.get_crm_status()
        
        # Test 2: Property validation
        properties = ["yucatan", "costalegre", "valle_de_guadalupe", "residencias"]
        property_tests = {}
        for prop in properties:
            property_tests[prop] = {
                "valid": crm_manager.validate_property_key(prop),
                "configured": lasso_service.is_property_configured(prop),
                "has_api_key": bool(lasso_service.get_property_api_key(prop))
            }
        
        # Test 3: Phone normalization
        test_phones = ["+573001234567", "whatsapp:+573001234567", "3001234567"]
        phone_tests = {}
        for phone in test_phones:
            phone_tests[phone] = lasso_service.normalize_phone_number(phone)
        
        # Test 4: Lead data preparation
        test_customer_data = {
            "nombre": "Test User Full",
            "telefono": "+573001234567",
            "email": "test.full@example.com",
            "ciudad_interes": "Mérida",
            "tipo_propiedad": "residencia",
            "presupuesto_min": 500000,
            "presupuesto_max": 800000,
            "motivo_interes": "compra",
            "urgencia_compra": "alta",
            "desea_llamada": True,
            "desea_visita": True,
            "fuente": "Test API Full",
            "sender_platform": "Test",
            "thread_id": "test_thread_full",
            "conversation_summary": "Full CRM test from API"
        }
        
        lead_data_tests = {}
        for prop in ["yucatan", "costalegre"]:
            if lasso_service.is_property_configured(prop):
                try:
                    lead_data = lasso_service.prepare_lead_data(test_customer_data, prop)
                    lead_data_tests[prop] = {
                        "success": True,
                        "property_id": lead_data.get("property_id"),
                        "contact_name": f"{lead_data.get('contact', {}).get('first_name', '')} {lead_data.get('contact', {}).get('last_name', '')}".strip(),
                        "phone": lead_data.get("contact", {}).get("phone"),
                        "email": lead_data.get("contact", {}).get("email")
                    }
                except Exception as e:
                    lead_data_tests[prop] = {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "test_results": {
                "crm_status": status,
                "property_tests": property_tests,
                "phone_normalization_tests": phone_tests,
                "lead_data_preparation_tests": lead_data_tests
            },
            "summary": {
                "lasso_enabled": status.get("lasso_enabled", False),
                "configured_properties": len(status.get("configured_properties", [])),
                "available_properties": len(status.get("available_properties", [])),
                "lasso_uid": lasso_service.lasso_uid
            }
        }
    except Exception as e:
        logger.error(f"Error in full CRM test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Full CRM test error: {str(e)}")
