# app/execute_functions.py

import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from app.models import CustomerInfo, QualifiedLead, Thread
from app.timeout_util import with_timeout
from app.utils import (
    analyze_conversation_thread,
    logger,
    send_twilio_media_message,
    create_hubspot_contact,
    send_yucatan_location
)
from openai import OpenAI
import colorama
from colorama import Fore, Style

# Initialize colorama for colored output
colorama.init()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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

# Get the root directory of the project (one level up from app directory)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to fotos.json - try multiple possible locations
POSSIBLE_PATHS = [
    os.path.join(ROOT_DIR, "assets", "fotos.json"),  # Local development
    os.path.join(os.getcwd(), "assets", "fotos.json"),  # Render deployment
    os.path.join("/opt/render/project/src", "assets", "fotos.json"),  # Render specific
    os.path.join(os.path.dirname(__file__), "..", "assets", "fotos.json"),  # Relative to current file
]

# Find the first existing path
FOTOS_JSON_PATH = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        FOTOS_JSON_PATH = path
        break

if not FOTOS_JSON_PATH:
    # If no path found, use the first one as default
    FOTOS_JSON_PATH = POSSIBLE_PATHS[0]

logger.info(f"Loading photos database from: {FOTOS_JSON_PATH}")
logger.info(f"File exists: {os.path.exists(FOTOS_JSON_PATH)}")

# In app/execute_functions.py

async def execute_function(tool_call, db: Session, sender_info=None):
    """
    Execute a function based on the tool_call data and return relevant output.

    Args:
        tool_call (dict): Contains function_name and arguments
        db (Session): Database session
        sender_info (dict): Contains sender's number and platform

    Returns:
        dict: Result to be returned to the assistant
    """
    function_name = tool_call.get("function_name")
    
    try:
        function_arguments = json.loads(tool_call.get("arguments", "{}"))
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing function arguments: {e}")
        # Try to fix common JSON parsing issues
        arguments_str = tool_call.get("arguments", "{}")
        if arguments_str.endswith("]}"):
            # Fix for msearch function with malformed JSON
            try:
                # Extract the array part
                if "[" in arguments_str and "]" in arguments_str:
                    array_part = arguments_str[arguments_str.find("["):arguments_str.rfind("]")+1]
                    # Parse as array
                    search_terms = json.loads(array_part)
                    # Convert to dictionary format
                    function_arguments = {"search_terms": search_terms}
                else:
                    function_arguments = {}
            except Exception as inner_e:
                logger.error(f"Failed to fix JSON: {inner_e}")
                function_arguments = {}
        else:
            function_arguments = {}

    # Add sender information if available
    if sender_info:
        # Only set telefono for WhatsApp users, not web widget users
        platform = sender_info.get("platform", "whatsapp")
        if platform.lower() == "whatsapp":
            function_arguments["telefono"] = sender_info.get("number", "")
        # Always set the source
        function_arguments["fuente"] = platform


    # Handle enviar_foto function
    if function_name == "enviar_foto":
        try:
            # Extract parameters with defaults
            categoria = function_arguments.get("categoria", "")
            subcategoria = function_arguments.get("subcategoria", None)
            tipo_apartamento = function_arguments.get("tipo_apartamento", None)
            area = function_arguments.get("area", None)
            mensaje_acompañante = function_arguments.get("mensaje_acompañante", None)
            buscar_alternativa = function_arguments.get("buscar_alternativa", True)
            
            logger.info(f"Enviando foto: categoria={categoria}, subcategoria={subcategoria}, tipo={tipo_apartamento}")
            
            # Call the enviar_foto function
            result = enviar_foto(
                categoria=categoria,
                subcategoria=subcategoria,
                tipo_apartamento=tipo_apartamento,
                area=area,
                mensaje_acompañante=mensaje_acompañante,
                buscar_alternativa=buscar_alternativa
            )
            
            # Log the result
            logger.info(f"Resultado de enviar_foto: {result}")
            
            # If the function returned a photo URL, actually send it via Twilio
            if result.get("success") and result.get("photo_url"):
                telefono = function_arguments.get("telefono") or sender_info.get("number", "")
                if telefono:
                    try:
                        from app.utils import send_twilio_media_message
                        photo_url = result["photo_url"]
                        mensaje = result.get("text_sent", "Aquí tienes la imagen que solicitaste")
                        
                        # Send the image via Twilio
                        message_sid = send_twilio_media_message(
                            to_number=telefono,
                            media_url=photo_url,
                            message_body=mensaje,
                            media_type="image"
                        )
                        
                        logger.info(f"📸 Imagen enviada exitosamente a {telefono}: {message_sid}")
                        result["message_sid"] = message_sid
                        result["sent_via_twilio"] = True
                        
                    except Exception as send_error:
                        logger.error(f"Error enviando imagen via Twilio: {send_error}")
                        result["twilio_error"] = str(send_error)
                else:
                    logger.warning("No se pudo obtener número de teléfono para enviar imagen")
                    result["error"] = "No se pudo obtener número de teléfono"
            
            # Return a serializable representation of the result
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error en enviar_foto: {e}")
            return json.dumps({
                "success": False,
                "error": f"Error al enviar la foto: {str(e)}"
            })

    elif function_name == "send_brochure":
        try:
            telefono = function_arguments.get("telefono") or sender_info.get("number", "")
            if not telefono:
                return json.dumps({
                    "success": False,
                    "error": "Número de teléfono requerido"
                })
            
            result = send_brochure(telefono)
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error en send_brochure: {e}")
            return json.dumps({
                "success": False,
                "error": f"Error al enviar el brochure: {str(e)}"
            })

    elif function_name == "forward_media":
        try:
            media_url = function_arguments.get("media_url", "")
            media_type = function_arguments.get("media_type", "image")
            message_body = function_arguments.get("message_body", "")
            telefono = function_arguments.get("telefono") or sender_info.get("number", "")
            
            if not telefono:
                return json.dumps({
                    "success": False,
                    "error": "Número de teléfono requerido"
                })
                
            if not media_url:
                return json.dumps({
                    "success": False,
                    "error": "URL de media requerida"
                })
            
            logger.info(f"Forwarding media: {media_url} to {telefono}")
            
            # Use the existing media sending function
            message_sid = send_twilio_media_message(
                to_number=telefono,
                media_url=media_url,
                message_body=message_body,
                media_type=media_type
            )
            
            if message_sid:
                return json.dumps({
                    "success": True,
                    "message": "Media reenviada exitosamente",
                    "message_sid": message_sid
                })
            else:
                return json.dumps({
                    "success": False,
                    "error": "No se pudo reenviar la media"
                })
                
        except Exception as e:
            logger.error(f"Error en forward_media: {e}")
            return json.dumps({
                "success": False,
                "error": f"Error al reenviar la media: {str(e)}"
            })

    elif function_name == "capture_customer_info":
        try:
            return await capture_customer_info(db, function_arguments)
        except Exception as e:
            logger.error(f"Failed to execute capture_customer_info: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "No se pudo guardar la información. Por favor, intenta nuevamente."
            }

    elif function_name == "qualify_lead":
        try:
            return await qualify_lead(db, function_arguments)
        except Exception as e:
            logger.error(f"Failed to execute qualify_lead: {e}")
            db.rollback()
            return {
                "success": False,
                "error": f"Error al registrar tu información: {str(e)}"
            }




    elif function_name == "send_yucatan_location":
        try:
            # Get the sender's phone number
            phone_number = sender_info.get("number") if sender_info else function_arguments.get("telefono")

            if not phone_number:
                return {
                    "success": False,
                    "error": "No se pudo enviar la ubicación porque no se encontró un número de teléfono."
                }

            # Send the location
            message_sid = send_yucatan_location(phone_number)

            if message_sid:
                return {
                    "success": True,
                    "message": "Te he enviado la ubicación de Chablé Yucatan. ¿Te gustaría conocer más detalles sobre el proyecto?"
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo enviar la ubicación. Por favor, intenta nuevamente."
                }
        except Exception as e:
            logger.error(f"Error sending Yucatan location: {str(e)}")
            return {
                "success": False,
                "error": f"Error al enviar la ubicación: {str(e)}"
            }

    elif function_name == "provide_contact_info":
        try:
            result = await provide_contact_info(db, function_arguments)
            return result["message"] if result["success"] else result["error"]
        except Exception as e:
            logger.error(f"Error executing provide_contact_info: {e}")
            return "Lo siento, hubo un error al procesar tu solicitud de contacto."

    logger.warning(f"Función {function_name} no reconocida.")
    return "Función no reconocida"


