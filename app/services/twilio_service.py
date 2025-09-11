# app/services/twilio_service.py

import os
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from twilio.rest import Client

from app.models import MessageLog

logger = logging.getLogger(__name__)


class TwilioService:
    """Service class for Twilio operations and message logging."""
    
    def __init__(self):
        """Initialize Twilio client and configuration."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        self.messaging_service_sid = os.getenv("TWILIO_MESSAGING_SERVICE_SID")
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            logger.warning("Twilio credentials not configured")
    
    def log_message(
        self,
        db: Session,
        direction: str,
        from_number: str,
        to_number: str,
        message_body: str,
        message_sid: Optional[str] = None,
        status: Optional[str] = None,
        thread_id: Optional[int] = None,
        response_time: Optional[int] = None,
        campaign_id: Optional[int] = None,
        platform: str = "whatsapp"
    ) -> MessageLog:
        """
        Log a message to the database.
        
        Args:
            db: Database session
            direction: 'inbound' or 'outbound'
            from_number: Sender phone number
            to_number: Recipient phone number
            message_body: Message content
            message_sid: Twilio message SID (optional)
            status: Message status (optional)
            thread_id: Thread ID (optional)
            response_time: Response time in seconds (optional)
            campaign_id: Campaign ID (optional)
            platform: Platform name (default: 'whatsapp')
            
        Returns:
            MessageLog: The created message log entry
        """
        try:
            # Check if message with this SID already exists (handle duplicate webhooks)
            if message_sid:
                existing_message = db.query(MessageLog).filter(
                    MessageLog.message_sid == message_sid
                ).first()
                
                if existing_message:
                    logger.info(f"Message with SID {message_sid} already exists, returning existing record")
                    return existing_message
            
            message_log = MessageLog(
                message_sid=message_sid,
                direction=direction,
                from_number=from_number,
                to_number=to_number,
                message_body=message_body,
                message_status=status,
                platform=platform,
                thread_id=thread_id,
                campaign_id=campaign_id,
                response_time=response_time,
                webhook_received_at=datetime.now(timezone.utc)
            )
            
            db.add(message_log)
            db.commit()
            db.refresh(message_log)
            
            logger.debug(f"Logged {direction} message: {message_sid}")
            return message_log
            
        except Exception as e:
            logger.error(f"Error logging message: {e}")
            db.rollback()
            raise
    
    def get_template_by_name(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a message template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Dict containing template data or None if not found
        """
        # Simple template storage - in production, this could be database-driven
        templates = {
            "followup": {
                "body": "Hola! Te escribo para seguir en contacto sobre tu interés en nuestros desarrollos exclusivos. ¿Te gustaría agendar una visita o tienes alguna pregunta específica?",
                "name": "followup"
            },
            "welcome": {
                "body": "¡Hola! Bienvenido a nuestros desarrollos exclusivos. Soy tu asistente virtual y estoy aquí para ayudarte con información sobre nuestros proyectos residenciales.",
                "name": "welcome"
            }
        }
        
        return templates.get(template_name)
    
    async def send_message(
        self,
        to_number: str,
        message_body: str,
        template_name: Optional[str] = None,
        use_template: bool = False
    ) -> Optional[str]:
        """
        Send a message via Twilio.
        
        Args:
            to_number: Recipient phone number
            message_body: Message content
            template_name: Template name (optional)
            use_template: Whether to use template messaging (optional)
            
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return None
        
        try:
            # Ensure proper phone number formatting
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            sender = f'whatsapp:{self.whatsapp_number}'
            if sender.startswith('whatsapp:whatsapp:'):
                sender = f'whatsapp:{self.whatsapp_number.replace("whatsapp:", "")}'
            
            # Use messaging service if configured and template is specified
            if use_template and self.messaging_service_sid:
                message = self.client.messages.create(
                    body=message_body,
                    messaging_service_sid=self.messaging_service_sid,
                    to=to_number
                )
            else:
                message = self.client.messages.create(
                    body=message_body,
                    from_=sender,
                    to=to_number
                )
            
            logger.info(f"Message sent to {to_number}: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Failed to send message to {to_number}: {e}")
            return None
    
    def send_media_message(
        self,
        to_number: str,
        media_url: str,
        message_body: str = "",
        media_type: str = "image"
    ) -> Optional[str]:
        """
        Send a media message via Twilio.
        
        Args:
            to_number: Recipient phone number
            media_url: URL of the media to send
            message_body: Text message to accompany the media
            media_type: Type of media ('image', 'pdf', etc.)
            
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.client:
            logger.error("Twilio client not initialized")
            return None
        
        try:
            # Ensure proper phone number formatting
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            sender = f'whatsapp:{self.whatsapp_number}'
            if sender.startswith('whatsapp:whatsapp:'):
                sender = f'whatsapp:{self.whatsapp_number.replace("whatsapp:", "")}'
            
            message = self.client.messages.create(
                body=message_body,
                from_=sender,
                to=to_number,
                media_url=[media_url]
            )
            
            logger.info(f"Media message sent to {to_number}: {message.sid}")
            return message.sid
            
        except Exception as e:
            logger.error(f"Failed to send media message to {to_number}: {e}")
            return None
