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
from app.execute_functions import execute_function
from app.prompt_builder import build_system_prompt

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
                    "description": "Send photos of Chablé luxury residences (KIN, KUXTAL, ÓOL, ÓOL TORRE, UTZ). Use 'interior' or 'planos' as categoria. Use 'kin', 'kuxtal', 'ool', 'ool_torre', or 'utz' as tipo_residencia.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "categoria": {"type": "string", "description": "Photo category: 'interior' or 'planos'"},
                            "subcategoria": {"type": "string", "description": "Optional subcategory"},
                            "tipo_residencia": {"type": "string", "description": "Luxury residence type: 'kin', 'kuxtal', 'ool', 'ool_torre', or 'utz'"},
                            "area": {"type": "string", "description": "Specific area of the residence"},
                            "mensaje_acompañante": {"type": "string", "description": "Custom message to accompany the photo"}
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
                    "description": "Send property brochure via WhatsApp",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tipo_propiedad": {"type": "string", "description": "Type of property brochure to send"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "send_yucatan_location",
                    "description": "Send the location of Chablé Yucatan via WhatsApp. Use ONLY when users explicitly ask about location, address, or how to get to the project. Do not proactively offer location unless specifically requested.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "qualify_lead",
                    "description": "Capture and qualify a lead when user shows explicit interest in visiting, buying, or being contacted. Use when user requests visits, calls, or shows buying intent.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre": {"type": "string", "description": "Customer name"},
                            "telefono": {"type": "string", "description": "Phone number"},
                            "email": {"type": "string", "description": "Email address"},
                            "motivo": {"type": "string", "description": "Reason for interest: 'visita', 'informacion', 'llamada', 'compra'"},
                            "urgencia": {"type": "string", "description": "Urgency level: 'inmediata', 'esta_semana', 'sin_urgencia'"},
                            "ciudad_interes": {"type": "string", "description": "City of interest"},
                            "tipo_propiedad": {"type": "string", "description": "Property type preference"},
                            "presupuesto": {"type": "string", "description": "Budget range"}
                        },
                        "required": ["nombre", "telefono", "motivo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_contact_info",
                    "description": "Provide official contact information for Chablé Residences ONLY when explicitly requested by the user. Do not offer this information proactively.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tipo_contacto": {"type": "string", "description": "Type of contact requested: 'email', 'telefono', 'sitio_web', 'todos'"}
                        },
                        "required": ["tipo_contacto"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "show_property_options",
                    "description": "Show property selection options to customer with interactive buttons",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "select_property",
                    "description": "Handle property selection and route to correct CRM based on customer choice",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selected_property": {
                                "type": "string", 
                                "description": "Selected property key: 'yucatan', 'valle_de_guadalupe', 'costalegre', or 'mar_de_cortes'"
                            },
                            "lead_data": {
                                "type": "object",
                                "description": "Lead information including name, phone, email, etc."
                            }
                        },
                        "required": ["selected_property", "lead_data"]
                    }
                }
            }
        ]
    
    def _create_system_prompt(self) -> str:
        """Build the system prompt from the structured KB and guardrails."""
        return build_system_prompt(self.store_id)
    
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
                    "categoria": "residencia",
                    "area": "Playa del Carmen",
                    "precio": "$450,000 USD",
                    "descripcion": "Hermosa residencia de lujo cerca de la playa",
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
    
    def process_message(self, user_message: str, model_speed: str = "balanced", db=None, sender_info=None) -> str:
        """
        Process a user message using the selected model and functions.
        
        Args:
            user_message (str): User's message
            model_speed (str): Model speed preference
            
        Returns:
            str: AI response
        """
        try:
            logger.info(f"🤖 AI processing message: '{user_message[:100]}...' (speed: {model_speed})")
            
            # Select model
            model = self.select_model(model_speed)
            logger.info(f"🤖 Selected model: {model}")
            
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                *self.conversation_history[-10:]  # Last 10 messages
            ]
            
            logger.info(f"🤖 Prepared {len(messages)} messages for AI processing")
            
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
                logger.info(f"🔧 AI requested {len(response.choices[0].message.tool_calls)} function calls")
                
                # Execute functions
                function_results = self._execute_functions(response.choices[0].message.tool_calls, db, sender_info)
                logger.info(f"🔧 Executed {len(function_results)} functions successfully")
                
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
                logger.info("🤖 Generating final response after function execution")
                final_response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.7
                )
                
                ai_response = final_response.choices[0].message.content
                logger.info(f"🤖 Final response generated: '{ai_response[:100]}...'")
            else:
                ai_response = response.choices[0].message.content
                logger.info(f"🤖 Direct response generated: '{ai_response[:100]}...'")
            
            # Add AI response to history
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            
            return ai_response or "No pude procesar tu mensaje."
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "Lo siento, hubo un problema técnico. Por favor, intenta de nuevo más tarde."
    
    def _execute_functions(self, tool_calls: List[Any], db=None, sender_info=None) -> List[Dict[str, Any]]:
        """Execute the functions called by OpenAI."""
        results = []
        
        for i, tool_call in enumerate(tool_calls):
            try:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"🔧 [{i+1}/{len(tool_calls)}] Executing: {function_name}")
                logger.debug(f"🔧 Function args: {function_args}")
                
                # Execute function based on name
                if function_name == "search_properties":
                    query = function_args.get("query", "")
                    max_results = function_args.get("max_results", 5)
                    logger.info(f"🔍 Searching properties: '{query}' (max: {max_results})")
                    result = self.call_vector_store(query, max_results)
                    logger.info(f"🔍 Found {len(result)} properties")
                    
                elif function_name in ["enviar_foto", "capture_customer_info", "send_brochure", "send_yucatan_location", "qualify_lead", "get_contact_info", "show_property_options", "select_property"]:
                    # Call the real function from execute_functions.py
                    if db and sender_info:
                        try:
                            logger.info(f"🔧 Executing {function_name} with database context")
                            # Prepare the tool_call data
                            tool_call_data = {
                                "function_name": function_name,
                                "arguments": json.dumps(function_args)
                            }
                            
                            # Execute function synchronously using asyncio.run
                            import asyncio
                            result = asyncio.run(execute_function(tool_call_data, db, sender_info))
                            logger.info(f"🔧 Function {function_name} completed successfully")
                                
                        except Exception as e:
                            logger.error(f"🔧 Error executing function {function_name}: {e}")
                            result = f"Error ejecutando función: {str(e)}"
                    else:
                        logger.warning(f"🔧 Function {function_name} requires database context")
                        result = f"Función {function_name} requiere contexto de base de datos"
                    
                else:
                    logger.info(f"🔧 Unknown function: {function_name}")
                    result = f"Función {function_name} ejecutada con éxito"
                
                results.append({
                    "tool_call_id": tool_call.id,
                    "output": str(result)
                })
                logger.info(f"🔧 Function {function_name} result: {str(result)[:100]}...")
                
            except Exception as e:
                logger.error(f"🔧 Error executing function {function_name}: {e}")
                results.append({
                    "tool_call_id": tool_call.id,
                    "output": f"Error executing function: {str(e)}"
                })
        
        logger.info(f"🔧 Completed {len(results)} function executions")
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
        "Busco una residencia de lujo de 2 recámaras en Playa del Carmen",
        model_speed="balanced"
    )
    
    print(f"AI Response: {response}")
    
    # Example: Get conversation summary
    summary = handler.get_conversation_summary()
    print(f"\nSummary: {summary}")
    
    # Example: Save conversation
    handler.save_conversation("conversation.json")
