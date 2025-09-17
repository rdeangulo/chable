# app/utils.py

import os
import re
import json
import logging
import httpx
import time
from dotenv import load_dotenv
from twilio.rest import Client
from openai import OpenAI
import openai
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
import datetime
import asyncio
from app.models import CustomerInfo, QualifiedLead, Thread, BlockedNumber, Conversation, Message
from app.db import SessionLocal
from app.services.twilio_service import TwilioService
import colorama
from colorama import Fore, Style
from typing import List

load_dotenv()

# Initialize colorama for colored output
colorama.init()

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
handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
TWILIO_STATUS_CALLBACK_URL = os.getenv("TWILIO_STATUS_CALLBACK_URL")

# Initialize clients
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Message debouncing storage
message_buffer = {}
message_lock = asyncio.Lock()


def is_number_blocked(phone_number: str) -> bool:
    """Check if a phone number is in the blocked list."""
    db = SessionLocal()
    try:
        return (
            db.query(BlockedNumber)
            .filter(BlockedNumber.phone_number == phone_number)
            .first()
            is not None
        )
    except Exception as e:
        logger.error(f"Error checking blocked number {phone_number}: {e}")
        return False
    finally:
        db.close()


def block_number(phone_number: str) -> bool:
    """Add a phone number to the block list."""
    db = SessionLocal()
    try:
        if is_number_blocked(phone_number):
            return False
        db.add(BlockedNumber(phone_number=phone_number))
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error blocking number {phone_number}: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def unblock_number(phone_number: str) -> bool:
    """Remove a phone number from the block list."""
    db = SessionLocal()
    try:
        record = (
            db.query(BlockedNumber)
            .filter(BlockedNumber.phone_number == phone_number)
            .first()
        )
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error unblocking number {phone_number}: {e}")
        db.rollback()
        return False
    finally:
        db.close()

async def get_debounced_message(whatsapp_number: str, current_message: str, message_sid: str) -> tuple[str, str, bool]:
    """
    Implements ultra-fast message buffering logic. If multiple messages are received from the same number
    within 1.5 seconds, they will be combined into a single message. This handles users who type in chunks
    while maintaining human-like response speed.
    
    Args:
        whatsapp_number: The sender's WhatsApp number
        current_message: The current message received
        message_sid: The current message SID
        
    Returns:
        tuple: (combined_message, message_sid, should_process)
        - combined_message: The combined message text
        - message_sid: The message SID to use (first message in the group)
        - should_process: Whether to process this message now
    """
    async with message_lock:
        current_time = time.time()
        
        # Check if there's an existing message in the buffer for this number
        if whatsapp_number in message_buffer:
            buffer_data = message_buffer[whatsapp_number]
            last_message_time = buffer_data['timestamp']
            
            # If the message is within 1.5 seconds of the last one (optimized for fast chunk typing)
            if current_time - last_message_time < 1.5:
                # Smart message combination - use space for short messages, newline for longer ones
                if len(current_message) <= 10 and len(buffer_data['message']) <= 50:
                    # Short messages: combine with space (like "Hola como estas")
                    combined_message = f"{buffer_data['message']} {current_message}"
                else:
                    # Longer messages: combine with newline
                    combined_message = f"{buffer_data['message']}\n{current_message}"
                
                buffer_data.update({
                    'message': combined_message,
                    'timestamp': current_time,
                    'message_count': buffer_data.get('message_count', 1) + 1
                })
                message_buffer[whatsapp_number] = buffer_data
                logger.info(f"📝 Buffering message #{buffer_data['message_count']} for {whatsapp_number}: '{current_message}' → Combined: '{combined_message}'")
                return combined_message, buffer_data['message_sid'], False
            else:
                # More than 1.5 seconds have passed, process the current message and start new buffer
                old_data = message_buffer[whatsapp_number]
                message_buffer[whatsapp_number] = {
                    'message': current_message,
                    'timestamp': current_time,
                    'message_sid': message_sid,
                    'message_count': 1
                }
                logger.info(f"⏰ Buffer timeout for {whatsapp_number}, processing current message: '{current_message}' (old buffered: '{old_data['message']}')")
                return current_message, message_sid, True
        else:
            # No existing message, create new buffer
            message_buffer[whatsapp_number] = {
                'message': current_message,
                'timestamp': current_time,
                'message_sid': message_sid,
                'message_count': 1
            }
            # Process immediately for ultra-fast response like a human would
            logger.info(f"🆕 New message buffer for {whatsapp_number}: '{current_message}' - processing immediately")
            return current_message, message_sid, True

async def cleanup_message_buffer(whatsapp_number: str):
    """
    Clean up the message buffer for a specific number after processing
    """
    async with message_lock:
        if whatsapp_number in message_buffer:
            del message_buffer[whatsapp_number]
            logger.info(f"🧹 Cleaned up message buffer for {whatsapp_number}")

async def flush_message_buffer(whatsapp_number: str) -> tuple[str, str, bool]:
    """
    Manually flush the message buffer for a specific number.
    Useful for forcing immediate processing of buffered messages.
    
    Returns:
        tuple: (message, message_sid, should_process)
    """
    async with message_lock:
        if whatsapp_number in message_buffer:
            buffer_data = message_buffer[whatsapp_number]
            message = buffer_data['message']
            message_sid = buffer_data['message_sid']
            del message_buffer[whatsapp_number]
            logger.info(f"🚀 Manually flushed buffer for {whatsapp_number}: '{message}'")
            return message, message_sid, True
        else:
            logger.info(f"⚠️ No buffer to flush for {whatsapp_number}")
            return "", "", False


def clean_repeated_text(message):
    """
    Removes repeated words or phrases at the start of a message.
    """
    pattern = r"^(\w+)\1+"
    return re.sub(pattern, r"\1", message)


def detect_image_url(message):
    """
    Detect image URLs in a message, with special handling for Cloudinary and other common image hosting services.
    
    Args:
        message (str): The message text to analyze
        
    Returns:
        str or None: The first detected image URL, or None if no image URL is found
    """
    if not message:
        return None

    # Enhanced patterns for various image hosting services
    patterns = [
        r'(https://res\.cloudinary\.com/[^\s)\"\']+)',  # Cloudinary URLs
        r'(https?://[^\s)\"\']+\.(?:jpg|jpeg|png|gif|webp))',  # Common image extensions
        r'(https?://[^\s)\"\']+/[^\s)\"\']+\?.*format=(?:jpg|jpeg|png|gif|webp))'  # URLs with format parameter
    ]

    for pattern in patterns:
        matches = re.findall(pattern, message, re.IGNORECASE)
        if matches:
            # For tuple results (from the extension pattern)
            if isinstance(matches[0], tuple):
                url = matches[0][0]
            else:
                url = matches[0]

            # Clean up the URL
            url = url.strip('.,!?()[]{}\'\"')
            logger.info(f"Found image URL: {url}")
            return url

    return None


async def transcribe_audio(media_url):
    """
    Transcribe audio from a URL using OpenAI's Whisper model.
    """
    temp_dir = "/tmp"
    audio_file_path = os.path.join(temp_dir, "voicenote.ogg")

    try:
        async with httpx.AsyncClient(auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN), follow_redirects=True) as client:
            response = await client.get(media_url)
            response.raise_for_status()

            with open(audio_file_path, "wb") as audio_file:
                audio_file.write(response.content)

        with open(audio_file_path, "rb") as audio_file:
            transcription_response = openai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcription = transcription_response.text
        return transcription

    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to download audio file: {e}")
    except openai.OpenAIError as e:
        logger.error(f"OpenAI transcription error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in transcribing audio: {e}")
    finally:
        if os.path.exists(audio_file_path):
            try:
                os.remove(audio_file_path)
                logger.info("Temporary audio file deleted successfully.")
            except Exception as e:
                logger.error(f"Failed to delete temporary audio file: {e}")

    return None




async def summarize_conversation(conversation_history, openai_client):
    """
    Generate a summary of the conversation using OpenAI's chat completions.
    """
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"Summarize the following conversation:\n\n{conversation_history}"
                }
            ]
        )
        summary = completion.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"Error in conversation summarization: {e}")
        return None


