# app/main.py

import os
import re
import json
import httpx
import asyncio
import time
from fastapi import FastAPI, Depends, Request, BackgroundTasks, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAI
from app.db import get_db
from app.models import Conversation, Thread, CustomerInfo, QualifiedLead, Message
from app.utils import (
    logger,
    send_message,
    transcribe_audio,
    send_twilio_media_message,
    extract_media_from_response,
    clean_repeated_text,
    get_debounced_message,
    cleanup_message_buffer,
    is_number_blocked,
    auto_inject_missing_lead,
    verify_and_fix_missing_leads,
)
from app.services.twilio_service import TwilioService
from app.execute_functions import execute_function, enviar_foto
from datetime import datetime, timezone
from fastapi.staticfiles import StaticFiles
from app.routes import router
from app.routes_crm import crm_router
import logging
import colorama
from colorama import Fore, Style
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys
from typing import Optional, Dict, Any

# Add the parent directory to the path to import single_ai_handler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from single_ai_handler import SingleAIHandler

# Initialize colorama for colored output
colorama.init()

# Pydantic model for web widget messages
class WebWidgetMessage(BaseModel):
    Body: str
    From: str
    To: str
    Platform: str = "web"

# Initialize logger with colors
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""

    def format(self, record):
        if record.levelno == logging.ERROR:
            color = Fore.RED
        elif record.levelno == logging.WARNING:
            color = Fore.YELLOW
        elif record.levelno == logging.INFO:
            color = Fore.GREEN
        else:
            color = Fore.WHITE

        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