@with_timeout(10)  # Apply 10-second timeout
async def capture_customer_info(db: Session, customer_data):
    try:
        # Handle presupuesto parameter conversion
        # The assistant might send 'presupuesto' but the model expects 'presupuesto_min' and 'presupuesto_max'
        if 'presupuesto' in customer_data:
            presupuesto_value = customer_data.pop('presupuesto')  # Remove the old key
            # If it's a range like "300-500 millones", try to parse it
            if presupuesto_value and isinstance(presupuesto_value, str):
                # Try to extract numeric values
                import re
                numbers = re.findall(r'\d+', presupuesto_value)
                if len(numbers) >= 2:
                    # Range detected
                    customer_data['presupuesto_min'] = int(numbers[0]) * 1000000  # Convert to millions
                    customer_data['presupuesto_max'] = int(numbers[1]) * 1000000
                elif len(numbers) == 1:
                    # Single value, use as max
                    customer_data['presupuesto_max'] = int(numbers[0]) * 1000000
                # If no numbers found, leave presupuesto fields empty
            
        # Remove any keys that don't exist in the CustomerInfo model
        valid_fields = {
            'nombre', 'email', 'telefono', 'fuente', 'ciudad_interes', 
            'tipo_propiedad', 'presupuesto_min', 'presupuesto_max', 'interes_compra'
        }
        
        # Filter customer_data to only include valid fields
        filtered_data = {k: v for k, v in customer_data.items() if k in valid_fields and v}
        
        logger.info(f"Filtered customer data: {filtered_data}")
        
        # Handle web widget users who don't have phone numbers
        is_web_widget = filtered_data.get("fuente", "").lower() == "web"
        
        # Check if customer already exists
        existing_customer = None
        if filtered_data.get("telefono"):
            # For WhatsApp users, search by phone number
            existing_customer = db.query(CustomerInfo).filter_by(
                telefono=filtered_data.get("telefono")
            ).first()
        elif is_web_widget and filtered_data.get("nombre"):
            # For web widget users without phone, search by name and source
            existing_customer = db.query(CustomerInfo).filter_by(
                nombre=filtered_data.get("nombre"),
                fuente="web"
            ).first()

        if existing_customer:
            # Update existing customer
            for key, value in filtered_data.items():
                if value and hasattr(existing_customer, key):
                    setattr(existing_customer, key, value)

            db.commit()
            customer_id = existing_customer.id
        else:
            # Create new customer
            new_customer = CustomerInfo(**filtered_data)
            db.add(new_customer)
            db.commit()
            customer_id = new_customer.id

        # Check if qualified lead already exists and enhance it
        existing_lead = None
        if filtered_data.get("telefono"):
            # For WhatsApp users, search by phone number
            existing_lead = db.query(QualifiedLead).filter_by(telefono=filtered_data.get("telefono")).first()
        elif is_web_widget and filtered_data.get("nombre"):
            # For web widget users without phone, search by name and source
            existing_lead = db.query(QualifiedLead).filter_by(
                nombre=filtered_data.get("nombre"),
                fuente="web"
            ).first()

        if existing_lead:
            # Enhance existing lead with new customer info
            if filtered_data.get("nombre") and filtered_data.get("nombre") != existing_lead.nombre:
                existing_lead.nombre = filtered_data.get("nombre")
            if filtered_data.get("email") and filtered_data.get("email") != existing_lead.email:
                existing_lead.email = filtered_data.get("email")
            if filtered_data.get("tipo_propiedad"):
                existing_lead.tipo_propiedad = filtered_data.get("tipo_propiedad")
            if filtered_data.get("presupuesto_min"):
                existing_lead.presupuesto_min = filtered_data.get("presupuesto_min")
            if filtered_data.get("presupuesto_max"):
                existing_lead.presupuesto_max = filtered_data.get("presupuesto_max")
            
            db.commit()
            logger.info(f"Enhanced existing lead {existing_lead.id} with customer info")
            
            # Inject updated lead to Lasso CRM
            try:
                from app.crm_integration import inject_qualified_lead_to_crm
                crm_result = await inject_qualified_lead_to_crm(db, existing_lead)
                
                if crm_result.get("success"):
                    logger.info(f"Successfully updated lead {existing_lead.id} in Lasso CRM")
                else:
                    logger.error(f"Failed to update lead {existing_lead.id} in Lasso CRM: {crm_result.get('errors')}")
            except Exception as e:
                logger.error(f"Error updating lead in Lasso CRM: {e}")
        else:
            # Create new qualified lead with the customer info
            # QualifiedLead is imported at module level; avoid re-importing inside the function to prevent scope issues
            
            # Priority for name: 1) filtered_data nombre, 2) existing customer name, 3) display name
            final_name = filtered_data.get("nombre", "")
            if not final_name and existing_customer and existing_customer.nombre:
                # Use existing customer's real name if available
                final_name = existing_customer.nombre
            elif not final_name and filtered_data.get("telefono"):
                # Fallback to display name only if no other name available
                thread_record = db.query(Thread).filter_by(sender=filtered_data.get("telefono")).first()
                if thread_record and thread_record.sender_display_name:
                    final_name = thread_record.sender_display_name
            
            new_lead = QualifiedLead(
                customer_info_id=customer_id,
                nombre=final_name,
                email=filtered_data.get("email", ""),
                telefono=filtered_data.get("telefono", ""),
                fuente=filtered_data.get("fuente", "WhatsApp"),
                tipo_propiedad=filtered_data.get("tipo_propiedad", ""),
                presupuesto_min=filtered_data.get("presupuesto_min"),
                presupuesto_max=filtered_data.get("presupuesto_max"),
                motivo_interes="informacion_recopilada",
                desea_informacion=True
            )
            db.add(new_lead)
            db.commit()
            logger.info(f"Created new qualified lead from customer info capture")
            
            # Inject new lead to Lasso CRM
            try:
                from app.crm_integration import inject_qualified_lead_to_crm
                crm_result = await inject_qualified_lead_to_crm(db, new_lead)
                
                if crm_result.get("success"):
                    logger.info(f"Successfully injected new lead {new_lead.id} to Lasso CRM")
                else:
                    logger.error(f"Failed to inject new lead {new_lead.id} to Lasso CRM: {crm_result.get('errors')}")
            except Exception as e:
                logger.error(f"Error injecting new lead to Lasso CRM: {e}")

        # Removed redundant extra HubSpot sync to avoid duplicate create calls

        # Return success message with customer information
        return {
            "success": True,
            "message": f"Información del cliente guardada exitosamente. Gracias, {filtered_data.get('nombre', 'cliente')}!",
            "customer_id": customer_id
        }
    except Exception as e:
        logger.error(f"Error storing customer info: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": f"Error al guardar la información del cliente: {str(e)}"
        }


