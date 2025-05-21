# -*- coding: utf-8 -*-

import os
import json
import asyncio
import logging
import traceback
import time
from datetime import datetime, date
from threading import Lock
from typing import Dict, Any, Optional, List, Tuple

from openai import AsyncOpenAI, NotFoundError
import pytz
from dotenv import load_dotenv

from .conversation_manager import ConversationManager
from .db import get_db
from .routers.crm import ContactSchema
from pydantic import ValidationError

# Basic configuration
load_dotenv()
logger = logging.getLogger('eventek_assistant')


# --- Tool Definition for CRM ---
add_contact_tool = {
    "type": "function",
    "function": {
        "name": "add_crm_contact",
        "description": "Adds a new contact or lead to the CRM database. Use this ONLY when you have gathered enough information like name, and potentially email or phone, event details, etc., from the user.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The full name of the contact."},
                "phone": {"type": "string", "description": "The contact's phone number (optional)."},
                "email": {"type": "string", "description": "The contact's email address (optional)."},
                "company": {"type": "string", "description": "The company the contact works for (optional)."},
                "event_type": {"type": "string", "description": "The type of event the contact is interested in (e.g., 'Corporate Gala', 'Wedding') (optional)."},
                "event_date": {"type": "string", "description": "The estimated date of the event in YYYY-MM-DD format (optional)."},
                "attendees": {"type": "integer", "description": "The estimated number of attendees for the event (optional)."},
                "plan_interest": {"type": "string", "description": "The specific Eventek plan (e.g., 'Básico B2C', 'Profesional B2B', 'Expert') (optional)."},
                "notes": {"type": "string", "description": "Any additional notes (optional)."}
            },
            "required": ["name"]
        }
    }
}
# --- End Tool Definition ---


