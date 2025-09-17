#!/usr/bin/env python3
"""
Direct Lead Injection Script for Lasso CRM
==========================================

This script allows you to directly inject leads to the Lasso CRM system
for the Yucatan project (ID: 24610).

Usage:
    python inject_lead_to_lasso.py

The script will prompt you for lead information and inject it directly
to the Lasso CRM system.
"""

import os
import sys
import json
import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Lasso CRM Configuration - Get from environment variables
LASSO_API_KEY = os.getenv("LASSO_API_KEY_YUCATAN")

# Project Configuration
PROJECT_ID = 24610  # Yucatan project
CLIENT_ID = 2589

# Lasso API Configuration
LASSO_BASE_URL = "https://api.lassocrm.com"
LASSO_LEADS_ENDPOINT = f"{LASSO_BASE_URL}/v1/registrants"


class LassoLeadInjector:
    """Handles direct lead injection to Lasso CRM."""
    
    def __init__(self, api_key: str, project_id: int, client_id: int):
        self.api_key = api_key
        self.project_id = project_id
        self.client_id = client_id
        self.base_url = LASSO_BASE_URL
        
    def create_lead_payload(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create the payload for Lasso CRM lead creation."""
        
        # Map our lead data to Lasso CRM format
        payload = {
            "firstName": lead_data.get("nombre", "").split()[0] if lead_data.get("nombre") else "",
            "lastName": " ".join(lead_data.get("nombre", "").split()[1:]) if lead_data.get("nombre") and len(lead_data.get("nombre", "").split()) > 1 else "",
            "email": lead_data.get("email", ""),
            "phone": lead_data.get("telefono", ""),
            "source": lead_data.get("fuente", "WhatsApp Bot"),
            "projectId": self.project_id,
            "notes": self._create_lead_notes(lead_data),
            "customFields": self._create_custom_fields(lead_data),
            "tags": self._create_tags(lead_data)
        }
        
        return payload
    
    def _create_lead_notes(self, lead_data: Dict[str, Any]) -> str:
        """Create comprehensive notes for the lead."""
        notes = []
        
        if lead_data.get("motivo_interes"):
            notes.append(f"Motivo de interés: {lead_data['motivo_interes']}")
        
        if lead_data.get("urgencia_compra"):
            notes.append(f"Urgencia de compra: {lead_data['urgencia_compra']}")
        
        if lead_data.get("tipo_propiedad"):
            notes.append(f"Tipo de propiedad: {lead_data['tipo_propiedad']}")
        
        if lead_data.get("presupuesto_min") or lead_data.get("presupuesto_max"):
            budget = f"Presupuesto: ${lead_data.get('presupuesto_min', 'N/A')} - ${lead_data.get('presupuesto_max', 'N/A')}"
            notes.append(budget)
        
        if lead_data.get("ciudad_interes"):
            notes.append(f"Ciudad de interés: {lead_data['ciudad_interes']}")
        
        if lead_data.get("proyecto_interes"):
            notes.append(f"Proyecto de interés: {lead_data['proyecto_interes']}")
        
        # Add preferences
        preferences = []
        if lead_data.get("desea_visita"):
            preferences.append("Desea visita")
        if lead_data.get("desea_llamada"):
            preferences.append("Desea llamada")
        if lead_data.get("desea_informacion"):
            preferences.append("Desea información")
        
        if preferences:
            notes.append(f"Preferencias: {', '.join(preferences)}")
        
        if lead_data.get("metodo_contacto_preferido"):
            notes.append(f"Método de contacto preferido: {lead_data['metodo_contacto_preferido']}")
        
        notes.append(f"Fecha de captura: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        notes.append(f"Plataforma: {lead_data.get('sender_platform', 'WhatsApp Bot')}")
        
        return "\n".join(notes)
    
    def _create_custom_fields(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create custom fields for the lead."""
        custom_fields = {}
        
        # Map common fields to Lasso custom fields
        field_mapping = {
            "motivo_interes": "Motivo de Interés",
            "urgencia_compra": "Urgencia de Compra",
            "tipo_propiedad": "Tipo de Propiedad",
            "presupuesto_min": "Presupuesto Mínimo",
            "presupuesto_max": "Presupuesto Máximo",
            "ciudad_interes": "Ciudad de Interés",
            "proyecto_interes": "Proyecto de Interés",
            "metodo_contacto_preferido": "Método de Contacto Preferido"
        }
        
        for our_field, lasso_field in field_mapping.items():
            if lead_data.get(our_field):
                custom_fields[lasso_field] = lead_data[our_field]
        
        return custom_fields
    
    def _create_tags(self, lead_data: Dict[str, Any]) -> list:
        """Create tags for the lead."""
        tags = ["WhatsApp Bot", "Yucatan"]
        
        if lead_data.get("fuente"):
            tags.append(lead_data["fuente"])
        
        if lead_data.get("proyecto_interes"):
            tags.append(lead_data["proyecto_interes"])
        
        if lead_data.get("urgencia_compra"):
            tags.append(f"Urgencia-{lead_data['urgencia_compra']}")
        
        return tags
    
    async def inject_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inject a lead to Lasso CRM."""
        try:
            # Create the payload
            payload = self.create_lead_payload(lead_data)
            
            logger.info(f"Creating lead payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            
            # Prepare headers
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            # Make the API call
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    LASSO_LEADS_ENDPOINT,
                    json=payload,
                    headers=headers
                )
                
                logger.info(f"Lasso API Response Status: {response.status_code}")
                logger.info(f"Lasso API Response: {response.text}")
                
                if response.status_code in [200, 201]:
                    response_data = response.json()
                    return {
                        "success": True,
                        "lead_id": response_data.get("id"),
                        "message": "Lead successfully injected to Lasso CRM",
                        "response": response_data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Lasso API error: {response.status_code} - {response.text}",
                        "status_code": response.status_code
                    }
                    
        except Exception as e:
            logger.error(f"Error injecting lead to Lasso CRM: {str(e)}")
            return {
                "success": False,
                "error": f"Exception occurred: {str(e)}"
            }


def get_lead_data_from_user() -> Dict[str, Any]:
    """Get lead data from user input."""
    print("\n" + "="*60)
    print("🏠 LASSO CRM LEAD INJECTION - YUCATAN PROJECT")
    print("="*60)
    print(f"Project ID: {PROJECT_ID}")
    print(f"Client ID: {CLIENT_ID}")
    print("="*60)
    
    lead_data = {}
    
    # Required fields
    print("\n📝 REQUIRED INFORMATION:")
    lead_data["nombre"] = input("👤 Full Name: ").strip()
    lead_data["telefono"] = input("📞 Phone Number: ").strip()
    lead_data["email"] = input("📧 Email: ").strip()
    
    # Optional fields
    print("\n📋 OPTIONAL INFORMATION:")
    lead_data["fuente"] = input("🔍 Source (default: WhatsApp Bot): ").strip() or "WhatsApp Bot"
    lead_data["motivo_interes"] = input("💭 Reason for Interest: ").strip()
    lead_data["urgencia_compra"] = input("⏰ Purchase Urgency (inmediata/esta_semana/este_mes/sin_urgencia): ").strip()
    lead_data["tipo_propiedad"] = input("🏡 Property Type: ").strip()
    lead_data["presupuesto_min"] = input("💰 Min Budget: ").strip()
    lead_data["presupuesto_max"] = input("💰 Max Budget: ").strip()
    lead_data["ciudad_interes"] = input("🌍 City of Interest: ").strip()
    lead_data["proyecto_interes"] = input("🏗️ Project Interest (default: Yucatan): ").strip() or "Yucatan"
    lead_data["metodo_contacto_preferido"] = input("📱 Preferred Contact Method (default: WhatsApp): ").strip() or "WhatsApp"
    
    # Preferences
    print("\n✅ PREFERENCES:")
    lead_data["desea_visita"] = input("🏠 Wants Visit? (y/n): ").strip().lower() == 'y'
    lead_data["desea_llamada"] = input("📞 Wants Call? (y/n): ").strip().lower() == 'y'
    lead_data["desea_informacion"] = input("📄 Wants Information? (y/n): ").strip().lower() == 'y'
    
    # Platform info
    lead_data["sender_platform"] = "WhatsApp Bot"
    
    return lead_data


async def main():
    """Main function to run the lead injection."""
    try:
        # Check if API key is available
        if not LASSO_API_KEY:
            print("❌ Error: LASSO_API_KEY_YUCATAN environment variable not set!")
            print("Please set the environment variable with your Lasso API key.")
            return
        
        # Initialize the injector
        injector = LassoLeadInjector(LASSO_API_KEY, PROJECT_ID, CLIENT_ID)
        
        # Get lead data from user
        lead_data = get_lead_data_from_user()
        
        # Validate required fields
        if not lead_data["nombre"] or not lead_data["telefono"]:
            print("❌ Error: Name and phone number are required!")
            return
        
        print("\n" + "="*60)
        print("🚀 INJECTING LEAD TO LASSO CRM...")
        print("="*60)
        
        # Inject the lead
        result = await injector.inject_lead(lead_data)
        
        # Display results
        print("\n" + "="*60)
        print("📊 INJECTION RESULTS")
        print("="*60)
        
        if result["success"]:
            print("✅ SUCCESS!")
            print(f"📋 Lead ID: {result.get('lead_id', 'N/A')}")
            print(f"💬 Message: {result['message']}")
            if result.get("response"):
                print(f"📄 Response: {json.dumps(result['response'], indent=2, ensure_ascii=False)}")
        else:
            print("❌ FAILED!")
            print(f"🚨 Error: {result['error']}")
            if result.get("status_code"):
                print(f"📊 Status Code: {result['status_code']}")
        
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        logger.error(f"Unexpected error in main: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