async def qualify_lead(db: Session, lead_data):
    try:
        # First, create or get customer info
        customer_info = None
        is_web_widget = lead_data.get("fuente", "").lower() == "web"
        
        if lead_data.get("telefono"):
            # Try to find existing customer by phone number
            customer_info = db.query(CustomerInfo).filter_by(
                telefono=lead_data.get("telefono")
            ).first()
        elif is_web_widget and lead_data.get("nombre"):
            # For web widget users, try to find by name and source
            customer_info = db.query(CustomerInfo).filter_by(
                nombre=lead_data.get("nombre"),
                fuente="web"
            ).first()
        
        # If not found, create new customer
        if not customer_info:
            # Use display name if name is not provided
            display_name = lead_data.get("nombre", "")
            if not display_name and lead_data.get("telefono"):
                # Try to get display name from thread record
                thread_record = db.query(Thread).filter_by(sender=lead_data.get("telefono")).first()
                if thread_record and thread_record.sender_display_name:
                    display_name = thread_record.sender_display_name
            
            customer_info = CustomerInfo(
                nombre=display_name,
                email=lead_data.get("email", ""),
                telefono=lead_data.get("telefono", ""),
                fuente=lead_data.get("fuente", "WhatsApp")
            )
            db.add(customer_info)
            db.commit()
            db.refresh(customer_info)

        if not customer_info:
            return {
                "success": False,
                "error": "No se pudo crear o encontrar la información del cliente"
            }

        # Priority for name: 1) lead_data nombre, 2) existing customer name, 3) display name
        final_name = lead_data.get("nombre", "")
        if not final_name and customer_info.nombre:
            # Use existing customer's real name if available
            final_name = customer_info.nombre
        elif not final_name and lead_data.get("telefono"):
            # Fallback to display name only if no other name available
            thread_record = db.query(Thread).filter_by(sender=lead_data.get("telefono")).first()
            if thread_record and thread_record.sender_display_name:
                final_name = thread_record.sender_display_name
        
        # Check if qualified lead already exists and update it
        existing_lead = None
        if lead_data.get("telefono"):
            # For WhatsApp users, search by phone number
            existing_lead = db.query(QualifiedLead).filter_by(telefono=lead_data.get("telefono")).first()
        elif is_web_widget and lead_data.get("nombre"):
            # For web widget users, search by name and source
            existing_lead = db.query(QualifiedLead).filter_by(
                nombre=lead_data.get("nombre"),
                fuente="web"
            ).first()
        
        if existing_lead:
            # Update existing lead with new information
            if final_name and final_name != existing_lead.nombre:
                existing_lead.nombre = final_name
            if lead_data.get("email") and lead_data.get("email") != existing_lead.email:
                existing_lead.email = lead_data.get("email")
            if lead_data.get("motivo"):
                existing_lead.motivo_interes = lead_data.get("motivo")
            if lead_data.get("urgencia"):
                existing_lead.urgencia_compra = lead_data.get("urgencia")
            if lead_data.get("metodo_contacto_preferido"):
                existing_lead.metodo_contacto_preferido = lead_data.get("metodo_contacto_preferido")
            
            # Update contact preferences based on motivo
            if lead_data.get("motivo") == "informacion":
                existing_lead.desea_informacion = True
            elif lead_data.get("motivo") == "visita":
                existing_lead.desea_visita = True
            elif lead_data.get("motivo") == "llamada":
                existing_lead.desea_llamada = True
            
            db.commit()
            logger.info(f"Updated existing qualified lead {existing_lead.id} with new information")
            
            # Generate conversation summary for the update
            summary = f"Lead actualizado: {lead_data.get('motivo', 'N/A')} - {lead_data.get('urgencia', 'N/A')}"
            if lead_data.get("motivo") == "disponibilidad":
                summary = f"Cliente interesado en disponibilidad de apartamentos. Urgencia: {lead_data.get('urgencia', 'N/A')}"
            elif lead_data.get("motivo") == "informacion":
                summary = f"Cliente solicita información adicional. Urgencia: {lead_data.get('urgencia', 'N/A')}"
            elif lead_data.get("motivo") == "visita":
                summary = f"Cliente solicita visita al proyecto. Urgencia: {lead_data.get('urgencia', 'N/A')}"
            elif lead_data.get("motivo") == "llamada":
                summary = f"Cliente solicita llamada. Urgencia: {lead_data.get('urgencia', 'N/A')}"
            
            # Update lead in Lasso CRM
            try:
                from app.crm_integration import inject_qualified_lead_to_crm
                crm_result = await inject_qualified_lead_to_crm(db, existing_lead)
                
                if crm_result.get("success"):
                    logger.info(f"Successfully updated lead {existing_lead.id} in Lasso CRM")
                else:
                    logger.error(f"Failed to update lead {existing_lead.id} in Lasso CRM: {crm_result.get('errors')}")
            except Exception as e:
                logger.error(f"Error updating lead in Lasso CRM: {e}")
            
            return {
                "success": True,
                "message": f"Información actualizada exitosamente. Gracias, {final_name}!",
                "lead_id": existing_lead.id,
                "updated": True
            }
        
        # Create new qualified lead only if none exists
        customer_id = customer_info.id

        # Create new qualified lead object
        new_lead = QualifiedLead(
            customer_info_id=customer_id,  # Now we're sure this exists
            nombre=final_name,
            email=lead_data.get("email", ""),
            telefono=lead_data.get("telefono", ""),
            fuente=lead_data.get("fuente", "WhatsApp"),
            ciudad_interes=lead_data.get("ciudad_interes", ""),
            proyecto_interes=lead_data.get("proyecto_interes", ""),
            tipo_propiedad=lead_data.get("tipo_propiedad", ""),
            tamano_minimo=lead_data.get("tamano_minimo"),
            habitaciones=lead_data.get("habitaciones"),
            banos=lead_data.get("banos"),
            presupuesto_min=lead_data.get("presupuesto_min"),
            presupuesto_max=lead_data.get("presupuesto_max"),
            motivo_interes=lead_data.get("motivo_interes", ""),
            urgencia_compra=lead_data.get("urgencia_compra", ""),
            metodo_contacto_preferido=lead_data.get("metodo_contacto_preferido", ""),
            horario_contacto_preferido=lead_data.get("horario_contacto_preferido", ""),
            desea_visita=lead_data.get("desea_visita", False),
            desea_llamada=lead_data.get("desea_llamada", False),
            desea_informacion=lead_data.get("desea_informacion", False)
        )

        # Add to database and commit
        db.add(new_lead)
        db.commit()

        # Generate more descriptive conversation summary
        summary = f"Lead calificado automáticamente con interés explícito: {lead_data.get('motivo_interes', 'N/A')}"
        if lead_data.get("motivo_interes") == "disponibilidad":
            summary = f"Cliente interesado en disponibilidad de apartamentos. Urgencia: {lead_data.get('urgencia_compra', 'N/A')}"
        elif lead_data.get("motivo_interes") == "informacion":
            summary = f"Cliente solicita información adicional. Urgencia: {lead_data.get('urgencia_compra', 'N/A')}"
        elif lead_data.get("motivo_interes") == "visita":
            summary = f"Cliente solicita visita al proyecto. Urgencia: {lead_data.get('urgencia_compra', 'N/A')}"
        elif lead_data.get("motivo_interes") == "llamada":
            summary = f"Cliente solicita llamada. Urgencia: {lead_data.get('urgencia_compra', 'N/A')}"
        
        interest_score = 85  # High score since we only inject explicit interest
        
        new_lead.conversation_summary = summary
        new_lead.deducted_interest = interest_score
        db.commit()

        # Inject to Lasso CRM automatically
        try:
            from app.crm_integration import inject_qualified_lead_to_crm
            crm_result = await inject_qualified_lead_to_crm(db, new_lead)
            
            if crm_result.get("success"):
                logger.info(f"Successfully injected lead {new_lead.id} to Lasso CRM")
            else:
                logger.error(f"Failed to inject lead {new_lead.id} to Lasso CRM: {crm_result.get('errors')}")
        except Exception as e:
            logger.error(f"Error injecting lead to Lasso CRM: {e}")

        logger.info(f"Updated lead analysis for lead ID {new_lead.id}")

        # Define next steps based on lead preferences
        next_steps = ""
        if lead_data.get("desea_visita"):
            next_steps += "Un asesor se pondrá en contacto para agendar tu visita. "
        if lead_data.get("desea_llamada"):
            next_steps += "Te llamaremos pronto para brindarte más información. "
        if lead_data.get("desea_informacion") or not next_steps:
            next_steps += "Te enviaremos información detallada sobre nuestros proyectos. "

        return {
            "success": True,
            "message": f"¡Excelente, {lead_data.get('nombre', '')}! Hemos registrado tu interés en nuestros proyectos. {next_steps}",
            "lead_id": new_lead.id
        }

    except Exception as e:
        logger.error(f"Error en qualify_lead: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": f"Error al registrar el lead: {str(e)}"
        }