class FestivalConfig:
    """Configuration for Eventek Assistant"""
    SPAIN_TZ = pytz.timezone('Europe/Madrid')
    TODAY = datetime.now(SPAIN_TZ)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ASSISTANT_ID_ENV_VAR = "EVENTEK_ASSISTANT_ID"
    ASSISTANT_ID = os.getenv(ASSISTANT_ID_ENV_VAR)
    logger = logging.getLogger('eventek_assistant.config')

    @classmethod
    async def get_or_create_assistant(cls, client: AsyncOpenAI) -> str:
        """
        Gets the assistant ID from environment variable or creates/updates the assistant.
        Includes file/vector store setup and tool configuration.
        All OpenAI client calls are asynchronous.
        """
        assistant_id_to_use = None
        create_new = False
        update_existing = False

        env_assistant_id = os.getenv(cls.ASSISTANT_ID_ENV_VAR)

        if env_assistant_id and env_assistant_id.lower() != "force_new":
            cls.logger.info(f"Attempting to retrieve assistant using ID from env: {env_assistant_id}")
            try:
                assistant = await client.beta.assistants.retrieve(env_assistant_id)
                assistant_id_to_use = assistant.id
                cls.logger.info(f"Successfully retrieved existing assistant with ID: {assistant_id_to_use}")
                update_existing = True
            except NotFoundError:
                cls.logger.warning(f"Assistant ID {env_assistant_id} from env not found. Will create a new one.")
                create_new = True
            except Exception as e:
                cls.logger.error(f"Error retrieving assistant {env_assistant_id}: {e}. Will create a new one.", exc_info=True)
                create_new = True
        else:
            if env_assistant_id and env_assistant_id.lower() == "force_new":
                cls.logger.info("`force_new` detected. Creating a new assistant.")
            else:
                cls.logger.info("No valid Assistant ID in env. Creating a new assistant.")
            create_new = True

        instructions_content = f"""Eres el asistente virtual de Eventek, experto en nuestros servicios para eventos. Tu DOBLE OBJETIVO es:
        1.  **INFORMAR:** Proporcionar información precisa y útil sobre Eventek, nuestros planes (Básico B2C, Profesional B2B, Expert), servicios y beneficios, utilizando SIEMPRE la herramienta `file_search` para consultar los archivos adjuntos.
        2.  **CAPTURAR LEADS:** Identificar a usuarios interesados y recopilar proactivamente su información de contacto (nombre, email, teléfono) y detalles del evento (tipo, fecha estimada, asistentes, plan de interés) para guardarlos en nuestro CRM usando la herramienta `add_crm_contact`.

        La fecha actual es {cls.TODAY.strftime('%Y-%m-%d')}.

        ### CÓMO INTERACTUAR:
        1.  **SALUDO Y DESCUBRIMIENTO:** Saluda amablemente. Pregunta si el usuario está organizando un evento y qué tipo de evento es. Muestra interés genuino.
        2.  **INFORMACIÓN (Usando `file_search`):** A medida que el usuario pregunte o muestres los planes, usa `file_search` para obtener y presentar la información relevante de los archivos. Sé claro sobre qué plan podría ajustarse mejor según las necesidades que descubras.
        3.  **RECOPILACIÓN DE DATOS (¡IMPORTANTE!):**
            *   Mientras conversas sobre los planes y servicios, busca oportunidades para preguntar por los detalles del lead. Hazlo de forma natural.
            *   Ejemplos: "Para poder darte detalles más ajustados, ¿podrías decirme tu nombre y quizás un email o teléfono donde podamos enviarte una propuesta?"
            *   Intenta obtener al menos el **nombre** y preferiblemente **email o teléfono**.
        4.  **GUARDAR EN CRM (Usando `add_crm_contact`):**
            *   **UNA VEZ** que tengas al menos el **nombre**, utiliza la herramienta `add_crm_contact`.
            *   Confirma con el usuario antes si no estás seguro.
            *   **NO uses `add_crm_contact` si no tienes al menos el nombre.**
        5.  **CIERRE:** Resume lo discutido. Si guardaste el contacto, informa al usuario.

        ### HERRAMIENTAS DISPONIBLES:
        - **`file_search`**: OBLIGATORIO para buscar información sobre Eventek. NO inventes información.
        - **`add_crm_contact`**: Úsala SÓLO DESPUÉS de haber recopilado información del lead (mínimo el nombre).

        ### RESTRICCIONES Y ESTILO:
        - Profesional pero cercano. Responde en el idioma del usuario.
        - NO inventes información. Si no encuentras algo, dilo.
        - NO almacenes información personal fuera del uso de `add_crm_contact`.
        ¡Tu objetivo es ser útil y ayudar a Eventek a conseguir nuevos clientes potenciales!
        """

        tools_list = [
            {"type": "file_search"},
            add_contact_tool
        ]

        if create_new:
            cls.logger.info("Creating new assistant 'Asistente Eventek'...")
            assistant = await client.beta.assistants.create(
                name="Asistente Eventek",
                instructions=instructions_content,
                model="gpt-4-turbo",
                tools=tools_list
            )
            assistant_id_to_use = assistant.id
            cls.logger.info(f"Created new assistant with ID: {assistant_id_to_use}")

            try:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = os.path.join(base_dir, "course_info.json")

                if not os.path.exists(file_path):
                    cls.logger.error(f"Knowledge file 'course_info.json' not found at: {file_path}")
                else:
                    cls.logger.info(f"Uploading knowledge file: {file_path}")
                    with open(file_path, "rb") as f:
                        uploaded_file = await client.files.create(file=f, purpose='assistants')
                    cls.logger.info(f"File uploaded with ID: {uploaded_file.id}")

                    vector_store_name = f"Eventek Knowledge Base - {cls.TODAY.strftime('%Y%m%d%H%M%S')}"
                    cls.logger.info(f"Creating vector store: {vector_store_name}")
                    vector_store = await client.vector_stores.create(name=vector_store_name, file_ids=[uploaded_file.id])
                    cls.logger.info(f"Vector store created with ID: {vector_store.id} and file {uploaded_file.id} added.")

                    cls.logger.info(f"Associating vector store {vector_store.id} with assistant {assistant_id_to_use}")
                    await client.beta.assistants.update(
                        assistant_id=assistant_id_to_use,
                        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
                    )
                    cls.logger.info(f"Assistant {assistant_id_to_use} updated with vector store.")
            except FileNotFoundError as fnf_error:
                cls.logger.error(f"Knowledge file error: {fnf_error}. Assistant may lack some file search capabilities.")
            except Exception as file_error:
                cls.logger.error(f"Error during file/vector store setup for new assistant {assistant_id_to_use}: {file_error}", exc_info=True)

            cls.logger.warning(f"IMPORTANT: A new assistant was created (ID: {assistant_id_to_use}). "
                               f"Update '{cls.ASSISTANT_ID_ENV_VAR}' to this ID to reuse it.")

        elif update_existing and assistant_id_to_use:
            cls.logger.info(f"Ensuring existing assistant {assistant_id_to_use} has latest instructions and tools...")
            current_assistant = await client.beta.assistants.retrieve(assistant_id_to_use)
            current_tool_resources = current_assistant.tool_resources or {}

            await client.beta.assistants.update(
                assistant_id=assistant_id_to_use,
                instructions=instructions_content,
                tools=tools_list,
                tool_resources=current_tool_resources
            )
            cls.logger.info(f"Assistant {assistant_id_to_use} updated with latest settings.")

        if not assistant_id_to_use:
            cls.logger.critical("Failed to obtain or create an assistant ID.")
            raise ValueError("Could not determine Assistant ID.")
        
        cls.ASSISTANT_ID = assistant_id_to_use
        return assistant_id_to_use


