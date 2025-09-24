# Add property selection webhook handler to existing main.py

@app.post("/property-selection")
async def handle_property_selection(
    request: Request, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Handle property selection from WhatsApp interactive buttons.
    """
    try:
        # Parse form data from Twilio webhook
        form_data = await request.form()
        logger.debug(f"Received property selection data: {form_data}")
        
        # Extract button payload
        button_payload = form_data.get("ButtonPayload")
        if not button_payload:
            logger.error("No ButtonPayload found in property selection request")
            return Response(content="", status_code=200)
        
        # Extract sender information
        whatsapp_number = form_data.get("From", "").split("whatsapp:")[-1]
        if not whatsapp_number:
            logger.error("No WhatsApp number found in property selection request")
            return Response(content="", status_code=200)
        
        # Map button payload to property key
        property_mapping = {
            "property_yucatan": "yucatan",
            "property_valle_guadalupe": "valle_de_guadalupe", 
            "property_costalegre": "costalegre",
            "property_mar_de_cortes": "mar_de_cortes"
        }
        
        selected_property = property_mapping.get(button_payload)
        if not selected_property:
            logger.error(f"Unknown property selection: {button_payload}")
            return Response(content="", status_code=200)
        
        # Get or create lead data from database
        lead_data = await get_lead_data_from_db(db, whatsapp_number)
        if not lead_data:
            logger.error(f"No lead data found for {whatsapp_number}")
            return Response(content="", status_code=200)
        
        # Handle property selection
        from app.execute_functions import select_property
        result = await select_property(
            phone_number=whatsapp_number,
            lead_data=lead_data,
            selected_property=selected_property
        )
        
        if result.get("success"):
            logger.info(f"Property selection handled successfully for {whatsapp_number}: {selected_property}")
        else:
            logger.error(f"Property selection failed for {whatsapp_number}: {result.get('error')}")
        
        return Response(content="", status_code=200)
        
    except Exception as e:
        logger.error(f"Error handling property selection: {e}")
        return Response(content="", status_code=200)

async def get_lead_data_from_db(db: Session, phone_number: str) -> Optional[Dict[str, Any]]:
    """
    Get lead data from database for property selection.
    """
    try:
        # Get the most recent qualified lead for this phone number
        lead = db.query(QualifiedLead).filter_by(telefono=phone_number).order_by(QualifiedLead.id.desc()).first()
        
        if not lead:
            return None
        
        return {
            "nombre": lead.nombre,
            "telefono": lead.telefono,
            "email": lead.email,
            "motivo_interes": lead.motivo_interes,
            "urgencia_compra": lead.urgencia_compra,
            "presupuesto_min": lead.presupuesto_min,
            "presupuesto_max": lead.presupuesto_max,
            "tipo_propiedad": lead.tipo_propiedad,
            "ciudad_interes": lead.ciudad_interes,
            "desea_visita": lead.desea_visita,
            "desea_llamada": lead.desea_llamada,
            "desea_informacion": lead.desea_informacion
        }
        
    except Exception as e:
        logger.error(f"Error getting lead data: {e}")
        return None