def clean_text(text: str) -> str:
    """
    Clean text by replacing Unicode escape sequences with their actual characters.
    
    Args:
        text (str): Text that may contain Unicode escape sequences
        
    Returns:
        str: Cleaned text with proper characters
    """
    if not text:
        return ""
    return text.encode('utf-8').decode('unicode_escape')

def cargar_base_fotos() -> Dict[str, Any]:
    """
    Carga la base de datos de fotos desde el archivo JSON.
    
    Returns:
        dict: Base de datos de fotos o un diccionario vacío si hay errores
    """
    try:
        if os.path.exists(FOTOS_JSON_PATH):
            with open(FOTOS_JSON_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
                logger.info(f"Base de datos de fotos cargada exitosamente desde: {FOTOS_JSON_PATH}")
                logger.info(f"Residencias disponibles: {list(data.get('residencias', {}).keys())}")
                return data
        else:
            logger.error(f"Archivo de fotos no encontrado: {FOTOS_JSON_PATH}")
            logger.info("Usando base de datos de fotos de respaldo...")
            return get_fallback_photos_db()
    except Exception as e:
        logger.error(f"Error cargando base de datos de fotos: {str(e)}")
        logger.info("Usando base de datos de fotos de respaldo...")
        return get_fallback_photos_db()

def get_fallback_photos_db() -> Dict[str, Any]:
    """
    Base de datos de fotos de respaldo en caso de que el archivo JSON no esté disponible.
    
    Returns:
        dict: Base de datos de fotos hardcodeada
    """
    return {
        "residencias": {
            "kin": {
                "nombre": "KIN Residence",
                "descripcion": "Residencia más exclusiva con 5 recámaras, piscina y jacuzzi de 127m², cine, spa, gimnasio, jardín en azotea y cuarto de servicio",
                "fotos": {
                    "interior": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450607/residencia-kin-1_vfzatf.webp",
                            "descripcion": "Interior de la residencia KIN",
                            "tipo": "interior"
                        }
                    ],
                    "planos": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450607/KinTOrre_sohyjz.webp",
                            "descripcion": "Plano de la residencia KIN",
                            "tipo": "plano"
                        }
                    ]
                }
            },
            "kuxtal": {
                "nombre": "KUXTAL Residence",
                "descripcion": "Residencia de 4 recámaras con piscina de 95m², terraza con ka'anche' y cuarto de servicio",
                "fotos": {
                    "interior": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450608/residencias-kuxtal-1_vnpeyt.webp",
                            "descripcion": "Interior de la residencia KUXTAL",
                            "tipo": "interior"
                        }
                    ],
                    "planos": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450607/PlanoKuxtal_ojubkc.webp",
                            "descripcion": "Plano de la residencia KUXTAL",
                            "tipo": "plano"
                        }
                    ]
                }
            },
            "ool": {
                "nombre": "ÓOL Residence",
                "descripcion": "Residencia de 3 recámaras con piscina de 75m² y terraza con ka'anche'",
                "fotos": {
                    "interior": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450608/rwsidencia-ool-1_fx7f4y.webp",
                            "descripcion": "Interior de la residencia ÓOL",
                            "tipo": "interior"
                        }
                    ],
                    "planos": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450607/PlanoOOL_pocgbv.webp",
                            "descripcion": "Plano de la residencia ÓOL",
                            "tipo": "plano"
                        }
                    ]
                }
            },
            "ool_torre": {
                "nombre": "ÓOL WITH TOWER Residence",
                "descripcion": "Residencia de 3 recámaras con torre, piscina de 75m² y terraza con ka'anche'",
                "fotos": {
                    "interior": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450608/rwsidencia-ool-torre-1_o8egzo.webp",
                            "descripcion": "Interior de la residencia ÓOL WITH TOWER",
                            "tipo": "interior"
                        }
                    ],
                    "planos": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450607/PlanoOOLTorre_qrcdeh.webp",
                            "descripcion": "Plano de la residencia ÓOL WITH TOWER",
                            "tipo": "plano"
                        }
                    ]
                }
            },
            "utz": {
                "nombre": "UTZ Residence",
                "descripcion": "Residencia de 2 recámaras con piscina de 60m² y terraza con ka'anche'",
                "fotos": {
                    "interior": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450608/residencia-utz-1_fujveh.webp",
                            "descripcion": "Interior de la residencia UTZ",
                            "tipo": "interior"
                        }
                    ],
                    "planos": [
                        {
                            "url": "https://res.cloudinary.com/ds3cng4pl/image/upload/v1757450607/PlanoUtz_xfbifl.webp",
                            "descripcion": "Plano de la residencia UTZ",
                            "tipo": "plano"
                        }
                    ]
                }
            }
        }
    }

