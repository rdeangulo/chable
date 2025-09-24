# app/crm_integration.py

import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.crm_manager import CRMManager
from app.models import QualifiedLead

logger = logging.getLogger(__name__)

# Initialize CRM manager
crm_manager = CRMManager()


async def inject_qualified_lead_to_crm(
    db: Session, 
    lead: QualifiedLead, 
    property_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inject a qualified lead to Lasso CRM for the specified property.
    
    Args:
        db: Database session
        lead: QualifiedLead object
        property_key: Property key (if None, will try to determine from lead data)
        
    Returns:
        Dict with injection results
    """
    try:
        # Check if lead was already injected to CRM
        if lead.crm_injected and lead.crm_lead_id:
            logger.info(f"Lead {lead.id} already injected to CRM (ID: {lead.crm_lead_id}), updating instead")
            # Update existing lead instead of creating new one
            return await update_existing_lead_in_crm(db, lead, property_key)
        # Prepare customer data from qualified lead
        customer_data = {
            "nombre": lead.nombre,
            "email": lead.email,
            "telefono": lead.telefono,
            "fuente": lead.fuente,
            "motivo_interes": lead.motivo_interes,
            "urgencia_compra": lead.urgencia_compra,
            "tipo_propiedad": lead.tipo_propiedad,
            "presupuesto_min": lead.presupuesto_min,
            "presupuesto_max": lead.presupuesto_max,
            "desea_visita": lead.desea_visita,
            "desea_llamada": lead.desea_llamada,
            "desea_informacion": lead.desea_informacion,
            "ciudad_interes": lead.ciudad_interes,
            "proyecto_interes": lead.proyecto_interes,
            "sender_platform": "WhatsApp Bot"
        }
        
        # Determine property key if not provided
        if not property_key:
            property_key = _determine_property_from_lead(lead)
        
        if not property_key:
            return {
                "success": False,
                "error": "Could not determine property for lead injection"
            }
        
        # Inject to Lasso CRM
        result = await crm_manager.inject_lead_to_property(
            customer_data,
            property_key
        )
        
        if result.get("success"):
            # Mark lead as injected and store CRM lead ID
            lead.crm_injected = True
            lead.crm_lead_id = result.get("lead_id")
            db.commit()
            logger.info(f"Successfully injected qualified lead {lead.id} to {property_key} (CRM ID: {lead.crm_lead_id})")
        else:
            logger.error(f"Failed to inject qualified lead {lead.id} to {property_key}: {result.get('errors')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error injecting qualified lead to CRM: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def _determine_property_from_lead(lead: QualifiedLead) -> Optional[str]:
    """
    Determine property key from lead data.
    
    Args:
        lead: QualifiedLead object
        
    Returns:
        Property key or None if cannot determine
    """
    try:
        # Check if proyecto_interes is set
        if lead.proyecto_interes:
            proyecto = lead.proyecto_interes.lower()
            
            # Map project names to property keys
            project_mapping = {
                "costalegre": "costalegre",
                "residencias": "residencias",
                "valle de guadalupe": "valle_de_guadalupe",
                "yucatan": "yucatan",
                "yucatán": "yucatan"
            }
            
            for project_name, property_key in project_mapping.items():
                if project_name in proyecto:
                    return property_key
        
        # Check ciudad_interes for location-based mapping
        if lead.ciudad_interes:
            ciudad = lead.ciudad_interes.lower()
            
            # Map cities to properties
            city_mapping = {
                # Yucatan (Primary Focus) - Riviera Maya region
                "yucatan": "yucatan",
                "yucatán": "yucatan",
                "merida": "yucatan",
                "mérida": "yucatan",
                "riviera maya": "yucatan",
                "cancun": "yucatan",
                "cancún": "yucatan",
                "playa del carmen": "yucatan",
                "tulum": "yucatan",
                "cozumel": "yucatan",
                "quintana roo": "yucatan",
                "caribe": "yucatan",
                "caribbean": "yucatan",
                
                # Costalegre - Jalisco region
                "costalegre": "costalegre",
                "guadalajara": "costalegre",
                "puerto vallarta": "costalegre",
                "vallarta": "costalegre",
                "jalisco": "costalegre",
                
                
                # Valle de Guadalupe - Baja California region
                "guadalupe": "valle_de_guadalupe",
                "ensenada": "valle_de_guadalupe",
                "baja california": "valle_de_guadalupe",
                "valle": "valle_de_guadalupe",
                "vino": "valle_de_guadalupe",
                "wine": "valle_de_guadalupe"
            }
            
            for city_name, property_key in city_mapping.items():
                if city_name in ciudad:
                    return property_key
        
        # Default to residencias if no specific mapping found (general leads)
        logger.info(f"Could not determine specific property for lead, defaulting to 'residencias' (general leads)")
        return "residencias"
        
    except Exception as e:
        logger.error(f"Error determining property from lead: {e}")
        return None


async def inject_lead_to_multiple_properties(
    db: Session,
    lead: QualifiedLead,
    property_keys: list
) -> Dict[str, Any]:
    """
    Inject a qualified lead to multiple properties in Lasso CRM.
    
    Args:
        db: Database session
        lead: QualifiedLead object
        property_keys: List of property keys
        
    Returns:
        Dict with injection results
    """
    try:
        # Prepare customer data from qualified lead
        customer_data = {
            "nombre": lead.nombre,
            "email": lead.email,
            "telefono": lead.telefono,
            "fuente": lead.fuente,
            "motivo_interes": lead.motivo_interes,
            "urgencia_compra": lead.urgencia_compra,
            "tipo_propiedad": lead.tipo_propiedad,
            "presupuesto_min": lead.presupuesto_min,
            "presupuesto_max": lead.presupuesto_max,
            "desea_visita": lead.desea_visita,
            "desea_llamada": lead.desea_llamada,
            "desea_informacion": lead.desea_informacion,
            "ciudad_interes": lead.ciudad_interes,
            "proyecto_interes": lead.proyecto_interes,
            "sender_platform": "WhatsApp Bot"
        }
        
        # Inject to multiple properties in Lasso CRM
        result = await crm_manager.inject_lead_to_multiple_properties(
            customer_data,
            property_keys
        )
        
        if result.get("success"):
            logger.info(f"Successfully injected qualified lead {lead.id} to {result['successful_injections']} properties")
        else:
            logger.error(f"Failed to inject qualified lead {lead.id} to multiple properties: {result.get('errors')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error injecting qualified lead to multiple properties: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def get_available_properties() -> list:
    """Get list of available properties."""
    return crm_manager.get_available_properties()


def get_property_info(property_key: str) -> Optional[Dict[str, Any]]:
    """Get information about a specific property."""
    return crm_manager.get_property_info(property_key)


def validate_property_key(property_key: str) -> bool:
    """Validate if property key exists."""
    return crm_manager.validate_property_key(property_key)


async def update_existing_lead_in_crm(
    db: Session, 
    lead: QualifiedLead, 
    property_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update an existing lead in Lasso CRM.
    
    Args:
        db: Database session
        lead: QualifiedLead object with existing CRM ID
        property_key: Property key (if None, will try to determine from lead data)
        
    Returns:
        Dict with update results
    """
    try:
        if not lead.crm_lead_id:
            return {
                "success": False,
                "error": "No CRM lead ID found for update"
            }
        
        # Prepare customer data from qualified lead
        customer_data = {
            "nombre": lead.nombre,
            "email": lead.email,
            "telefono": lead.telefono,
            "fuente": lead.fuente,
            "motivo_interes": lead.motivo_interes,
            "urgencia_compra": lead.urgencia_compra,
            "tipo_propiedad": lead.tipo_propiedad,
            "presupuesto_min": lead.presupuesto_min,
            "presupuesto_max": lead.presupuesto_max,
            "desea_visita": lead.desea_visita,
            "desea_llamada": lead.desea_llamada,
            "desea_informacion": lead.desea_informacion,
            "ciudad_interes": lead.ciudad_interes,
            "proyecto_interes": lead.proyecto_interes,
            "sender_platform": "WhatsApp Bot"
        }
        
        # Determine property key if not provided
        if not property_key:
            property_key = _determine_property_from_lead(lead)
        
        if not property_key:
            return {
                "success": False,
                "error": "Could not determine property for lead update"
            }
        
        # Update in Lasso CRM
        result = await crm_manager.update_lead_to_property(
            lead.crm_lead_id,
            customer_data,
            property_key
        )
        
        if result.get("success"):
            logger.info(f"Successfully updated qualified lead {lead.id} in {property_key} (CRM ID: {lead.crm_lead_id})")
        else:
            logger.error(f"Failed to update qualified lead {lead.id} in {property_key}: {result.get('errors')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating qualified lead in CRM: {e}")
        return {
            "success": False,
            "error": str(e)
        }