def validate_hubspot_interes_compra():
    """Test function to validate interes_compra normalization"""
    test_cases = [
        ("bajo", "Bajo"),
        ("BAJO", "Bajo"), 
        ("medio", "Medio"),
        ("MEDIO", "Medio"),
        ("alto", "Alto"),
        ("ALTO", "Alto"),
        ("unknown", "Medio"),
        ("", "Medio"),
        (None, "Medio")
    ]
    
    def normalize_interes_compra(value):
        if not value:
            return "Medio"
        value_lower = str(value).lower()
        if value_lower in ["bajo", "baja"]:
            return "Bajo"
        elif value_lower in ["medio", "media", "mediano"]:
            return "Medio"
        elif value_lower in ["alto", "alta"]:
            return "Alto"
        else:
            return "Medio"
    
    for input_val, expected in test_cases:
        result = normalize_interes_compra(input_val)
        status = "✅" if result == expected else "❌"
        logger.info(f"{status} {input_val} -> {result} (expected: {expected})")
    
    return True


async def create_hubspot_contact(customer_data, extra_properties=None):
    """
    Create or update a contact in HubSpot with the provided customer data.
    `extra_properties` allows adding additional HubSpot fields such as
    conversation summary or lead score when the lead is qualified.
    """
    hubspot_api_key = os.getenv("HUBSPOT_API_KEY")
    if not hubspot_api_key:
        logger.error("HUBSPOT_API_KEY environment variable not set")
        return None

    endpoint = "https://api.hubapi.com/crm/v3/objects/contacts"
    headers = {
        "Authorization": f"Bearer {hubspot_api_key}",
        "Content-Type": "application/json"
    }

    # Normalize interes_compra value to match HubSpot options
    def normalize_interes_compra(value):
        original_value = value
        if not value:
            return "Medio"
        value_lower = str(value).lower()
        normalized = None
        if value_lower in ["bajo", "baja"]:
            normalized = "Bajo"
        elif value_lower in ["medio", "media", "mediano"]:
            normalized = "Medio"
        elif value_lower in ["alto", "alta"]:
            normalized = "Alto"
        else:
            normalized = "Medio"  # Default fallback
        
        if original_value != normalized:
            logger.info(f"🔧 Normalized interes_compra: '{original_value}' -> '{normalized}'")
        
        return normalized

    # Prepare contact properties mapping assistant data to HubSpot properties
    # Normalize phone input to reduce duplicates caused by formatting
    def normalize_phone_input(raw_phone: str) -> str:
        if not raw_phone:
            return ""
        try:
            # Strip common prefixes and non-digits except leading '+'
            phone = str(raw_phone).strip()
            phone = phone.replace("whatsapp:", "")
            # Keep leading '+' if present, remove other non-digits
            if phone.startswith('+'):
                digits = '+' + re.sub(r'\D', '', phone[1:])
            else:
                digits = re.sub(r'\D', '', phone)
            # Heuristic: if Colombia 57 missing '+', add it
            if digits and not digits.startswith('+') and digits.startswith('57'):
                digits = '+' + digits
            return digits
        except Exception:
            return str(raw_phone)

    raw_phone = customer_data.get("telefono", "")
    phone_normalized = normalize_phone_input(raw_phone)
    contact_data = {
        "properties": {
            # Basic contact information
            "firstname": customer_data.get("nombre", ""),  # Use full name as firstname
            "email": customer_data.get("email", ""),
            "phone": phone_normalized or "",
            
            # Property preferences
            "te_interesa_el_proyecto_para": customer_data.get("tipo_propiedad", ""),
            "cul_es_tu_presupuesto_mximo_de_compra": customer_data.get("presupuesto", ""),
            
            # Lead information
            "origen_del_lead": "Ninabot",
            "hs_lead_status": "NEW",
            "lastmodifieddate": datetime.datetime.now().isoformat(),
            
            # Default values for required fields - normalized value
            "interes_compra": normalize_interes_compra(customer_data.get("interes_compra"))
        }
    }

    if extra_properties:
        contact_data["properties"].update(extra_properties)

    async with httpx.AsyncClient() as client:
        try:
            # Build a robust de-duplication search by phone/mobile/email
            search_endpoint = "https://api.hubapi.com/crm/v3/objects/contacts/search"
            email_value = (customer_data.get("email") or "").strip()
            digits_only = re.sub(r'\D', '', phone_normalized or raw_phone or "")
            last10 = digits_only[-10:] if digits_only else ""
            filter_groups = []

            if phone_normalized:
                filter_groups.append({
                    "filters": [{
                        "propertyName": "phone",
                        "operator": "EQ",
                        "value": phone_normalized
                    }]
                })
                # Search mobilephone exact too
                filter_groups.append({
                    "filters": [{
                        "propertyName": "mobilephone",
                        "operator": "EQ",
                        "value": phone_normalized
                    }]
                })
            if raw_phone and raw_phone != phone_normalized:
                filter_groups.append({
                    "filters": [{
                        "propertyName": "phone",
                        "operator": "EQ",
                        "value": raw_phone
                    }]
                })
            if last10:
                filter_groups.append({
                    "filters": [{
                        "propertyName": "phone",
                        "operator": "CONTAINS_TOKEN",
                        "value": last10
                    }]
                })
            if email_value:
                filter_groups.append({
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email_value
                    }]
                })

            search_payload = {
                "filterGroups": filter_groups or [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email_value}]}],
                "properties": ["email", "phone", "mobilephone", "firstname", "lastname"],
                "limit": 5
            }

            search_response = await client.post(search_endpoint, headers=headers, json=search_payload)
            search_response.raise_for_status()
            search_results = search_response.json()

            contact_id = None
            if search_results.get("total") > 0:
                # Choose the best matching contact
                candidates = search_results.get("results", [])
                # Prefer exact email match
                if email_value:
                    for c in candidates:
                        props = c.get("properties", {})
                        if (props.get("email") or "").strip().lower() == email_value.lower():
                            contact_id = c.get("id")
                            break
                # Else prefer exact phone match
                if not contact_id and phone_normalized:
                    for c in candidates:
                        props = c.get("properties", {})
                        if (props.get("phone") or "") == phone_normalized or (props.get("mobilephone") or "") == phone_normalized:
                            contact_id = c.get("id")
                            break
                # Fallback to first result
                if not contact_id and candidates:
                    contact_id = candidates[0].get("id")

            if contact_id:
                # Contact exists, update it
                update_endpoint = f"{endpoint}/{contact_id}"
                response = await client.patch(update_endpoint, headers=headers, json=contact_data)
                logger.info(f"Updated existing HubSpot contact {contact_id}")
            else:
                # Create new contact
                response = await client.post(endpoint, headers=headers, json=contact_data)
                logger.info("Created new HubSpot contact")

            response.raise_for_status()
            return response.json().get("id")
        except httpx.HTTPStatusError as exc:
            logger.error(f"Failed to create/update HubSpot contact: {exc.response.status_code} - {exc.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error creating/updating HubSpot contact: {e}")
            return None


async def create_hubspot_note(contact_id, note_body):
    """Create a note in HubSpot associated with the given contact."""
    hubspot_api_key = os.getenv("HUBSPOT_API_KEY")
    if not hubspot_api_key:
        logger.error("HUBSPOT_API_KEY environment variable not set")
        return None

    if not contact_id or not note_body:
        return None

    endpoint = "https://api.hubapi.com/crm/v3/objects/notes"
    headers = {
        "Authorization": f"Bearer {hubspot_api_key}",
        "Content-Type": "application/json",
    }

    # Get current timestamp in milliseconds (HubSpot requires this format)
    current_timestamp = int(datetime.datetime.now().timestamp() * 1000)

    data = {
        "properties": {
            "hs_note_body": note_body,
            "hs_timestamp": current_timestamp
        },
        "associations": [
            {
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": 202,
                    }
                ],
            }
        ],
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            return response.json().get("id")
        except httpx.HTTPStatusError as exc:
            logger.error(
                f"Failed to create HubSpot note: {exc.response.status_code} - {exc.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Error creating HubSpot note: {e}")
            return None


def wait_for_run_completion(client, thread_id, run_id, max_wait_seconds=60):
    """
    Utility function to wait for an assistant run to complete.

    Args:
        client: OpenAI client
        thread_id: Thread ID
        run_id: Run ID to wait for
        max_wait_seconds: Maximum time to wait

    Returns:
        tuple: (success, status, response)
    """
    start_time = time.time()

    while time.time() - start_time < max_wait_seconds:
        try:
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )

            # If run is complete, get the messages
            if run.status == "completed":
                messages = client.beta.threads.messages.list(
                    thread_id=thread_id,
                    order="desc",
                    limit=1
                )

                if messages.data:
                    for content_part in messages.data[0].content:
                        if content_part.type == "text":
                            return True, "completed", content_part.text.value
                return True, "completed", ""

            # If run requires action, return the run for processing
            elif run.status == "requires_action":
                return False, "requires_action", run

            # If run failed, return error
            elif run.status in ["failed", "cancelled", "expired"]:
                return False, run.status, f"Run failed with status {run.status}"

            # Wait before checking again
            time.sleep(1)

        except Exception as e:
            logger.error(f"Error waiting for run completion: {str(e)}")
            return False, "error", str(e)

    # If timeout reached
    return False, "timeout", f"Run did not complete within {max_wait_seconds} seconds"