def buscar_foto_alternativa(fotos_db: Dict[str, Any], categoria: str, tags: List[str] = None) -> tuple:
    """
    Busca una foto alternativa basada en categoría y etiquetas.
    
    Args:
        fotos_db: Base de datos de fotos
        categoria: Categoría principal
        tags: Lista de etiquetas para buscar coincidencias
        
    Returns:
        tuple: (url_foto, caption) o (None, None) si no se encuentra
    """
    if not tags:
        tags = []
    
    # Buscar en la categoría especificada
    categoria_fotos = fotos_db.get("photos", {}).get(categoria, {})
    if not categoria_fotos:
        return None, None
    
    # Recorrer subcategorías
    for subcategoria, subcategoria_data in categoria_fotos.items():
        # Si es un diccionario simple con url
        if "url" in subcategoria_data:
            # Verificar si hay coincidencia de etiquetas
            foto_tags = subcategoria_data.get("tags", [])
            if any(tag in foto_tags for tag in tags) or not tags:
                return subcategoria_data.get("url"), subcategoria_data.get("caption")
        else:
            # Es otra estructura anidada, revisar el primer elemento
            for item_key, item_data in subcategoria_data.items():
                if "url" in item_data:
                    foto_tags = item_data.get("tags", [])
                    if any(tag in foto_tags for tag in tags) or not tags:
                        return item_data.get("url"), item_data.get("caption")
    
    # Si llegamos aquí, no se encontró coincidencia
    # Intentar devolver la primera foto disponible de la categoría
    for subcategoria, subcategoria_data in categoria_fotos.items():
        if "url" in subcategoria_data:
            return subcategoria_data.get("url"), subcategoria_data.get("caption")
        else:
            for item_key, item_data in subcategoria_data.items():
                if "url" in item_data:
                    return item_data.get("url"), item_data.get("caption")
    
    return None, None

