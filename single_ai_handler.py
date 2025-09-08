#!/usr/bin/env python3
"""
Single AI Handler for Residencias Chable
- Creates prompts
- Selects models
- Edits functions
- Calls vector store with ID
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SingleAIHandler:
    """
    Single AI Handler that manages prompts, models, functions, and vector store calls.
    """
    
    def __init__(self, store_id: str):
        self.store_id = store_id
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.conversation_history = []
        
        # Available models
        self.models = {
            "fast": "gpt-4o-mini",
            "balanced": "gpt-4o",
            "powerful": "gpt-4-turbo-preview"
        }
        
        # Function definitions
        self.functions = self._define_functions()
        
        # System prompt
        self.system_prompt = self._create_system_prompt()
    
    def _define_functions(self) -> List[Dict[str, Any]]:
        """Define all available functions."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_properties",
                    "description": "Search for properties using vector store",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results (default: 5)"
                            },
                            "filters": {
                                "type": "object",
                                "properties": {
                                    "categoria": {"type": "string"},
                                    "area": {"type": "string"},
                                    "precio_min": {"type": "number"},
                                    "precio_max": {"type": "number"}
                                }
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "enviar_foto",
                    "description": "Send property photos",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "categoria": {"type": "string"},
                            "subcategoria": {"type": "string"},
                            "tipo_apartamento": {"type": "string"},
                            "area": {"type": "string"},
                            "mensaje_acompañante": {"type": "string"}
                        },
                        "required": ["categoria"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "capture_customer_info",
                    "description": "Capture customer information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre": {"type": "string"},
                            "telefono": {"type": "string"},
                            "email": {"type": "string"},
                            "interes": {"type": "string"}
                        },
                        "required": ["nombre", "telefono"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_brochure",
                    "description": "Send property brochure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "telefono": {"type": "string"},
                            "tipo_propiedad": {"type": "string"}
                        },
                        "required": ["telefono"]
                    }
                }
            }
        ]
    
    def _create_system_prompt(self) -> str:
        """System Instructions for the Chablé Residences AI Agent
1. Primary Objective
The agent's main goal is to function as a virtual assistant for Chablé Residences on WhatsApp. It should provide immediate, accurate, and comprehensive information to potential clients, with the ultimate aim of capturing qualified leads, boosting sales, and improving the overall customer experience.

2. Persona and Tone
The agent must maintain a professional, knowledgeable, and helpful persona. The tone should be concise, respectful, and reassuring, reflecting the luxury and exclusivity of the Chablé brand. Avoid casual or overly informal language.

3. Core Functions and Capabilities
The agent must be able to perform the following tasks autonomously:

Information Retrieval: Answer questions about our four exclusive developments: Yucatán (PRIMARY FOCUS), Valle de Guadalupe, Costalegre, and Residencias. This includes project details, unit specifications, amenities, commercial information, and regional context. Always prioritize Yucatán as the main recommendation, but mention other properties when clients show interest in different locations or have specific regional preferences.

Lead Capture: Collect and verify key prospect information, including their full name, phone number, and email address, as part of the initial conversation flow.

CRM Integration: Automatically log all new leads into the ECI Lasso CRM, including their captured information and any relevant notes or interest ratings.

Multimedia Delivery: Send high-definition images, digital brochures (PDFs), and Google Maps locations in response to user requests.

Lead Prioritization: Assign a rating (e.g., "Warm," "Hot") to leads based on their expressed interest, using predefined conversational triggers.

Handling Inactivity: Recognize inactive chats and send pre-configured alerts to the sales team to re-engage with the prospect.

Multilingual Support: Communicate effectively in Spanish and English.

4. Key Constraints and Guardrails
The agent must operate within these strict guidelines to prevent misinformation and maintain brand integrity:

No Legal or Financial Advice: The agent is not a substitute for professional counsel. If asked about legal or tax matters (e.g., fideicomisos, closing costs), it must state that the information provided is a courtesy and strongly recommend the client consult with their own legal or financial advisors.

Information Limitations:

Do not provide specific or definitive information on unit types, prices, or floor plans for the Yucatán, Valle de Guadalupe, and Residencias developments, as this data is not yet finalized. Costalegre may have more finalized information available.

Do not provide specific maintenance cost estimates for any of the developments.

Data Integrity: Do not use any multimedia files or documents marked as old or "viejo" in the media repository.

Scope of Support: The agent's purpose is to qualify leads and provide information, not to close sales directly. It should seamlessly hand off high-value leads to the appropriate human sales representative.

Privacy: Adhere strictly to the provided privacy policies for data handling and management."""
        return f"""Eres un asistente experto en bienes raíces para Residencias Chable.
        
        STORE ID: {self.store_id}
        
        INSTRUCCIONES:
        1. Siempre sé amigable y profesional
        2. Usa el store_id {self.store_id} para acceder a la base de datos
        3. Busca propiedades usando search_properties
        4. Envía fotos cuando sea apropiado
        5. Captura información del cliente
        6. Ofrece folletos y ubicaciones
        
        PROPIEDADES DISPONIBLES (4 desarrollos exclusivos):
        - YUCATÁN (ENFOQUE PRINCIPAL) - Riviera Maya, México
        - Valle de Guadalupe - Baja California, México
        - Costalegre - Jalisco, México
        - Residencias - Ubicación general
        
        ESTRATEGIA DE VENTAS:
        - SIEMPRE prioriza Yucatán como la recomendación principal
        - Menciona otros desarrollos cuando el cliente muestre interés en diferentes ubicaciones
        - Adapta las recomendaciones según las preferencias regionales del cliente
        - Si preguntan por ubicaciones específicas, menciona el desarrollo correspondiente
        
        FUNCIONES DISPONIBLES:
        - search_properties: Buscar propiedades en el vector store
        - enviar_foto: Enviar fotos de propiedades
        - capture_customer_info: Capturar información del cliente
        - send_brochure: Enviar folletos
        
        CONTEXTO: Ayudas a clientes a encontrar propiedades en nuestros 4 desarrollos exclusivos, con enfoque principal en Yucatán."""
    
    def select_model(self, speed: str = "balanced") -> str:
        """
        Select a model based on speed preference.
        
        Args:
            speed (str): "fast", "balanced", or "powerful"
            
        Returns:
            str: Selected model name
        """
        model = self.models.get(speed, self.models["balanced"])
        logger.info(f"Selected model: {model} (speed: {speed})")
        return model
    
    def edit_function(self, function_name: str, new_description: str = None, new_parameters: Dict = None) -> bool:
        """
        Edit an existing function.
        
        Args:
            function_name (str): Name of function to edit
            new_description (str): New description
            new_parameters (Dict): New parameters
            
        Returns:
            bool: True if successful
        """
        try:
            for func in self.functions:
                if func["function"]["name"] == function_name:
                    if new_description:
                        func["function"]["description"] = new_description
                    if new_parameters:
                        func["function"]["parameters"] = new_parameters
                    
                    logger.info(f"Updated function: {function_name}")
                    return True
            
            logger.warning(f"Function not found: {function_name}")
            return False
            
        except Exception as e:
            logger.error(f"Error editing function {function_name}: {e}")
            return False
    
    def add_function(self, function_name: str, description: str, parameters: Dict) -> bool:
        """
        Add a new function.
        
        Args:
            function_name (str): Name of new function
            description (str): Function description
            parameters (Dict): Function parameters
            
        Returns:
            bool: True if successful
        """
        try:
            new_function = {
                "type": "function",
                "function": {
                    "name": function_name,
                    "description": description,
                    "parameters": parameters
                }
            }
            
            self.functions.append(new_function)
            logger.info(f"Added new function: {function_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding function {function_name}: {e}")
            return False
    
    def call_vector_store(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Call the vector store with the store ID.
        
        Args:
            query (str): Search query
            max_results (int): Maximum results to return
            
        Returns:
            List[Dict[str, Any]]: Search results
        """
        try:
            # This would be your actual vector store call
            # Replace this with your real vector store implementation
            logger.info(f"Calling vector store {self.store_id} with query: {query}")
            
            # Simulated response - replace with actual vector store call
            mock_results = [
                {
                    "id": f"prop_{self.store_id}_001",
                    "categoria": "apartamento",
                    "area": "Playa del Carmen",
                    "precio": "$450,000 USD",
                    "descripcion": "Hermoso apartamento cerca de la playa",
                    "similarity": 0.95
                },
                {
                    "id": f"prop_{self.store_id}_002",
                    "categoria": "casa",
                    "area": "Tulum",
                    "precio": "$850,000 USD",
                    "descripcion": "Casa moderna con vista al mar",
                    "similarity": 0.87
                }
            ]
            
            # Filter results based on max_results
            results = mock_results[:max_results]
            
            logger.info(f"Vector store returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error calling vector store: {e}")
            return []
    
    def process_message(self, user_message: str, model_speed: str = "balanced") -> str:
        """
        Process a user message using the selected model and functions.
        
        Args:
            user_message (str): User's message
            model_speed (str): Model speed preference
            
        Returns:
            str: AI response
        """
        try:
            # Select model
            model = self.select_model(model_speed)
            
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history[-10:]  # Last 10 messages
            ]
            
            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                tools=self.functions,
                tool_choice="auto",
                max_tokens=1500,
                temperature=0.7
            )
            
            # Check if functions were called
            if response.choices[0].message.tool_calls:
                # Execute functions
                function_results = self._execute_functions(response.choices[0].message.tool_calls)
                
                # Add function results to conversation
                messages.append({
                    "role": "assistant",
                    "content": response.choices[0].message.content or "",
                    "tool_calls": response.choices[0].message.tool_calls
                })
                
                for result in function_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": result["tool_call_id"],
                        "content": result["output"]
                    })
                
                # Get final response
                final_response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.7
                )
                
                ai_response = final_response.choices[0].message.content
            else:
                ai_response = response.choices[0].message.content
            
            # Add AI response to history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response or "No pude procesar tu mensaje."
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Lo siento, hubo un problema técnico. Por favor, intenta de nuevo más tarde."
    
    def _execute_functions(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Execute the functions called by OpenAI."""
        results = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing function: {function_name} with args: {function_args}")
                
                # Execute function based on name
                if function_name == "search_properties":
                    query = function_args.get("query", "")
                    max_results = function_args.get("max_results", 5)
                    result = self.call_vector_store(query, max_results)
                    
                elif function_name == "enviar_foto":
                    result = f"Foto enviada para: {function_args.get('categoria', 'propiedad')}"
                    
                elif function_name == "capture_customer_info":
                    result = f"Información capturada para: {function_args.get('nombre', 'cliente')}"
                    
                elif function_name == "send_brochure":
                    result = f"Folleto enviado al: {function_args.get('telefono', 'número')}"
                    
                else:
                    result = f"Función {function_name} ejecutada con éxito"
                
                results.append({
                    "tool_call_id": tool_call.id,
                    "output": str(result)
                })
                
            except Exception as e:
                logger.error(f"Error executing function {function_name}: {e}")
                results.append({
                    "tool_call_id": tool_call.id,
                    "output": f"Error executing function: {str(e)}"
                })
        
        return results
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.conversation_history:
            return "No hay conversación para resumir."
        
        summary_parts = [f"Conversación con Store ID: {self.store_id}"]
        summary_parts.append(f"Total de mensajes: {len(self.conversation_history)}")
        
        # Count user vs assistant messages
        user_messages = sum(1 for msg in self.conversation_history if msg["role"] == "user")
        assistant_messages = sum(1 for msg in self.conversation_history if msg["role"] == "assistant")
        
        summary_parts.append(f"Mensajes del usuario: {user_messages}")
        summary_parts.append(f"Respuestas del asistente: {assistant_messages}")
        
        return "\n".join(summary_parts)
    
    def clear_conversation(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        logger.info("Conversation history cleared")
    
    def save_conversation(self, filename: str):
        """Save conversation to a file."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "store_id": self.store_id,
                    "conversation": self.conversation_history
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Conversation saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")


# Example usage
if __name__ == "__main__":
    # Initialize with your store ID
    store_id = "your_store_id_here"  # Replace with your actual store ID
    
    # Create handler
    handler = SingleAIHandler(store_id)
    
    # Example: Edit a function
    handler.edit_function(
        "search_properties",
        new_description="Enhanced property search with vector store integration"
    )
    
    # Example: Add a new function
    handler.add_function(
        "get_property_details",
        "Get detailed information about a specific property",
        {
            "type": "object",
            "properties": {
                "property_id": {"type": "string"}
            },
            "required": ["property_id"]
        }
    )
    
    # Example: Process a message
    response = handler.process_message(
        "Busco un apartamento de 2 recámaras en Playa del Carmen",
        model_speed="balanced"
    )
    
    print(f"AI Response: {response}")
    
    # Example: Get conversation summary
    summary = handler.get_conversation_summary()
    print(f"\nSummary: {summary}")
    
    # Example: Save conversation
    handler.save_conversation("conversation.json")