def detect_pdf_url(message):
    """
    Detect PDF URLs in a message with improved pattern matching.
    """
    if not message:
        return None

    # Enhanced pattern to catch more PDF URL variations
    patterns = [
        r'(https?://[^\s)\"\']+\.pdf)',  # Standard PDF URLs
        r'(https?://[^\s)\"\']+/[^\s)\"\']+\?.*type=pdf)',  # URLs with query params
        r'(https?://[^\s)\"\']+/document/d/[^\s)\"\']+)'  # Google Docs style URLs
    ]

    for pattern in patterns:
        matches = re.findall(pattern, message)
        if matches:
            logger.info(f"Found PDF URL: {matches[0]}")
            return matches[0]

    return None


def extract_media_from_response(response):
    """
    Extracts media URLs (images, PDFs) from the assistant's response.
    Handles both direct URLs, markdown-formatted image links, and media descriptions.

    Args:
        response (str): The assistant's response message

    Returns:
        tuple: (media_url, media_type, cleaned_message)
        media_type will be 'image', 'pdf', or None
    """
    if not response:
        return None, None, "Lo siento, no pude procesar la respuesta en este momento."

    # Check if response is a dictionary (from enviar_foto function)
    if isinstance(response, dict):
        if response.get("success"):
            photo_url = response.get("photo_url")
            message = response.get("text_sent", "Aquí está la imagen que solicitaste.")
            if photo_url:
                return photo_url, 'image', message
        else:
            error_msg = response.get("error", "Lo siento, no pude encontrar la imagen solicitada.")
            return None, None, error_msg

    # Check for media descriptions from incoming messages first
    media_description_patterns = [
        r'\[IMAGEN_RECIBIDA:\s*([^\]]+)\]',
        r'\[PDF_RECIBIDO:\s*([^\]]+)\]',
        r'\[ARCHIVO_RECIBIDO:\s*([^\]]+)(?:\s*-\s*tipo:\s*[^\]]+)?\]'
    ]
    
    for pattern in media_description_patterns:
        match = re.search(pattern, response)
        if match:
            media_url = match.group(1).strip()
            # Remove the media description from the response
            cleaned_message = re.sub(pattern, '', response).strip()
            
            # Determine media type based on pattern
            if 'IMAGEN_RECIBIDA' in pattern:
                media_type = 'image'
            elif 'PDF_RECIBIDO' in pattern:
                media_type = 'pdf'
            else:
                # Determine from URL or default to image
                if media_url.lower().endswith('.pdf'):
                    media_type = 'pdf'
                else:
                    media_type = 'image'
            
            logger.info(f"Extracted media from description: {media_url} (type: {media_type})")
            return media_url, media_type, cleaned_message or "Aquí está el archivo que solicitaste."

    # First check for markdown image syntax
    markdown_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
    markdown_matches = re.findall(markdown_pattern, response)
    
    if markdown_matches:
        # Use the URL from the first markdown image
        image_url = markdown_matches[0][1].strip()
        # Remove the markdown image syntax
        cleaned_message = re.sub(markdown_pattern, '', response).strip()
    else:
        # Check for direct image URLs
        image_url = detect_image_url(response)
        cleaned_message = response

    if image_url:
        # Remove the URL from the message if it exists
        cleaned_message = cleaned_message.replace(image_url, '').strip()
        # Clean up any remaining markdown syntax
        cleaned_message = re.sub(r'!\[.*?\]', '', cleaned_message).strip()
        cleaned_message = re.sub(r'\s+', ' ', cleaned_message)  # Normalize whitespace
        cleaned_message = re.sub(r'\n\s*\n', '\n', cleaned_message)  # Remove extra newlines
        
        if not cleaned_message or cleaned_message.isspace():
            cleaned_message = "Aquí está la imagen que solicitaste."
        
        logger.info(f"Extracted image URL: {image_url}")
        return image_url, 'image', cleaned_message

    # If no image found, check for PDF
    pdf_url = detect_pdf_url(response)
    if pdf_url:
        # Remove the URL from the message
        cleaned_message = response.replace(pdf_url, '').strip()
        cleaned_message = re.sub(r'\s+', ' ', cleaned_message)
        cleaned_message = re.sub(r'\n\s*\n', '\n', cleaned_message)
        
        if not cleaned_message or cleaned_message.isspace():
            cleaned_message = "Aquí está el documento PDF que solicitaste."
        
        logger.info(f"Extracted PDF URL: {pdf_url}")
        return pdf_url, 'pdf', cleaned_message

    # No media found, return original message
    return None, None, response


# Updated send_twilio_media_message function for utils.py

def clean_markdown(text):
    """
    Removes Markdown formatting and bracketed text from text to make it suitable
    for messaging platforms like WhatsApp.

    Args:
        text (str): Text containing Markdown formatting and possibly bracketed instructions

    Returns:
        str: Clean text without Markdown formatting or bracketed text
    """
    if not text:
        return ""

    # Remove text within square brackets
    cleaned = re.sub(r'\[.*?\]', '', text)

    # Remove markdown image syntax ![text]() or ![text](url)
    cleaned = re.sub(r'!\[(.*?)\]\((.*?)\)', '', cleaned)

    # Remove other common markdown elements
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # Bold
    cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)  # Italic
    cleaned = re.sub(r'__(.*?)__', r'\1', cleaned)  # Underline
    cleaned = re.sub(r'~~(.*?)~~', r'\1', cleaned)  # Strikethrough
    cleaned = re.sub(r'```(.*?)```', r'\1', cleaned, flags=re.DOTALL)  # Code blocks
    cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)  # Inline code

    # Clean up markdown headings
    cleaned = re.sub(r'^#{1,6}\s+(.*?)$', r'\1', cleaned, flags=re.MULTILINE)

    # Clean up markdown lists
    cleaned = re.sub(r'^\s*[\*\-\+]\s+(.*?)$', r'• \1', cleaned, flags=re.MULTILINE)  # Bullet lists
    cleaned = re.sub(r'^\s*\d+\.\s+(.*?)$', r'• \1', cleaned, flags=re.MULTILINE)  # Numbered lists

    # Remove unnecessary line breaks and whitespace
    cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
    cleaned = re.sub(r'  +', ' ', cleaned)

    return cleaned.strip()

def send_message(to_number, message_body):
    """
    Send a text message via Twilio WhatsApp.
    Cleans any Markdown formatting before sending.
    """
    if is_number_blocked(to_number):
        logger.info(f"Not sending message to blocked number {to_number}")
        return None

    if not message_body or message_body.strip() == "":
        logger.warning(f"Attempted to send empty message to {to_number}")
        return None

    # Clean markdown from message
    clean_message = clean_markdown(message_body)

    try:
        message = twilio_client.messages.create(
            body=clean_message,
            from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
            to=f"whatsapp:{to_number}",
            status_callback=TWILIO_STATUS_CALLBACK_URL if TWILIO_STATUS_CALLBACK_URL else None,
        )
        logger.info(
            f"Message sent to {to_number}: {message.sid} initial status: {message.status}"
        )
        try:
            db = SessionLocal()
            service = TwilioService()
            service.log_message(
                db=db,
                direction="outbound",
                from_number=TWILIO_WHATSAPP_NUMBER,
                to_number=to_number,
                message_body=clean_message,
                message_sid=message.sid,
                status=message.status,
            )
            db.close()
        except Exception as log_err:
            logger.error(f"Failed to log message: {log_err}")

        return message.sid
    except Exception as e:
        logger.error(f"Failed to send message to {to_number}: {e}")
        return None


# Update send_twilio_media_message function in utils.py