def enviar_foto(
    categoria: str, 
    subcategoria: Optional[str] = None, 
    tipo_apartamento: Optional[str] = None, 
    area: Optional[str] = None, 
    mensaje_acompañante: Optional[str] = None,
    buscar_alternativa: bool = True
) -> Dict[str, Any]:
    """
    Envía una foto de las residencias de Chablé al usuario según los parámetros especificados.
    
    Args:
        categoria (str): Categoría principal de la foto ('interior', 'exterior', 'planos', 'amenidades')
        subcategoria (str, optional): Especificación dentro de la categoría (ej: 'sala', 'cocina', 'piscina')
        tipo_apartamento (str, optional): Tipo de residencia ('kin', 'kuxtal', 'ool', 'ool_torre', 'utz')
        area (str, optional): Área específica de la residencia (ej: 'sala', 'cocina', 'recamara_principal')
        mensaje_acompañante (str, optional): Mensaje personalizado que acompaña a la foto
        buscar_alternativa (bool): Si es True y no encuentra la foto exacta, buscará alternativas similares
        
    Returns:
        dict: Resultado de la operación con URL de la imagen y mensaje
    """
    try:
        # Clean input parameters
        categoria = clean_text(categoria)
        subcategoria = clean_text(subcategoria) if subcategoria else None
        tipo_apartamento = clean_text(tipo_apartamento) if tipo_apartamento else None
        area = clean_text(area) if area else None
        mensaje_acompañante = clean_text(mensaje_acompañante) if mensaje_acompañante else None
        
        # Cargar base de datos de fotos
        fotos_db = cargar_base_fotos()
        if not fotos_db:
            return {
                "success": False, 
                "error": "No se pudo cargar la base de datos de fotos"
            }
            
        # Diccionario de mensajes predeterminados por categoría
        mensajes_predeterminados = {
            "exterior": "¡Bienvenido a Residencias Chablé! Aquí puedes apreciar la impresionante arquitectura de nuestras residencias.",
            "interior": "Espacios diseñados pensando en tu comodidad y estilo de vida en Chablé.",
            "planos": "Plano detallado para que visualices la distribución de espacios en tu futura residencia.",
            "amenidades": "En Chablé te ofrecemos amenidades de primer nivel para una experiencia de vida excepcional."
        }
        
        # Buscar la foto según los parámetros en la nueva estructura de residencias
        url_foto = None
        caption = None
        
        # Obtener las residencias disponibles
        residencias = fotos_db.get("residencias", {})
        if not residencias:
            return {
                "success": False,
                "error": "No se encontraron residencias en la base de datos de fotos"
            }
        
        # Determinar qué residencia buscar
        residencia_target = None
        if tipo_apartamento:
            # Mapear nombres de residencias
            residencia_mapping = {
                "kin": "kin",
                "kuxtal": "kuxtal", 
                "ool": "ool",
                "ool_torre": "ool_torre",
                "ool torre": "ool_torre",
                "ool with tower": "ool_torre",
                "utz": "utz"
            }
            residencia_key = residencia_mapping.get(tipo_apartamento.lower(), tipo_apartamento.lower())
            residencia_target = residencias.get(residencia_key)
        
        # Si no se especifica residencia, buscar en todas
        if not residencia_target:
            # Buscar en todas las residencias
            for residencia_key, residencia_data in residencias.items():
                fotos_residencia = residencia_data.get("fotos", {})
                categoria_fotos = fotos_residencia.get(categoria, [])
                
                if categoria_fotos:
                    # Tomar la primera foto de la categoría
                    foto = categoria_fotos[0]
                    url_foto = foto.get("url")
                    caption = foto.get("descripcion")
                    residencia_nombre = residencia_data.get("nombre", residencia_key)
                    break
        else:
            # Buscar en la residencia específica
            fotos_residencia = residencia_target.get("fotos", {})
            categoria_fotos = fotos_residencia.get(categoria, [])
            
            if categoria_fotos:
                # Tomar la primera foto de la categoría
                foto = categoria_fotos[0]
                url_foto = foto.get("url")
                caption = foto.get("descripcion")
                residencia_nombre = residencia_target.get("nombre", tipo_apartamento)
            else:
                # Si no hay fotos en la categoría específica, buscar en otras categorías
                for cat_key, cat_fotos in fotos_residencia.items():
                    if cat_fotos:
                        foto = cat_fotos[0]
                        url_foto = foto.get("url")
                        caption = f"Te muestro una vista de {residencia_target.get('nombre', tipo_apartamento)}"
                        residencia_nombre = residencia_target.get("nombre", tipo_apartamento)
                        break
        
        # Si aún no se encuentra foto, buscar en cualquier residencia
        if not url_foto:
            for residencia_key, residencia_data in residencias.items():
                fotos_residencia = residencia_data.get("fotos", {})
                for cat_key, cat_fotos in fotos_residencia.items():
                    if cat_fotos:
                        foto = cat_fotos[0]
                        url_foto = foto.get("url")
                        caption = f"Te muestro una vista de {residencia_data.get('nombre', residencia_key)}"
                        residencia_nombre = residencia_data.get("nombre", residencia_key)
                        break
                if url_foto:
                    break
        
        if not url_foto:
            return {
                "success": False,
                "error": f"No se encontró ninguna foto para la categoría {categoria}. ¿Te gustaría ver otra área del proyecto?"
            }
        
        # Determinar el mensaje a enviar
        mensaje_categoria = mensajes_predeterminados.get(categoria, "Descubre Residencias Chablé, donde la vida se ve mejor.")
        mensaje_final = mensaje_acompañante if mensaje_acompañante else (caption if caption else mensaje_categoria)
        
        # Aquí iría la integración con el sistema de mensajería (como Twilio)
        # Por ahora solo registramos la acción
        logger.info(f"Enviando foto desde URL: {url_foto}")
        logger.info(f"Mensaje: {mensaje_final}")
        
        # Optimize image URL for WhatsApp (5MB limit) using Cloudinary transformations
        if url_foto and "cloudinary.com" in url_foto:
            # Add Cloudinary transformations to compress and optimize for WhatsApp
            # Insert transformations before the version (v1757450607)
            if "/upload/v" in url_foto:
                # Add quality reduction and format optimization
                optimized_url = url_foto.replace(
                    "/upload/v",
                    "/upload/q_auto:low,f_auto,w_1200,h_1200,c_limit/v"
                )
                logger.info(f"Optimized URL for WhatsApp: {optimized_url}")
                url_foto = optimized_url
        
        # Simulamos la respuesta exitosa
        return {
            "success": True,
            "message": f"Foto de {categoria} enviada exitosamente",
            "photo_url": url_foto,
            "text_sent": mensaje_final,
            "is_placeholder": "placeholder" in str(url_foto) if url_foto else False
        }
        
    except Exception as e:
        logger.error(f"Error al enviar la foto: {str(e)}")
        return {
            "success": False,
            "error": f"Error al enviar la foto: {str(e)}"
        }