# Configure logger with colors
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(
    ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get store ID from environment or use default
STORE_ID = os.getenv("STORE_ID", "residencias_chable_default")

# Initialize the single AI handler
ai_handler = SingleAIHandler(STORE_ID)

app = FastAPI(title="Residencias Chable - Multi-Channel AI Assistant")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routers
app.include_router(router, prefix="/api", tags=["api"])
app.include_router(crm_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def index():
    return {"status": "working", "version": "2.0.0", "ai_system": "single_handler"}

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

@app.post("/message")
async def process_message(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Process incoming messages from Twilio webhook (WhatsApp).
    """
    # Generate request ID for tracking
    import uuid
    request_id = str(uuid.uuid4())[:8]
    
    try:
        logger.info(f"[{request_id}] Starting WhatsApp message processing")
        twilio_service = TwilioService()

        # Parse form data from Twilio webhook
        form_data = await request.form()
        logger.info(f"[{request_id}] Received form data with {len(form_data)} fields")
        logger.debug(f"[{request_id}] Form data: {dict(form_data)}")
        
        # Quick validation and early response to prevent timeouts
        message_sid = form_data.get("MessageSid")
        if not message_sid:
            logger.error(f"[{request_id}] No MessageSid found in request")
            return Response(content="", status_code=200)
        
        logger.info(f"[{request_id}] Processing message SID: {message_sid}")

        # Extract sender information
        whatsapp_number = form_data.get("From", "").split("whatsapp:")[-1]
        if not whatsapp_number:
            logger.error(f"[{request_id}] No WhatsApp number found in request")
            return Response(content="", status_code=200)

        profile_name = form_data.get("ProfileName", "").strip()
        logger.info(f"[{request_id}] Processing message from {whatsapp_number} (Profile: {profile_name})")

        # Drop message early if number is blocked
        if is_number_blocked(whatsapp_number):
            logger.info(f"[{request_id}] Ignoring message from blocked number {whatsapp_number}")
            return Response(content="", status_code=200)

        # Determine platform (default to WhatsApp)
        platform = "WhatsApp"
        sender_info = {"number": whatsapp_number, "platform": platform}

        # Extract referral metadata from WhatsApp webhook
        referral_metadata = {
            "referral_source_type": form_data.get("ReferralSourceType"),
            "referral_source_id": form_data.get("ReferralSourceId"),
            "referral_source_url": form_data.get("ReferralSourceUrl"),
            "referral_header": form_data.get("ReferralHeader"),
            "referral_body": form_data.get("ReferralBody"),
            "ctwa_clid": form_data.get("ctwa_clid"),
            "button_text": form_data.get("ButtonText"),
            "button_payload": form_data.get("ButtonPayload"),
        }
        
        # Log referral metadata if present
        if any(referral_metadata.values()):
            logger.info(f"Referral metadata for {whatsapp_number}: {referral_metadata}")
        else:
            logger.info(f"No referral metadata found for {whatsapp_number}")
            
        # Log ALL form data for debugging (remove this in production)
        logger.debug(f"All form data received: {dict(form_data)}")

        # Extract message content
        num_media = int(form_data.get("NumMedia", 0))
        body = form_data.get("Body", "").strip()

        if not body and num_media == 0:
            logger.error(f"[{request_id}] No message content found")
            return Response(content="", status_code=200)

        # Clean message to remove duplicated text
        body = clean_repeated_text(body)
        logger.info(f"[{request_id}] Message content: '{body}' (Media: {num_media})")

        # Handle media messages (including non-audio)
        if num_media > 0:
            media_content_type = form_data.get("MediaContentType0")
            media_url = form_data.get("MediaUrl0")
            
            if media_content_type and "audio" in media_content_type.lower():
                # Handle voice notes
                transcription = await transcribe_audio(media_url)

                if transcription:
                    body = transcription
                    logger.info(f"Transcribed audio: {body}")
                else:
                    error_msg = "No pude transcribir tu mensaje de voz. Por favor, envía un mensaje de texto."
                    sid = send_message(whatsapp_number, error_msg)
                    twilio_service.log_message(
                        db=db,
                        direction="outbound",
                        from_number=os.getenv("TWILIO_WHATSAPP_NUMBER", ""),
                        to_number=whatsapp_number,
                        message_body=error_msg,
                        message_sid=sid,
                        status="sent",
                        thread_id=None,
                        response_time=None,
                    )
                    return Response(content="", status_code=200)
            else:
                # Handle images, PDFs, and other media
                logger.info(f"Received media: {media_content_type} - {media_url}")
                
                # Determine media type
                if media_content_type:
                    if "image" in media_content_type.lower():
                        media_description = f"[IMAGEN_RECIBIDA: {media_url}]"
                    elif "pdf" in media_content_type.lower() or media_content_type.lower() == "application/pdf":
                        media_description = f"[PDF_RECIBIDO: {media_url}]"
                    else:
                        media_description = f"[ARCHIVO_RECIBIDO: {media_url} - tipo: {media_content_type}]"
                else:
                    media_description = f"[ARCHIVO_RECIBIDO: {media_url}]"
                
                # Combine text message (if any) with media description
                if body:
                    body = f"{body} {media_description}"
                else:
                    body = media_description
                
                logger.info(f"Processing media message: {body}")

        # Apply message debouncing
        debounced_message, final_message_sid, should_process = (
            await get_debounced_message(whatsapp_number, body, message_sid)
        )

        if not should_process:
            # Message is being buffered, return early
            return Response(content="", status_code=200)

        # Check if this message has already been processed
        existing_message = (
            db.query(Conversation).filter_by(message_sid=final_message_sid).first()
        )
        if existing_message:
            logger.info(f"Message {final_message_sid} has already been processed")
            return Response(content="", status_code=200)

        # Find or create a thread for this user
        thread_record = db.query(Thread).filter_by(sender=whatsapp_number).first()

        if thread_record:
            thread_id = thread_record.thread_id
            logger.info(f"Using existing thread {thread_id} for {whatsapp_number}")
            # Update last conversation timestamp
            thread_record.last_conversation_at = datetime.now()
            if profile_name and not thread_record.sender_display_name:
                thread_record.sender_display_name = profile_name
            
            # Store referral metadata if this is the first time we see it and fields are empty
            updated = False
            for key, value in referral_metadata.items():
                if value and getattr(thread_record, key, None) in (None, ""):
                    setattr(thread_record, key, value)
                    updated = True
                    logger.info(f"Updated thread {thread_id} with {key}: {value}")
            
            if updated:
                db.commit()
            else:
                db.commit()  # Commit the timestamp update
        else:
            # Create a new thread
            thread = client.beta.threads.create()
            thread_id = thread.id
            thread_record = Thread(
                sender=whatsapp_number,
                sender_platform=platform,
                thread_id=thread_id,
                sender_display_name=profile_name or None,
                **{k: v for k, v in referral_metadata.items() if v}  # Add referral metadata if present
            )
            db.add(thread_record)
            db.commit()
            logger.info(f"Created new thread {thread_id} for {whatsapp_number}")
            if any(referral_metadata.values()):
                logger.info(f"Thread {thread_id} created with referral metadata: {referral_metadata}")

        # Log inbound message
        inbound_log = twilio_service.log_message(
            db=db,
            direction="inbound",
            from_number=whatsapp_number,
            to_number=os.getenv("TWILIO_WHATSAPP_NUMBER", ""),
            message_body=debounced_message,
            message_sid=final_message_sid,
            status=form_data.get("SmsStatus"),
            thread_id=thread_record.id,
        )

        if thread_record.is_paused:
            logger.info(
                f"Thread {thread_id} is paused; storing message without AI response"
            )
            response = ""
        else:
            # Process message through new AI handler with timeout protection
            try:
                import asyncio
                from app.timeout_util import with_timeout
                
                logger.info(f"[{request_id}] Starting AI processing for message: '{debounced_message[:100]}...'")
                
                # Add timeout to prevent long delays
                @with_timeout(10)  # 10 second timeout
                async def process_ai_message():
                    return ai_handler.process_message(
                        debounced_message, 
                        model_speed="balanced", 
                        db=db, 
                        sender_info=sender_info
                    )
                
                response = asyncio.run(process_ai_message())
                logger.info(f"[{request_id}] AI response generated: '{response[:100]}...'")
            except Exception as ai_error:
                logger.error(f"[{request_id}] AI processing timeout or error: {ai_error}")
                response = "Lo siento, hubo un problema técnico. Por favor, intenta de nuevo."

            media_url, media_type, cleaned_message = extract_media_from_response(
                response
            )

            if media_url:
                logger.info(f"[{request_id}] Sending {media_type} media to {whatsapp_number}")
                sid = send_twilio_media_message(
                    whatsapp_number, media_url, cleaned_message, media_type
                )
                logger.info(f"[{request_id}] Sent {media_type} message to {whatsapp_number} (SID: {sid})")
                twilio_service.log_message(
                    db=db,
                    direction="outbound",
                    from_number=os.getenv("TWILIO_WHATSAPP_NUMBER", ""),
                    to_number=whatsapp_number,
                    message_body=cleaned_message,
                    message_sid=sid,
                    status="sent",
                    thread_id=thread_record.id,
                    response_time=int((datetime.now(timezone.utc) - inbound_log.created_at).total_seconds()),
                )
            else:
                logger.info(f"[{request_id}] Sending text message to {whatsapp_number}")
                sid = send_message(whatsapp_number, response)
                logger.info(f"[{request_id}] Sent text message to {whatsapp_number} (SID: {sid})")
                twilio_service.log_message(
                    db=db,
                    direction="outbound",
                    from_number=os.getenv("TWILIO_WHATSAPP_NUMBER", ""),
                    to_number=whatsapp_number,
                    message_body=response,
                    message_sid=sid,
                    status="sent",
                    thread_id=thread_record.id,
                    response_time=int((datetime.now(timezone.utc) - inbound_log.created_at).total_seconds()),
                )

        # Store the conversation in the database
        try:
            conversation = Conversation(
                sender=whatsapp_number,
                sender_platform=platform,
                message=debounced_message,  # Store the debounced message
                response=response,
                thread_id=thread_record.id,
                message_sid=final_message_sid,
            )
            db.add(conversation)

            # Store individual messages
            db.add_all(
                [
                    Message(
                        thread_id=thread_record.id,
                        role="user",
                        content=debounced_message,
                        message_sid=final_message_sid,
                    ),
                    Message(
                        thread_id=thread_record.id,
                        role="assistant",
                        content=response,
                    ),
                ]
            )
            db.commit()
            logger.info(f"Stored conversation for {whatsapp_number}")
            
            # Check for special delete command (simplified)
            if debounced_message.strip().lower() == "borrar123borrar":
                logger.info(f"Delete command received for {whatsapp_number}")
                # Note: Full delete functionality can be implemented later
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")

        # Create or update lead immediately with available information
        try:
            logger.info(f"[{request_id}] Starting lead creation/update process")
            await create_or_update_lead_immediately(db, thread_record, debounced_message, whatsapp_number, profile_name)
            logger.info(f"[{request_id}] Lead creation/update completed successfully")
        except Exception as e:
            logger.error(f"[{request_id}] Error in lead creation: {e}")

        logger.info(f"[{request_id}] Message processing completed successfully")
        return Response(content="", status_code=200)

    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")
        return Response(content="", status_code=500)

@app.post("/web-widget/message")
async def process_web_widget_message(
    message: WebWidgetMessage, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Process messages from the web widget.
    """
    try:
        # Extract message data
        visitor_id = message.From
        body = message.Body.strip()
        platform = message.Platform

        if not body:
            return JSONResponse(
                content={"error": "No message content provided"}, 
                status_code=400
            )

        logger.info(f"Received web widget message from {visitor_id}: {body}")

        # Find or create a thread for this visitor
        thread_record = db.query(Thread).filter_by(sender=visitor_id).first()

        if thread_record:
            thread_id = thread_record.thread_id
            logger.info(f"Using existing thread {thread_id} for {visitor_id}")
            # Update last conversation timestamp
            thread_record.last_conversation_at = datetime.now()
            db.commit()
        else:
            # Create a new thread
            thread = client.beta.threads.create()
            thread_id = thread.id
            thread_record = Thread(
                sender=visitor_id,
                sender_platform=platform,
                thread_id=thread_id,
                sender_display_name=f"Web Visitor ({visitor_id[:8]}...)",
            )
            db.add(thread_record)
            db.commit()
            logger.info(f"Created new thread {thread_id} for {visitor_id}")

        # Prepare sender info
        sender_info = {"number": visitor_id, "platform": platform}

        # Process message through new AI handler
        response = ai_handler.process_message(body, model_speed="balanced")

        # Store the conversation in the database
        try:
            conversation = Conversation(
                sender=visitor_id,
                sender_platform=platform,
                message=body,
                response=response,
                thread_id=thread_record.id,
            )
            db.add(conversation)

            # Store individual messages
            db.add_all([
                Message(
                    thread_id=thread_record.id,
                    role="user",
                    content=body,
                ),
                Message(
                    thread_id=thread_record.id,
                    role="assistant",
                    content=response,
                ),
            ])
            db.commit()
            logger.info(f"Stored web widget conversation for {visitor_id}")
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
        
        return JSONResponse(content={
            "success": True,
            "response": response,
            "thread_id": thread_id
        })
        
    except Exception as e:
        logger.error(f"Error processing web widget message: {str(e)}")
        return JSONResponse(
            content={"error": "Internal server error"}, 
            status_code=500
        )

# Add other necessary endpoints here...

async def create_or_update_lead_immediately(db: Session, thread_record, message: str, phone_number: str, profile_name: str = ""):
    """
    Create or update lead immediately with available information.
    Implements rating system: initial -> warm -> hot
    """
    try:
        logger.info(f"Starting lead creation for {phone_number}")
        from app.models import CustomerInfo, QualifiedLead
        from app.crm_integration import inject_qualified_lead_to_crm
        
        # Use AI assistant function to nurture lead progression
        logger.info(f"🌱 Using AI assistant to nurture lead progression")
        try:
            from app.execute_functions import nurture_lead_progression
            import asyncio
            
            # Get conversation history for context
            conversation_history = []
            try:
                thread_record = db.query(Thread).filter_by(sender=phone_number).first()
                if thread_record:
                    # Get conversation history from related messages
                    from app.models import Message
                    messages = db.query(Message).filter_by(thread_id=thread_record.id).order_by(Message.created_at).all()
                    conversation_history = [msg.content for msg in messages if msg.content]
                    logger.info(f"📚 Retrieved {len(conversation_history)} messages from conversation history")
                else:
                    logger.info(f"📚 No conversation history found for {phone_number}")
            except Exception as e:
                logger.warning(f"Could not retrieve conversation history: {e}")
                conversation_history = []
            
            nurturing_data = {
                "message": message,
                "telefono": phone_number,
                "conversation_history": conversation_history
            }
            
            nurturing_result = await nurture_lead_progression(db, nurturing_data)
            
            if nurturing_result.get("success"):
                lead_data = nurturing_result.get("lead_data", {})
                progression_level = lead_data.get("progression_level", "cold")
                nurturing_actions = lead_data.get("nurturing_actions", [])
                logger.info(f"✅ AI nurtured lead to {progression_level} level")
                logger.info(f"🌱 Next actions: {nurturing_actions}")
            else:
                logger.warning(f"⚠️ AI lead nurturing failed, using fallback")
                
        except Exception as e:
            logger.error(f"❌ Error in AI lead nurturing: {e}")
        
        # The nurturing function handles lead creation/update and CRM injection
        logger.info(f"🌱 Lead nurturing completed for {phone_number}")
            
    except Exception as e:
        logger.error(f"Error in create_or_update_lead_immediately: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)