def send_twilio_media_message(to_number, media_url, message_body, media_type=None):
    """
    Send a media message via Twilio WhatsApp.
    Handles both images and documents (PDFs).
    Cleans any Markdown formatting before sending.

    Args:
        to_number: Recipient's phone number
        media_url: URL of the media to send
        message_body: Text message to accompany the media
        media_type: Type of media ('image', 'pdf', or None for auto-detection)
    """
    try:
        number_plain = to_number.split('whatsapp:')[-1]
        if is_number_blocked(number_plain):
            logger.info(f"Not sending media message to blocked number {number_plain}")
            return None

        # Ensure proper phone number formatting
        if not to_number.startswith('whatsapp:'):
            to_number = f'whatsapp:{to_number}'
        
        sender = f'whatsapp:{TWILIO_WHATSAPP_NUMBER}'
        if sender.startswith('whatsapp:whatsapp:'):
            sender = f'whatsapp:{TWILIO_WHATSAPP_NUMBER.replace("whatsapp:", "")}'

        # Validate media URL
        if not media_url:
            logger.error("No media URL provided")
            if message_body:
                # If we have a message but no media, send as regular message
                return send_message(to_number, message_body)
            return None

        # Auto-detect media type if not specified
        if media_type is None:
            if isinstance(media_url, str):
                if media_url.lower().endswith('.pdf'):
                    media_type = 'pdf'
                elif any(ext in media_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                    media_type = 'image'
                else:
                    media_type = 'file'

        # Clean markdown from message body
        clean_message = clean_markdown(message_body) if message_body else ""

        # Ensure we have a message body
        if not clean_message or clean_message.strip() == "":
            if media_type == 'pdf':
                clean_message = "Aquí está el documento PDF que solicitaste."
            elif media_type == 'image':
                clean_message = "Aquí está la imagen que solicitaste."
            else:
                clean_message = "Aquí está el archivo que solicitaste."

        # Prepare media URL list
        if isinstance(media_url, str):
            media_url_list = [media_url]
        elif isinstance(media_url, list):
            media_url_list = [url for url in media_url if url]  # Filter out empty URLs
        else:
            try:
                media_url_list = [str(media_url)]
            except:
                logger.error(f"Could not convert media_url to string: {type(media_url)}")
                return None

        # Log the attempt
        logger.info(f"Attempting to send {media_type} message to {to_number}")
        logger.info(f"Media URLs: {media_url_list}")
        logger.info(f"Message body: {clean_message}")
        
        # Ensure proper UTF-8 encoding for the message
        if isinstance(clean_message, str):
            clean_message = clean_message.encode('utf-8').decode('utf-8')

        # Create and send the message
        message = twilio_client.messages.create(
            body=clean_message,
            from_=sender,
            to=to_number,
            media_url=media_url_list,
            status_callback=TWILIO_STATUS_CALLBACK_URL if TWILIO_STATUS_CALLBACK_URL else None,
        )

        logger.info(
            f"Successfully sent {media_type} message to {to_number}: {message.sid} initial status: {message.status}"
        )
        try:
            db = SessionLocal()
            service = TwilioService()
            service.log_message(
                db=db,
                direction="outbound",
                from_number=TWILIO_WHATSAPP_NUMBER,
                to_number=to_number,
                message_body=clean_message,
                message_sid=message.sid,
                status=message.status,
            )
            db.close()
        except Exception as log_err:
            logger.error(f"Failed to log media message: {log_err}")

        return message.sid

    except Exception as e:
        logger.error(f"Failed to send media message to {to_number}: {e}")
        
        # Try to send error message
        try:
            error_msg = f"Lo siento, hubo un problema al enviar el {media_type}. Por favor, intenta nuevamente."
            twilio_client.messages.create(
                body=error_msg,
                from_=f"whatsapp:{TWILIO_WHATSAPP_NUMBER}",
                to=to_number
            )
            logger.info(f"Sent error notification to {to_number}")
        except Exception as inner_e:
            logger.error(f"Also failed to send error message: {inner_e}")
        
        return None


def send_location_message(to_number, latitude, longitude, name, address):
    """
    Send a location message via WhatsApp using Twilio's persistent_action parameter.
    """
    try:
        # Ensure proper formatting of phone numbers
        if not to_number.startswith('whatsapp:'):
            recipient = f'whatsapp:{to_number}'
        else:
            recipient = to_number

        # Format the sender number
        sender = f'whatsapp:{TWILIO_WHATSAPP_NUMBER}'
        if sender.startswith('whatsapp:whatsapp:'):
            sender = f'whatsapp:{TWILIO_WHATSAPP_NUMBER.replace("whatsapp:", "")}'

        # Create the location message body with address info
        body = f"Ubicación: {name}\n{address}"

        # Send message with location using persistent_action
        message = twilio_client.messages.create(
            body=body,
            from_=sender,
            to=recipient,
            persistent_action=[f'geo:{latitude},{longitude}|{name}'],
            status_callback=TWILIO_STATUS_CALLBACK_URL if TWILIO_STATUS_CALLBACK_URL else None,
        )

        logger.info(
            f"Location message sent to {to_number}: {message.sid} initial status: {message.status}"
        )
        try:
            db = SessionLocal()
            service = TwilioService()
            service.log_message(
                db=db,
                direction="outbound",
                from_number=TWILIO_WHATSAPP_NUMBER,
                to_number=to_number,
                message_body=body,
                message_sid=message.sid,
                status=message.status,
            )
            db.close()
        except Exception as log_err:
            logger.error(f"Failed to log location message: {log_err}")

        return message.sid
    except Exception as e:
        logger.error(f"Failed to send location message to {to_number}: {e}")
        return None


def send_yucatan_location(to_number):
    """
    Send the Chablé Yucatan location via WhatsApp.
    """
    # Coordinates for Chablé Yucatan
    latitude = 20.75437450571972
    longitude = -89.86088050055272
    name = "Chablé Yucatan"
    address = "Yucatan, Mexico"

    return send_location_message(to_number, latitude, longitude, name, address)


async def check_and_handle_active_runs(client, thread_id):
    """
    Check for any active runs in the thread and handle them appropriately.
    
    Args:
        client: OpenAI client instance
        thread_id: The ID of the thread to check
        
    Returns:
        bool: True if the thread is ready for new messages, False otherwise
    """
    try:
        # List all runs for the thread
        runs = client.beta.threads.runs.list(thread_id=thread_id)
        
        # Check for any active runs
        for run in runs.data:
            if run.status in ["in_progress", "queued"]:
                logger.info(f"Found active run {run.id} in thread {thread_id}")
                
                # Cancel the run
                try:
                    client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    logger.info(f"Successfully cancelled run {run.id}")
                except Exception as e:
                    logger.warning(f"Failed to cancel run {run.id}: {e}")
                    # Even if we can't cancel, we'll continue
                
                # Wait a short time to ensure the cancellation is processed
                await asyncio.sleep(1)
            
            elif run.status == "requires_action":
                logger.info(f"Found run requiring action {run.id}, attempting to cancel")
                try:
                    client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                except Exception as e:
                    logger.warning(f"Failed to cancel run requiring action {run.id}: {e}")
                
                await asyncio.sleep(1)
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking thread runs: {e}")
        return False

async def analyze_conversation_thread(client, db, thread_id):
    """
    Analyze a complete conversation thread to generate a summary and interest score using gpt-4o-mini.
    Returns (summary, interest_score) where interest_score is 0-100.
    """
    try:
        # Get all messages from the thread
        messages = client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc"
        )
        conversation_text = ""
        for msg in messages.data:
            role = "Cliente" if msg.role == "user" else "Asistente"
            for content in msg.content:
                if content.type == "text":
                    conversation_text += f"{role}: {content.text.value}\n\n"

        # --- Generate summary ---
        summary_prompt = (
            "Por favor, proporciona un resumen conciso pero completo de esta conversación con el cliente potencial.\n"
            "Incluye los puntos clave discutidos, las preferencias del cliente y cualquier acuerdo o siguiente paso acordado.\n\n"
            "NO uses formato markdown ni caracteres especiales.\n"
            "MANTÉN el formato simple y legible.\n\n"
            "Conversación:\n{conversation}"
        )
        try:
            summary_completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un analista experto en bienes raíces que resume conversaciones de ventas de manera clara y concisa, sin usar formato markdown."},
                    {"role": "user", "content": summary_prompt.format(conversation=conversation_text)}
                ]
            )
            summary = summary_completion.choices[0].message.content.strip()
            summary = clean_markdown(summary)
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            summary = "Error al generar resumen."

        # --- Calculate interest score ---
        score_prompt = (
            "Analiza esta conversación y asigna una puntuación numérica del 0 al 100 basada en:\n"
            "- Urgencia de compra (25 puntos)\n"
            "- Claridad en preferencias y requisitos (25 puntos)\n"
            "- Compromiso en la conversación (25 puntos)\n"
            "- Capacidad financiera aparente (25 puntos)\n\n"
            "RESPONDE ÚNICAMENTE CON EL NÚMERO (0-100).\n"
            "NO incluyas explicaciones ni texto adicional.\n\n"
            "Conversación:\n{conversation}"
        )
        try:
            score_completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un analista experto en calificación de leads de bienes raíces. Debes responder únicamente con un número del 0 al 100."},
                    {"role": "user", "content": score_prompt.format(conversation=conversation_text)}
                ]
            )
            score_text = score_completion.choices[0].message.content.strip()
            interest_score = int(float(score_text))
            interest_score = max(0, min(100, interest_score))
        except Exception as e:
            logger.error(f"Error generating interest score: {e}")
            interest_score = 0

        logger.info(f"Conversation summary: {summary}")
        logger.info(f"Interest score: {interest_score}")
        return summary, interest_score
    except Exception as e:
        logger.error(f"Error analyzing conversation thread: {e}")
        return "Error al generar resumen.", 0