def send_brochure(to_number: str) -> dict:
    """
    Envía el brochure digital de nuestros desarrollos.
    
    Args:
        to_number: Número de teléfono del destinatario
        
    Returns:
        dict: Resultado de la operación
    """
    try:
        # URL del brochure digital (PDF)
        brochure_url = "https://peregrino.co/residere/Brochure_AM2025.pdf"
        
        # Enviar el PDF sin mensaje
        message_sid = send_twilio_media_message(
            to_number=to_number,
            media_url=brochure_url,
            message_body="",
            media_type='pdf'
        )
        
        if message_sid:
            return {
                "success": True,
                "message": "¿Te gustaría que te explicara algo específico del brochure o tienes alguna otra pregunta?"
            }
        else:
            return {
                "success": False,
                "error": "No se pudo enviar el brochure. Por favor, intenta nuevamente."
            }
            
    except Exception as e:
        logger.error(f"Error sending brochure: {str(e)}")
        return {
            "success": False,
            "error": f"Error al enviar el brochure: {str(e)}"
        }

async def provide_contact_info(db: Session, data: dict) -> dict:
    """
    Proporciona la información de contacto y registra al cliente como lead calificado.
    
    Args:
        db: Database session
        data: Dictionary containing client information
        
    Returns:
        dict: Response with contact information and next steps
    """
    try:
        # Preparar datos para el lead calificado
        lead_data = {
            "telefono": data.get("telefono", ""),
            "nombre": data.get("nombre", "Cliente"),
            "fuente": data.get("fuente", "WhatsApp"),
            "motivo_interes": data.get("motivo", "otro"),
            "urgencia_compra": data.get("urgencia", "sin_urgencia"),
            "desea_llamada": True,
            "metodo_contacto_preferido": "WhatsApp",
            "proyecto_interes": "Yucatan"
        }
        
        # Calificar el lead
        qualify_result = await qualify_lead(db, lead_data)
        
        if not qualify_result["success"]:
            logger.error(f"Error calificando lead: {qualify_result['error']}")
        
        # Información de contacto
        contact_info = {
            "nombre": "Kevin",
            "telefono": "+57 310 221 2532",
            "correo": "asesor@residenciaschable.com",
            "cargo": "Asesor Comercial" 
        }
        
        # Preparar mensaje de respuesta
        urgency_messages = {
            "inmediata": "Te contactaremos inmediatamente.",
            "esta_semana": "Te contactaremos en las próximas 24 horas.",
            "este_mes": "Te contactaremos en los próximos días.",
            "sin_urgencia": "Te contactaremos pronto."
        }
        
        urgency_msg = urgency_messages.get(data.get("urgencia", "sin_urgencia"))
        
        response = (
            f"Con gusto te comparto los datos de contacto de nuestra asesora comercial:\n\n"
            f"👩‍💼 {contact_info['nombre']}\n"
            f"📞 {contact_info['telefono']}\n"
            f"📧 {contact_info['correo']}\n\n"
            f"{urgency_msg} "
            f"También puedes escribirle directamente por WhatsApp para una atención más rápida."
        )
        
        return {
            "success": True,
            "message": response,
            "contact_info": contact_info
        }
        
    except Exception as e:
        logger.error(f"Error providing contact info: {str(e)}")
        return {
            "success": False,
            "error": "Lo siento, hubo un error al procesar tu solicitud. Por favor, intenta nuevamente."
        }