class CourseAssistant:
    _instance = None
    _lock = Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.logger = logging.getLogger("eventek_assistant.core")
            self.logger.info("CourseAssistant __init__ started.")

            self.settings = FestivalConfig()

            if not self.settings.OPENAI_API_KEY:
                self.logger.critical("OPENAI_API_KEY not found.")
                raise ValueError("OPENAI_API_KEY must be set.")

            try:
                self.client = AsyncOpenAI(api_key=self.settings.OPENAI_API_KEY)
                self.logger.info("AsyncOpenAI client initialized.")
            except Exception as e:
                self.logger.error(f"Failed to initialize AsyncOpenAI client: {e}", exc_info=True)
                raise

            self.assistant_id = self.settings.ASSISTANT_ID
            if not self.assistant_id:
                self.logger.critical("EVENTEK_ASSISTANT_ID is missing after setup!")
                raise ValueError("EVENTEK_ASSISTANT_ID must be set by setup process.")
            self.logger.info(f"Using Assistant ID: {self.assistant_id}")

            self.conversation_manager = ConversationManager()
            self.logger.info("ConversationManager initialized.")
            self.initialized = True
            self.logger.info(f"CourseAssistant __init__ completed for ID: {self.assistant_id}")


    async def _execute_add_crm_contact(self, arguments: Dict[str, Any]) -> str:
        """Executes the add_crm_contact function and returns the result as a JSON string."""
        self.logger.info(f"Executing tool 'add_crm_contact' with arguments: {arguments}")
        db = None
        try:
            db = await get_db()
            contact_data = {
                "name": arguments.get("name"),
                "phone": arguments.get("phone"),
                "email": arguments.get("email"),
                "company": arguments.get("company"),
                "event_type": arguments.get("event_type"),
                "plan_interest": arguments.get("plan_interest"),
                "notes": arguments.get("notes"),
                "added_on": datetime.now(FestivalConfig.SPAIN_TZ)
            }
            attendees_str = arguments.get("attendees")
            contact_data["attendees"] = int(attendees_str) if attendees_str is not None and str(attendees_str).isdigit() else None
            
            event_date_str = arguments.get("event_date")
            contact_data["event_date"] = None
            if event_date_str:
                try:
                    parsed_date = date.fromisoformat(event_date_str)
                    contact_data["event_date"] = datetime.combine(parsed_date, datetime.min.time()).replace(tzinfo=FestivalConfig.SPAIN_TZ)
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid date format '{event_date_str}' for event_date. Setting to None.")
            
            validated_contact = ContactSchema(**contact_data)
            insert_data = validated_contact.model_dump(by_alias=True, exclude={'id'})
            insert_result = await db.contacts.insert_one(insert_data)

            if insert_result.inserted_id:
                self.logger.info(f"Contact '{validated_contact.name}' inserted with ID: {insert_result.inserted_id}")
                return json.dumps({
                    "status": "success",
                    "message": f"Contact '{validated_contact.name}' added successfully.",
                    "contact_id": str(insert_result.inserted_id)
                })
            else:
                self.logger.error("Contact insertion failed (no inserted_id).")
                return json.dumps({"status": "error", "message": "Failed to insert contact."})
        except ValidationError as e:
            error_details = e.errors()[0]
            msg = f"Validation failed: {error_details['msg']} for field '{error_details['loc'][0]}'."
            self.logger.error(f"Contact validation failed for tool: {msg} - Data: {arguments}")
            return json.dumps({"status": "error", "message": msg})
        except Exception as e:
            self.logger.error(f"Error executing add_crm_contact tool: {e}", exc_info=True)
            return json.dumps({"status": "error", "message": f"Internal error: {str(e)}"})


    async def _wait_for_run_completion_and_handle_actions(self, thread_id: str, run_id: str, timeout_seconds: int = 180) -> str:
        """Polls run status, handles required actions (tool calls), and returns final status."""
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            try:
                run = await self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
                self.logger.debug(f"Polling run {run_id} status: {run.status}")

                if run.status == "completed":
                    return "completed"
                elif run.status in ["failed", "cancelled", "expired"]:
                    self.logger.error(f"Run {run_id} ended with terminal status {run.status}. Last error: {run.last_error}")
                    return run.status
                elif run.status == "requires_action":
                    self.logger.info(f"Run {run.id} requires action: {run.required_action.type}")
                    if run.required_action.type == "submit_tool_outputs":
                        tool_outputs = []
                        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                            function_name = tool_call.function.name
                            arguments_str = tool_call.function.arguments
                            self.logger.info(f"Tool call requested: {function_name}({arguments_str}) ID: {tool_call.id}")
                            try:
                                arguments = json.loads(arguments_str)
                            except json.JSONDecodeError:
                                self.logger.error(f"Failed to parse JSON args for tool {tool_call.id}: {arguments_str}")
                                output = json.dumps({"status": "error", "message": "Invalid JSON arguments."})
                                tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
                                continue
                            
                            if function_name == "add_crm_contact":
                                output = await self._execute_add_crm_contact(arguments)
                            else:
                                self.logger.warning(f"Unknown tool function requested: {function_name}")
                                output = json.dumps({"status": "error", "message": f"Unknown function '{function_name}'."})
                            tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
                        
                        if tool_outputs:
                            self.logger.info(f"Submitting tool outputs for run {run.id}: {tool_outputs}")
                            try:
                                await self.client.beta.threads.runs.submit_tool_outputs(
                                    thread_id=thread_id, run_id=run.id, tool_outputs=tool_outputs
                                )
                            except Exception as submit_err:
                                self.logger.error(f"Error submitting tool outputs for run {run.id}: {submit_err}", exc_info=True)
                                return "error_submitting_tools"
                        else:
                            self.logger.warning(f"Run {run.id} required tool outputs, but no tools were processed.")
                            return "error_no_tools_processed"
                    else:
                        self.logger.error(f"Run {run.id} requires unhandled action: {run.required_action.type}")
                        return "error_unhandled_action"
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"Error during run polling/action handling for {run_id}: {e}", exc_info=True)
                return "error_polling"
        self.logger.error(f"Run {run_id} timed out after {timeout_seconds} seconds.")
        return "timeout"

    async def process_message(self, user_id: str, message: str) -> Optional[str]:
        try:
            self.logger.info(f"Processing message from {user_id}: '{message[:100]}...'")
            thread_id = self.conversation_manager.get_thread_id(user_id)
            if not thread_id:
                thread = await self.client.beta.threads.create()
                thread_id = thread.id
                self.conversation_manager.add_thread(user_id, thread_id)
                self.logger.info(f"Created new thread {thread_id} for user {user_id}")

            await self.client.beta.threads.messages.create(
                thread_id=thread_id, role="user", content=message
            )
            self.logger.info(f"User message added to thread {thread_id}")

            run = await self.client.beta.threads.runs.create(
                thread_id=thread_id, assistant_id=self.assistant_id,
            )
            self.logger.info(f"Run {run.id} created for thread {thread_id}")

            run_status = await self._wait_for_run_completion_and_handle_actions(thread_id, run.id)
            self.logger.info(f"Run {run.id} finished with status: {run_status}")

            if run_status == 'completed':
                messages_page = await self.client.beta.threads.messages.list(
                    thread_id=thread_id, order="desc", limit=5
                )
                assistant_response_text = ""
                for msg in messages_page.data:
                    if msg.role == "assistant":
                        for content_block in msg.content:
                            if content_block.type == "text":
                                assistant_response_text += content_block.text.value + "\n"
                        if assistant_response_text:
                            break 
                
                if not assistant_response_text:
                    self.logger.warning(f"Run {run.id} completed but no final assistant text response found.")
                    return "Procesamiento completado, pero no encontré una respuesta final."
                return assistant_response_text.strip()
            else:
                final_run_state = await self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
                error_info = f"Status: {final_run_state.status}."
                if final_run_state.last_error:
                    error_info += f" Error: {final_run_state.last_error.code} - {final_run_state.last_error.message}"
                self.logger.error(f"Run {run.id} did not complete successfully. {error_info}")
                return f"Lo siento, ha ocurrido un problema ({error_info}). Por favor, inténtalo de nuevo."

        except Exception as e:
            self.logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            return "Lo siento, ha ocurrido un error general. ¿Podrías reformular tu pregunta?"