async def analyze_need_for_followup(client, thread_id, conversation_text):
    """
    Analyze a conversation to determine if a follow-up message should be sent.
    
    Args:
        client: OpenAI client
        thread_id: Thread ID
        conversation_text: Text of the conversation
        
    Returns:
        tuple: (should_follow_up, suggested_message)
    """
    try:
        analysis_prompt = (
            "Analiza esta conversación y determina si sería apropiado enviar un mensaje de seguimiento "
            "después de 10 minutos sin respuesta.\n\n"
            "Criterios para NO enviar seguimiento:\n"
            "1. Si hay interés obvio y ya se acordaron próximos pasos\n"
            "2. Si el cliente está molesto o insatisfecho\n"
            "3. Si la conversación parece haber concluido naturalmente\n"
            "4. Si el último mensaje fue del cliente\n\n"
            "DEBES responder con un objeto JSON válido que contenga estos campos exactos:\n"
            '{\n'
            '    "should_follow_up": true/false,\n'
            '    "reason": "explicación de la decisión",\n'
            '    "suggested_message": "mensaje sugerido si should_follow_up es true"\n'
            '}\n\n'
            "IMPORTANTE:\n"
            "- El JSON debe estar correctamente formateado\n"
            "- No incluyas saltos de línea dentro del JSON\n"
            "- No incluyas texto antes o después del JSON\n"
            "- Usa comillas dobles para las cadenas\n"
            "- El campo should_follow_up debe ser un booleano (true/false, no \"true\"/\"false\")\n\n"
            "Conversación:\n"
            "{conversation}"
        )
        
        logger.info(f"Requesting follow-up analysis for thread {thread_id}")
        
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un experto en ventas de bienes raíces que analiza conversaciones. Tu tarea es generar ÚNICAMENTE un objeto JSON válido como respuesta, sin ningún otro texto o formato adicional."
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt.format(conversation=conversation_text)
                    }
                ],
                response_format={ "type": "json_object" }
            )
            
            # Validate completion response structure
            if not completion or not completion.choices or len(completion.choices) == 0:
                logger.error(f"Invalid completion response structure for thread {thread_id}")
                return False, ""
            
            if not completion.choices[0].message or not completion.choices[0].message.content:
                logger.error(f"Empty or invalid message content in completion for thread {thread_id}")
                return False, ""
            
            # Get and clean the response
            response_text = completion.choices[0].message.content.strip()
            logger.debug(f"Raw response from OpenAI: {response_text}")
            
            # Basic validation of response format
            if not response_text:
                logger.error(f"Empty response text from OpenAI for thread {thread_id}")
                return False, ""
            
            try:
                # Try to parse the JSON response
                result = json.loads(response_text)
                
                # Validate result is a dictionary
                if not isinstance(result, dict):
                    logger.error(f"Expected dict, got {type(result)}: {result}")
                    return False, ""
                
                # Safely extract should_follow_up with proper error handling
                should_follow_up = result.get("should_follow_up")
                if should_follow_up is None:
                    logger.error(f"Missing 'should_follow_up' field in response. Available fields: {list(result.keys())}")
                    logger.error(f"Full response: {result}")
                    return False, ""
                
                # Validate should_follow_up is boolean or can be converted
                if isinstance(should_follow_up, str):
                    should_follow_up_str = should_follow_up.lower().strip()
                    if should_follow_up_str in ["true", "1", "yes"]:
                        should_follow_up = True
                    elif should_follow_up_str in ["false", "0", "no"]:
                        should_follow_up = False
                    else:
                        logger.error(f"Invalid should_follow_up string value: '{should_follow_up}'")
                        return False, ""
                elif not isinstance(should_follow_up, bool):
                    logger.error(f"Invalid should_follow_up value: {should_follow_up} (type: {type(should_follow_up)})")
                    return False, ""
                
                suggested_message = result.get("suggested_message", "") if should_follow_up else ""
                reason = result.get("reason", "No reason provided")
                
                # Log the decision with full context
                logger.info(f"Follow-up analysis for thread {thread_id}:")
                logger.info(f"  Should follow up: {should_follow_up}")
                logger.info(f"  Reason: {reason}")
                if should_follow_up:
                    logger.info(f"  Suggested message: {suggested_message}")
                
                return should_follow_up, suggested_message
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parse error for thread {thread_id}:")
                logger.error(f"  Error message: {str(e)}")
                logger.error(f"  Response text: {response_text}")
                logger.error(f"  Error position: char {e.pos}, line {e.lineno}, col {e.colno}")
                return False, ""
            except KeyError as e:
                logger.error(f"KeyError in JSON response for thread {thread_id}:")
                logger.error(f"  Missing key: {str(e)}")
                logger.error(f"  Full response: {response_text}")
                logger.error(f"  Parsed result keys: {list(result.keys()) if 'result' in locals() else 'N/A'}")
                return False, ""
            except Exception as e:
                logger.error(f"Unexpected error parsing response for thread {thread_id}: {str(e)}")
                logger.error(f"  Response text: {response_text}")
                return False, ""
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API for thread {thread_id}:")
            logger.error(f"  Error type: {type(e).__name__}")
            logger.error(f"  Error message: {str(e)}")
            logger.error(f"  Full error details: {repr(e)}")
            if hasattr(e, '__traceback__'):
                import traceback
                logger.error(f"  Traceback: {traceback.format_exc()}")
            return False, ""
            
    except Exception as e:
        logger.error(f"Error analyzing need for follow-up for thread {thread_id}:")
        logger.error(f"  Error type: {type(e).__name__}")
        logger.error(f"  Error message: {str(e)}")
        logger.error(f"  Conversation length: {len(conversation_text)} chars")
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error(f"  Traceback: {traceback.format_exc()}")
        return False, ""

