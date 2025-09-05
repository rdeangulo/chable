# app/main_clean.py

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
import logging
import colorama
from colorama import Fore, Style
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sys

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
    """Serve the main testing interface."""
    from fastapi.responses import FileResponse
    import os
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"status": "working", "version": "2.0.0", "ai_system": "single_handler", "note": "index.html not found"}

@app.post("/message")
async def process_message(
    request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Process incoming messages from Twilio webhook (WhatsApp).
    """
    try:
        twilio_service = TwilioService()

        # Parse form data from Twilio webhook
        form_data = await request.form()
        logger.debug(f"Received form data: {form_data}")

        # Check for message ID to prevent duplicates
        message_sid = form_data.get("MessageSid")
        if not message_sid:
            logger.error("No MessageSid found in request")
            return Response(content="", status_code=200)

        # Extract sender information
        whatsapp_number = form_data.get("From", "").split("whatsapp:")[-1]
        if not whatsapp_number:
            logger.error("No WhatsApp number found in request")
            return Response(content="", status_code=200)

        profile_name = form_data.get("ProfileName", "").strip()

        # Drop message early if number is blocked
        if is_number_blocked(whatsapp_number):
            logger.info(f"Ignoring message from blocked number {whatsapp_number}")
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
            logger.error("No message content found")
            return Response(content="", status_code=200)

        # Clean message to remove duplicated text
        body = clean_repeated_text(body)
        logger.info(f"Received message from {whatsapp_number}: {body}")

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
            # Process message through new AI handler
            response = await ai_handler.process_message(debounced_message, model_speed="balanced")

            media_url, media_type, cleaned_message = extract_media_from_response(
                response
            )

            if media_url:
                sid = send_twilio_media_message(
                    whatsapp_number, media_url, cleaned_message, media_type
                )
                logger.info(f"Sent {media_type} message to {whatsapp_number}")
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
                sid = send_message(whatsapp_number, response)
                logger.info(f"Sent text message to {whatsapp_number}")
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

        # Auto-inject missing lead if needed
        try:
            await auto_inject_missing_lead(db, whatsapp_number, platform, body)
        except Exception as e:
            logger.error(f"Error in auto-lead injection: {e}")

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
        response = await ai_handler.process_message(body, model_speed="balanced")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