async def initialize_assistant() -> CourseAssistant:
    """Initializes the assistant instance, including async assistant creation/retrieval."""
    logger.info("Running initialize_assistant function...")
    try:
        api_key = FestivalConfig.OPENAI_API_KEY
        if not api_key:
             raise ValueError("OPENAI_API_KEY is required for initialize_assistant.")
        
        async_client_for_setup = AsyncOpenAI(api_key=api_key)
        logger.info("AsyncOpenAI client for setup initialized.")

        await FestivalConfig.get_or_create_assistant(async_client_for_setup)
        logger.info(f"Assistant setup completed. Using Assistant ID: {FestivalConfig.ASSISTANT_ID}")

        instance = CourseAssistant()
        logger.info("CourseAssistant instance created and initialized.")
        return instance
    except Exception as e:
        logger.error(f"Error during initialize_assistant: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    async def main_test():
        try:
            logger.info("Inicializando asistente Eventek para prueba...")
            course_assistant_instance = await initialize_assistant()
            logger.info("¡Hola! Soy tu asistente de Eventek. ¿En qué puedo ayudarte?")
            logger.info("(Escribe 'salir' para terminar)")
            test_user_id = "test_user_cli_123"

            while True:
                user_input = input("\nTú: ")
                if user_input.lower() == "salir":
                    logger.info("\n¡Hasta luego!")
                    break

                response = await course_assistant_instance.process_message(test_user_id, user_input)
                print(f"\nAsistente: {response}")
        except ValueError as ve:
            logger.critical(f"Configuration error: {ve}")
        except Exception as e:
            logger.error(f"Error en la prueba principal: {str(e)}", exc_info=True)

    asyncio.run(main_test())