async def check_and_send_followup(db: Session):
    """
    Check all threads for those needing follow-up and send messages if appropriate.
    This function should be called periodically (e.g., every minute).
    """
    try:
        # Get all threads where:
        # 1. follow_up_need_sent is False
        # 2. last_conversation_at was more than 10 minutes ago
        current_time = datetime.datetime.now()
        ten_minutes_ago = current_time - datetime.timedelta(minutes=10)
        
        threads = db.query(Thread).filter(
            Thread.follow_up_need_sent == False,
            Thread.last_conversation_at <= ten_minutes_ago
        ).all()
        
        for thread in threads:
            try:
                logger.debug(f"Processing thread {thread.thread_id} for follow-up check")
                # Get messages from the thread using openai_client
                messages = openai_client.beta.threads.messages.list(
                    thread_id=thread.thread_id,
                    order="asc"
                )
                
                # Format conversation for analysis
                conversation_text = ""
                last_message_role = None
                for msg in messages.data:
                    role = "Cliente" if msg.role == "user" else "Asistente"
                    last_message_role = role
                    for content in msg.content:
                        if content.type == "text":
                            conversation_text += f"{role}: {content.text.value}\n\n"
                
                # Only proceed if last message was from assistant
                if last_message_role == "Asistente":
                    try:
                        should_follow_up, suggested_message = await analyze_need_for_followup(
                            openai_client,
                            thread.thread_id,
                            conversation_text
                        )
                    except Exception as follow_up_error:
                        logger.error(f"Error analyzing follow-up for thread {thread.thread_id}: {follow_up_error}")
                        # Mark as processed to avoid retrying indefinitely
                        thread.follow_up_need_sent = True
                        thread.follow_up_sent_at = datetime.datetime.now(datetime.timezone.utc)
                        db.commit()
                        continue
                    
                    if should_follow_up:
                        service = TwilioService()
                        template = service.get_template_by_name("followup")
                        if template:
                            await service.send_message(
                                to_number=thread.sender,
                                message_body=template.get("body", ""),
                                template_name="followup",
                                use_template=True,
                            )
                            logger.info(f"Sent follow-up message to {thread.sender}")
                        else:
                            logger.error("Followup template not found or not approved")

                        # Mark follow-up as sent
                        thread.follow_up_need_sent = True
                        thread.follow_up_sent_at = datetime.datetime.now(datetime.timezone.utc)
                        db.commit()
                    else:
                        logger.info(f"No follow-up needed for thread {thread.thread_id}")
                        # Mark as processed even if no follow-up was needed
                        thread.follow_up_need_sent = True
                        thread.follow_up_sent_at = datetime.datetime.now(datetime.timezone.utc)
                        db.commit()
                else:
                    logger.info(f"Last message was from client for thread {thread.thread_id}, no follow-up needed")
                    thread.follow_up_need_sent = True
                    thread.follow_up_sent_at = datetime.datetime.now(datetime.timezone.utc)
                    db.commit()
                    
            except Exception as thread_error:
                logger.error(f"Error processing thread {thread.thread_id} for follow-up: {thread_error}")
                logger.error(f"Thread error details: {repr(thread_error)}")
                try:
                    # Mark as processed to prevent retrying indefinitely
                    thread.follow_up_need_sent = True
                    thread.follow_up_sent_at = datetime.datetime.now(datetime.timezone.utc)
                    db.commit()
                except Exception as commit_error:
                    logger.error(f"Failed to mark thread as processed: {commit_error}")
                    db.rollback()
                continue
                
    except Exception as e:
        logger.error(f"Error in check_and_send_followup: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


async def audit_conversations(client, db: Session, start: datetime.datetime, end: datetime.datetime):
    """Analyze conversations in a date range and provide supervisor feedback with structured insights.
    Returns a dict with metrics, issues, missed leads, errors, and suggestions.
    """
    try:
        # Fetch threads with activity in range
        threads = (
            db.query(Thread)
            .filter(Thread.last_conversation_at.isnot(None))
            .filter(Thread.last_conversation_at >= start, Thread.last_conversation_at <= end)
            .order_by(Thread.last_conversation_at.desc())
            .all()
        )

        if not threads:
            return {
                "summary": "No se encontraron conversaciones en el periodo seleccionado.",
                "metrics": {
                    "threads": 0,
                    "conversations": 0,
                    "messages": 0,
                    "qualified_leads": 0,
                    "missed_leads": 0,
                    "errors": 0
                },
                "issues": [],
                "missed_leads": [],
                "agent_errors": [],
                "suggestions": []
            }

        # Gather conversations and compute basic metrics
        total_conversations = 0
        total_messages = 0
        qualified_leads = 0
        errors_detected = 0
        missed_leads_list = []
        convo_samples_for_ai: List[str] = []

        max_threads_for_ai = 15
        max_messages_per_thread = 30

        for idx, thread in enumerate(threads):
            # Count qualified leads
            lead = db.query(QualifiedLead).filter(QualifiedLead.telefono == thread.sender).first()
            if lead:
                qualified_leads += 1

            # Get messages in range for this thread
            msgs = (
                db.query(Message)
                .filter(Message.thread_id == thread.id)
                .order_by(Message.created_at.asc())
                .all()
            )
            if not msgs:
                # fallback to legacy Conversation table
                exchanges = (
                    db.query(Conversation)
                    .filter(Conversation.thread_id == thread.id)
                    .order_by(Conversation.created_at.asc())
                    .all()
                )
                total_conversations += len(exchanges)
                # Build transcript from legacy
                transcript = []
                for ex in exchanges[-max_messages_per_thread:]:
                    if ex.message:
                        transcript.append(f"Cliente: {ex.message}")
                        total_messages += 1
                    if ex.response:
                        transcript.append(f"Asistente: {ex.response}")
                        total_messages += 1
                    # Detect error patterns in responses
                    if ex.response and "error" in ex.response.lower():
                        errors_detected += 1
                convo_text = "\n".join(transcript)
            else:
                total_conversations += 1
                # Build transcript from messages table
                transcript = []
                # limit to last N
                recent_msgs = msgs[-max_messages_per_thread:]
                for m in recent_msgs:
                    role = "Cliente" if m.role == "user" else "Asistente"
                    if m.content:
                        transcript.append(f"{role}: {m.content}")
                        total_messages += 1
                        if role == "Asistente" and ("error" in m.content.lower() or "lo siento" in m.content.lower()):
                            errors_detected += 1
                convo_text = "\n".join(transcript)

            # Collect a bounded set for AI analysis
            if idx < max_threads_for_ai and convo_text:
                header = f"Hilo {idx+1} ({thread.sender_platform}, {thread.sender}):"
                convo_samples_for_ai.append(header + "\n" + convo_text)

            # Missed lead detection: scan user messages for explicit interest and absence of lead
            try:
                if not lead:  # Only consider missed if no lead exists
                    # inspect last messages for interest
                    last_user_texts: List[str] = []
                    if msgs:
                        for m in msgs[-10:]:
                            if m.role == "user" and m.content:
                                last_user_texts.append(m.content)
                    else:
                        for ex in exchanges[-10:]:
                            if ex.message:
                                last_user_texts.append(ex.message)

                    interest_hits = []
                    for txt in last_user_texts:
                        det = await detect_lead_interest(client, txt)
                        if det and det.get("shows_interest") and det.get("confidence_score", 0) >= 70:
                            interest_hits.append({
                                "text": txt,
                                "interest_type": det.get("interest_type"),
                                "confidence": det.get("confidence_score")
                            })
                    if interest_hits:
                        missed_leads_list.append({
                            "sender": thread.sender,
                            "platform": thread.sender_platform,
                            "examples": interest_hits[:3]
                        })
            except Exception as _:
                # best-effort; continue
                pass

        # Build AI prompt using larger-context model
        joined_samples = "\n\n" + ("\n\n".join(convo_samples_for_ai) if convo_samples_for_ai else "")
        system_prompt = (
            "Eres un supervisor de ventas que audita conversaciones de WhatsApp. "
            "Entrega hallazgos accionables y concisos. Identifica: \n"
            "1) problemas de tono/flujo, 2) preguntas sin responder o contexto faltante, "
            "3) errores del agente/bot, 4) oportunidades perdidas (missed leads), "
            "5) recomendaciones concretas para mejorar guiones y triggers. "
            "Responde en JSON válido con claves: summary, issues[], agent_errors[], suggestions[]."
        )
        user_prompt = (
            "Analiza las siguientes conversaciones recientes (muestra recortada). "
            "Devuelve JSON estrictamente con este formato: \n"
            "{\n"
            "  \"summary\": string,\n"
            "  \"issues\": [{\"title\": string, \"severity\": \"low|medium|high\", \"example\": string, \"suggestion\": string}],\n"
            "  \"agent_errors\": [{\"type\": string, \"example\": string, \"fix\": string}],\n"
            "  \"suggestions\": [string]\n"
            "}\n\n"
            f"Conversaciones:\n{joined_samples}"
        )

        ai_summary = None
        try:
            completion = client.chat.completions.create(
                model="gpt-4.1",  # larger-context model for on-demand audits
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                timeout=20
            )
            ai_text = completion.choices[0].message.content.strip()
            try:
                ai_summary = json.loads(ai_text)
            except Exception:
                # Fallback: wrap raw text
                ai_summary = {"summary": ai_text, "issues": [], "agent_errors": [], "suggestions": []}
        except Exception as e:
            logger.error(f"Error in GPT audit completion: {e}")
            ai_summary = {"summary": "No fue posible generar el análisis con IA.", "issues": [], "agent_errors": [], "suggestions": []}

        result = {
            "summary": ai_summary.get("summary") if isinstance(ai_summary, dict) else str(ai_summary),
            "metrics": {
                "threads": len(threads),
                "conversations": total_conversations,
                "messages": total_messages,
                "qualified_leads": qualified_leads,
                "missed_leads": len(missed_leads_list),
                "errors": errors_detected,
            },
            "issues": ai_summary.get("issues", []) if isinstance(ai_summary, dict) else [],
            "missed_leads": missed_leads_list,
            "agent_errors": ai_summary.get("agent_errors", []) if isinstance(ai_summary, dict) else [],
            "suggestions": ai_summary.get("suggestions", []) if isinstance(ai_summary, dict) else [],
        }
        return result

    except Exception as e:
        logger.error(f"Error auditing conversations: {e}")
        return {
            "summary": "Error al analizar conversaciones. Por favor, intente nuevamente.",
            "metrics": {},
            "issues": [],
            "missed_leads": [],
            "agent_errors": [],
            "suggestions": []
        }

async def extract_lead_info(client, thread_id):
    """Extract lead details from a conversation thread using GPT-4.1-nano."""
    try:
        messages = client.beta.threads.messages.list(
            thread_id=thread_id,
            order="asc",
        )
        conversation_text = ""
        for msg in messages.data:
            role = "Cliente" if msg.role == "user" else "Asistente"
            for content in msg.content:
                if content.type == "text":
                    conversation_text += f"{role}: {content.text.value}\n"
        prompt = (
            "Extrae la información del cliente potencial en formato JSON con las "
            "claves: nombre, email, ciudad_interes, proyecto_interes, tipo_propiedad, presupuesto. "
            "Si no se menciona algún dato, deja el valor vacío.\n\nConversación:\n{conversation}"
        )
        completion = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "Eres un asistente que extrae datos de leads inmobiliarios."},
                {"role": "user", "content": prompt.format(conversation=conversation_text)}
            ]
        )
        text = completion.choices[0].message.content.strip()
        try:
            return json.loads(text)
        except Exception:
            logger.error(f"Failed to parse lead info JSON: {text}")
            return {}
    except Exception as e:
        logger.error(f"Error extracting lead info: {e}")
        return {}


