from fastapi import APIRouter, Request, Depends, HTTPException, Response, Query, status
import logging
import json
import traceback
import httpx
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Assuming db, config, assistant_logic, services are in the parent directory 'src'
from ..db import get_db # May not be needed if webhook doesn't directly use DB
from ..config import settings
from ..assistant_logic import CourseAssistant # Assuming CourseAssistant is needed here
from ..services.whatsapp_service import WhatsAppService # Import the service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhook", # Add a prefix for all routes in this router
    tags=["WhatsApp"], # Optional tag for API docs
)

# --- Pydantic Models for WhatsApp ---
# (Keep only the models specifically used by the webhook endpoints)

class WebhookVerification(BaseModel):
    hub_mode: str = Field(..., alias="hub.mode")
    hub_challenge: int = Field(..., alias="hub.challenge")
    hub_verify_token: str = Field(..., alias="hub.verify_token")

class WhatsAppChangeValue(BaseModel):
    messaging_product: str
    metadata: Dict[str, Any]
    contacts: Optional[List[Dict[str, Any]]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    statuses: Optional[List[Dict[str, Any]]] = None # Handle status updates

class WhatsAppEntry(BaseModel):
    id: str
    changes: List[WhatsAppChangeValue]

class WhatsAppWebhookPayload(BaseModel):
    object: str
    entry: List[WhatsAppEntry]

# --- WhatsApp Helper Functions ---
# (Moved from app.py - consider moving to whatsapp_service.py later if preferred)
async def send_whatsapp_message(recipient_id: str, message: str):
    """Sends a text message via the WhatsApp Business API."""
    whatsapp_service = WhatsAppService()
    try:
        result = await whatsapp_service.send_message(recipient_id, message)
        logger.info(f"Message sent successfully to {recipient_id}: {result}")
        return result
    except Exception as e:
        # Error logging is handled within WhatsAppService, re-raise or handle as needed
        logger.error(f"Failed to send message via router function wrapper: {e}")
        # Depending on desired behavior, you might raise HTTPException here
        raise

# --- WhatsApp Webhook Endpoints ---

@router.get("", summary="Verify WhatsApp Webhook")
async def verify_webhook(
    request: Request,
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: int = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    """Handles WhatsApp webhook verification challenge."""
    logger.debug(f"Webhook verification request received: mode={hub_mode}, token={hub_verify_token}, challenge={hub_challenge}")
    # Use Pydantic for validation (optional but good practice)
    try:
        verification_data = WebhookVerification(
            **{"hub.mode": hub_mode, "hub.challenge": hub_challenge, "hub.verify_token": hub_verify_token}
        )
    except Exception as e:
         logger.error(f"Webhook verification validation failed: {e}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification parameters")

    if verification_data.hub_mode == "subscribe" and verification_data.hub_verify_token == settings.WEBHOOK_VERIFY_TOKEN:
        logger.info("Webhook verified successfully!")
        return Response(content=str(verification_data.hub_challenge), media_type="text/plain")
    else:
        logger.warning("Webhook verification failed: Mode or token mismatch.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Webhook verification failed")


@router.post("", summary="Handle WhatsApp Messages")
async def handle_webhook(request: Request, assistant: CourseAssistant = Depends()): # Inject assistant
    """Receives and processes incoming messages from WhatsApp."""
    payload_bytes = await request.body()
    payload_str = payload_bytes.decode('utf-8')
    logger.debug(f"Raw WhatsApp payload received: {payload_str}")

    try:
        data = json.loads(payload_str)
        # Validate payload structure (optional but recommended)
        # payload = WhatsAppWebhookPayload.model_validate(data)

        # Process messages
        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        for message_data in value.get("messages", []):
                            if message_data.get("type") == "text":
                                sender_id = message_data.get("from")
                                text = message_data.get("text", {}).get("body")
                                timestamp = message_data.get("timestamp")
                                message_id = message_data.get("id")

                                if sender_id and text:
                                    logger.info(f"Received message from {sender_id}: '{text}'")
                                    # Process message with assistant
                                    try:
                                        response_text = await assistant.process_message(sender_id, text)
                                        if response_text:
                                            await send_whatsapp_message(sender_id, response_text)
                                        else:
                                            logger.info(f"No response generated for message from {sender_id}")
                                    except Exception as e:
                                        logger.error(f"Error processing message or sending reply to {sender_id}: {e}")
                                        logger.error(traceback.format_exc())
                                        # Optionally send an error message back to the user
                                        # await send_whatsapp_message(sender_id, "Sorry, I encountered an error. Please try again later.")
                            # Handle other message types (image, audio, location, etc.) if needed
                            elif message_data.get("type") == "interactive":
                                # Handle button clicks, list replies etc.
                                logger.info(f"Received interactive message: {message_data}")
                                # Add specific logic here if needed
                            # Add more elif blocks for other types
                    elif "statuses" in value:
                         # Handle message status updates (sent, delivered, read)
                         for status_data in value.get("statuses", []):
                             logger.debug(f"Received status update: {status_data}")
                             # Add logic here if you need to track message delivery/read status

        return Response(status_code=status.HTTP_200_OK)

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON payload")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error processing webhook payload: {e}")
        logger.error(traceback.format_exc())
        # Return 200 OK even on errors to prevent WhatsApp from resending excessively
        return Response(status_code=status.HTTP_200_OK)