async def detect_lead_interest(client, message_text: str) -> dict:
    """
    Detecta automáticamente si un mensaje indica interés usando AI (GPT-4o-mini).
    Solo detecta interés cuando el cliente EXPLÍCITAMENTE solicita una acción específica.
    """
    try:
        # Use AI to analyze the message for EXPLICIT interest only
        analysis_prompt = f"""
        Analiza este mensaje de WhatsApp y determina si el cliente muestra interés EXPLÍCITO en:
        1. Visitar el proyecto
        2. Contactar o ser contactado por un asesor
        3. Obtener más información, SOLO si pide ser contactado o solicita un envío que requiere seguimiento humano (no genérico)
        4. Comprar una propiedad

        CRITERIOS ESTRICTOS:
        - SOLO marca interés si el cliente EXPLÍCITAMENTE solicita una acción que requiere seguimiento humano (agendar visita, que lo contacten, llamada, comprar, cerrar negocio, agendar cita, enviar datos de contacto, etc.).
        - Pedir "más información" de forma genérica NO es suficiente a menos que pida que lo contacten o agendar algo.
        - NO detectes interés por comentarios generales, preguntas casuales, o expresiones de curiosidad.

        EJEMPLOS DE INTERÉS EXPLÍCITO (✅ SÍ inyectar a HubSpot):
        ✅ "Quiero visitar el proyecto"
        ✅ "Me puede contactar un asesor"
        ✅ "Necesito más información, ¿me puedes llamar?"
        ✅ "Me interesa comprar"
        ✅ "Puedo agendar una cita"
        ✅ "Quisiera que me contacten"
        ✅ "Deseo ver el apartamento"
        ✅ "Envíame la información y agendamos una llamada"

        EJEMPLOS DE NO INTERÉS EXPLÍCITO (❌ NO inyectar a HubSpot):
        ❌ "Hola, cómo están?"
        ❌ "Qué precio tienen?"
        ❌ "Bonito proyecto"
        ❌ "Dónde está ubicado?"
        ❌ "Quiero más información" (sin pedir contacto, visita ni acción concreta)
        ❌ "Cuánto cuesta?"
        ❌ "Qué incluye?"
        ❌ "Tienen fotos?"
        ❌ "Es bonito"
        ❌ "Me gusta"

        IMPORTANTE: Solo detecta interés si hay una SOLICITUD EXPLÍCITA de acción que requiera seguimiento humano.
        Preguntas informativas o comentarios generales NO cuentan como interés a efectos de inyección en CRM.

        Mensaje a analizar: "{message_text}"

        Responde ÚNICAMENTE con un JSON válido que contenga estos campos exactos:
        {{
            "shows_interest": true/false,
            "interest_type": "visita/contacto/informacion/compra/otro",
            "urgency_level": "inmediata/esta_semana/sin_urgencia",
            "confidence_score": 0-100,
            "requires_human_followup": true/false,
            "reason": "breve explicación de por qué sí/no requiere seguimiento humano",
            "extracted_info": {{
                "presupuesto": "valor extraído o null",
                "ubicacion": "ubicación mencionada o null",
                "tipo_propiedad": "tipo mencionado o null"
            }}
        }}
        """

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Eres un experto en análisis de leads inmobiliarios. Tu tarea es detectar interés expreso en visitar, contactar, obtener información o comprar propiedades. Responde ÚNICAMENTE con JSON válido."
                    },
                    {
                        "role": "user", 
                        "content": analysis_prompt
                    }
                ],
                response_format={ "type": "json_object" }
            )
            
            # Parse the AI response
            response_text = completion.choices[0].message.content.strip()
            result = json.loads(response_text)
            
            # Validate and clean the result
            result["shows_interest"] = bool(result.get("shows_interest", False))
            result["interest_type"] = result.get("interest_type", "otro")
            result["urgency_level"] = result.get("urgency_level", "sin_urgencia")
            result["confidence_score"] = max(0, min(100, int(result.get("confidence_score", 0))))
            result["requires_human_followup"] = bool(result.get("requires_human_followup", False))
            result["reason"] = result.get("reason", "")
            
            # Ensure extracted_info is properly formatted
            extracted_info = result.get("extracted_info", {})
            if not isinstance(extracted_info, dict):
                extracted_info = {}
            
            result["extracted_info"] = {
                "presupuesto": extracted_info.get("presupuesto"),
                "ubicacion": extracted_info.get("ubicacion"),
                "tipo_propiedad": extracted_info.get("tipo_propiedad")
            }
            
            logger.info(f"AI Lead interest detection result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.error(f"Raw response: {response_text}")
            # Fallback to basic detection
            return _fallback_interest_detection(message_text)
            
        except Exception as e:
            logger.error(f"Error calling AI for interest detection: {e}")
            # Fallback to basic detection
            return _fallback_interest_detection(message_text)
        
    except Exception as e:
        logger.error(f"Error in detect_lead_interest: {e}")
        return {
            "shows_interest": False,
            "interest_type": "otro",
            "urgency_level": "sin_urgencia",
            "confidence_score": 0,
            "extracted_info": {},
            "detected_interests": []
        }


def _fallback_interest_detection(message_text: str) -> dict:
    """
    Fallback method using simple keyword detection if AI fails.
    Only detects EXPLICIT requests, not general questions.
    """
    message_lower = message_text.lower()
    
    # EXPLICIT request patterns only - no general questions
    explicit_interest_patterns = {
        'visita': [
            r'quiero\s+visitar', r'me\s+gustaría\s+visitar', r'deseo\s+ver',
            r'puedo\s+agendar', r'quisiera\s+visitar', r'me\s+gustaría\s+ver'
        ],
        'contacto': [
            r'me\s+puede\s+contactar', r'quisiera\s+que\s+me\s+contacten',
            r'me\s+gustaría\s+hablar', r'puede\s+llamarme'
        ],
        'informacion': [
            r'necesito\s+más\s+información', r'me\s+gustaría\s+recibir\s+info',
            r'quisiera\s+más\s+detalles', r'puede\s+enviarme\s+información'
        ],
        'compra': [
            r'me\s+interesa\s+comprar', r'quisiera\s+comprar',
            r'me\s+gustaría\s+adquirir', r'estoy\s+interesado\s+en\s+comprar'
        ]
    }
    
    detected_interests = []
    confidence_score = 0
    
    for interest_type, patterns in explicit_interest_patterns.items():
        for pattern in patterns:
            if re.search(pattern, message_lower):
                detected_interests.append(interest_type)
                confidence_score += 30  # Higher score for explicit patterns
                break  # Only count once per interest type
    
    shows_interest = len(detected_interests) > 0
    
    # Determine primary interest type
    if 'compra' in detected_interests:
        interest_type = "compra"
    elif 'visita' in detected_interests:
        interest_type = "visita"
    elif 'contacto' in detected_interests:
        interest_type = "contacto"
    elif 'informacion' in detected_interests:
        interest_type = "informacion"
    else:
        interest_type = "otro"
    
    return {
        "shows_interest": shows_interest,
        "interest_type": interest_type,
        "urgency_level": "sin_urgencia",
        "confidence_score": min(100, confidence_score),
        "extracted_info": {
            "presupuesto": None,
            "ubicacion": None,
            "tipo_propiedad": None
        },
        "detected_interests": detected_interests
    }


async def auto_inject_missing_lead(client, db: Session, thread_record, message_text: str) -> bool:
    """
    Detecta automáticamente si un mensaje indica interés y autoinyecta el lead si es necesario.
    Retorna True si se inyectó un lead, False en caso contrario.
    """
    try:
        # Verificar si ya existe un lead calificado para este número
        existing_lead = db.query(QualifiedLead).filter_by(telefono=thread_record.sender).first()
        if existing_lead:
            logger.info(f"Lead already exists for {thread_record.sender}, skipping auto-injection")
            return False
        
        # Ignore the very first user message in a thread (campaign auto-greetings may contain trigger words)
        try:
            user_msg_count = db.query(Message).filter(
                Message.thread_id == thread_record.id,
                Message.role == "user"
            ).count()
            if user_msg_count <= 1:
                logger.info(f"Skipping intent analysis for first user message in thread {thread_record.thread_id}")
                return False
        except Exception:
            pass
        
        # Detectar interés en el mensaje
        interest_analysis = await detect_lead_interest(client, message_text)
        
        if not interest_analysis.get("shows_interest", False):
            logger.info(f"No interest detected in message from {thread_record.sender}")
            return False
        
        confidence_score = interest_analysis.get("confidence_score", 0)
        if confidence_score < 70:  # Higher threshold for explicit interest only
            logger.info(f"Interest confidence too low ({confidence_score}) for {thread_record.sender} - only explicit interest accepted")
            return False
        
        # Ensure AI says this requires human follow-up (to avoid generic info-only cases)
        if not interest_analysis.get("requires_human_followup", False):
            logger.info(f"AI marked interest but no human follow-up required; skipping CRM injection for {thread_record.sender}")
            return False
        
        # Extraer información del mensaje
        extracted_info = interest_analysis.get("extracted_info", {})
        interest_type = interest_analysis.get("interest_type", "otro")
        urgency_level = interest_analysis.get("urgency_level", "sin_urgencia")
        
        # Only auto-inject for explicit actions (not generic information requests)
        allowed_types = {"visita", "contacto", "compra"}
        if interest_type not in allowed_types:
            logger.info(f"Interest type '{interest_type}' is not in allowed explicit actions; skipping auto-injection for {thread_record.sender}")
            return False
        
        # Determinar flags de interés
        desea_visita = interest_type in ["visita", "compra"]
        desea_llamada = interest_type in ["contacto", "compra", "informacion"]
        desea_informacion = interest_type in ["informacion", "compra"]
        
        # Crear datos del lead
        lead_data = {
            "telefono": thread_record.sender,
            "nombre": thread_record.sender_display_name or "Cliente",
            "fuente": thread_record.sender_platform or "WhatsApp",
            "motivo_interes": interest_type,
            "urgencia_compra": urgency_level,
            "desea_visita": desea_visita,
            "desea_llamada": desea_llamada,
            "desea_informacion": desea_informacion,
            "metodo_contacto_preferido": "WhatsApp",
            "ciudad_interes": extracted_info.get("ubicacion"),
            "tipo_propiedad": extracted_info.get("tipo_propiedad"),
            "presupuesto": extracted_info.get("presupuesto"),
            "proyecto_interes": "Yucatan"  # Default project
        }
        
        # Procesar presupuesto si existe
        if lead_data.get("presupuesto"):
            try:
                import re
                numbers = re.findall(r'\d+', lead_data["presupuesto"])
                if len(numbers) >= 2:
                    lead_data['presupuesto_min'] = int(numbers[0]) * 1000000
                    lead_data['presupuesto_max'] = int(numbers[1]) * 1000000
                elif len(numbers) == 1:
                    lead_data['presupuesto_max'] = int(numbers[0]) * 1000000
            except:
                pass
        
        # Calificar el lead
        from app.execute_functions import qualify_lead
        qualify_result = await qualify_lead(db, lead_data)
        
        if qualify_result.get("success"):
            logger.info(f"Auto-injected lead for {thread_record.sender} with confidence {confidence_score}")
            return True
        else:
            logger.error(f"Failed to auto-inject lead for {thread_record.sender}: {qualify_result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error in auto_inject_missing_lead: {e}")
        return False


async def verify_and_fix_missing_leads(client, db: Session, thread_record) -> bool:
    """
    Verifica si un thread debería tener un lead calificado y lo crea si falta.
    Se ejecuta después de cada conversación para capturar leads perdidos.
    """
    try:
        # Verificar si ya existe un lead calificado
        existing_lead = db.query(QualifiedLead).filter_by(telefono=thread_record.sender).first()
        if existing_lead:
            return False
        
        # Obtener todas las conversaciones del thread
        conversations = db.query(Conversation).filter_by(thread_id=thread_record.id).order_by(Conversation.created_at).all()
        
        if not conversations:
            return False
        
        # Analizar todas las conversaciones para detectar interés
        all_messages = []
        first_user_skipped = False
        for conv in conversations:
            if conv.message:
                if not first_user_skipped:
                    first_user_skipped = True
                else:
                    all_messages.append(f"Cliente: {conv.message}")
            if conv.response:
                all_messages.append(f"Asistente: {conv.response}")
        
        conversation_text = "\n".join(all_messages)
        
        # Detectar interés en toda la conversación
        interest_analysis = await detect_lead_interest(client, conversation_text)
        
        if not interest_analysis.get("shows_interest", False):
            return False
        
        confidence_score = interest_analysis.get("confidence_score", 0)
        if confidence_score < 70:  # Higher threshold for explicit interest only
            return False
        
        # Extraer información de la conversación
        extracted_info = interest_analysis.get("extracted_info", {})
        interest_type = interest_analysis.get("interest_type", "otro")
        urgency_level = interest_analysis.get("urgency_level", "sin_urgencia")
        
        # Only fix when explicit actions are present (avoid generic info-only cases)
        allowed_types = {"visita", "contacto", "compra"}
        if interest_type not in allowed_types:
            return False
        
        # Determinar flags de interés
        desea_visita = interest_type in ["visita", "compra"]
        desea_llamada = interest_type in ["contacto", "compra", "informacion"]
        desea_informacion = interest_type in ["informacion", "compra"]
        
        # Crear datos del lead
        lead_data = {
            "telefono": thread_record.sender,
            "nombre": thread_record.sender_display_name or "Cliente",
            "fuente": thread_record.sender_platform or "WhatsApp",
            "motivo_interes": interest_type,
            "urgencia_compra": urgency_level,
            "desea_visita": desea_visita,
            "desea_llamada": desea_llamada,
            "desea_informacion": desea_informacion,
            "metodo_contacto_preferido": "WhatsApp",
            "ciudad_interes": extracted_info.get("ubicacion"),
            "tipo_propiedad": extracted_info.get("tipo_propiedad"),
            "presupuesto": extracted_info.get("presupuesto"),
            "proyecto_interes": "Yucatan"
        }
        
        # Procesar presupuesto si existe
        if lead_data.get("presupuesto"):
            try:
                import re
                numbers = re.findall(r'\d+', lead_data["presupuesto"])
                if len(numbers) >= 2:
                    lead_data['presupuesto_min'] = int(numbers[0]) * 1000000
                    lead_data['presupuesto_max'] = int(numbers[1]) * 1000000
                elif len(numbers) == 1:
                    lead_data['presupuesto_max'] = int(numbers[0]) * 1000000
            except:
                pass
        
        # Calificar el lead
        from app.execute_functions import qualify_lead
        qualify_result = await qualify_lead(db, lead_data)
        
        if qualify_result.get("success"):
            logger.info(f"Fixed missing lead for {thread_record.sender} with confidence {confidence_score}")
            return True
        else:
            logger.error(f"Failed to fix missing lead for {thread_record.sender}: {qualify_result.get('error')}")
            return False
            
    except Exception as e:
        logger.error(f"Error in verify_and_fix_missing_leads: {e}")
        return False


