# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import json
import sys
import os
import logging
import traceback
import httpx
import time
from .config import settings
from .assistant_logic import CourseAssistant, initialize_assistant
from .services.whatsapp_service import WhatsAppService

# Setup logging with higher verbosity
logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,  # Change to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('whatsapp_bot')

app = FastAPI()

# Middleware mejorado para logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    method = request.method
    
    # Log all incoming webhook requests with high visibility
    if "/webhook" in path:
        logger.warning(f"⚠️ WEBHOOK REQUEST: {method} {path}")
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8', errors='ignore')
        
        try:
            # Store webhook data persistently
            timestamp = datetime.now().isoformat()
            with open(f"webhook_log_{timestamp}.json", "w") as f:
                f.write(body_text)
                
            logger.warning(f"💾 WEBHOOK CONTENT SAVED TO: webhook_log_{timestamp}.json")
            logger.warning(f"📩 WEBHOOK CONTENT: {body_text[:500]}...")
        except Exception as e:
            logger.error(f"Error logging webhook: {str(e)}")
            
        # Create a new request object since we've consumed the body
        request = Request(request.scope, request.receive)
    
    response = await call_next(request)
    return response

# Store assistant instances in app state
app.state.course_assistant = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store webhook history - limit to last 50 messages to avoid memory issues
webhook_history = []
MAX_WEBHOOK_HISTORY = 50

async def send_whatsapp_message(recipient_id: str, message: str):
    """Send message using WhatsApp Cloud API"""
    if not settings.PHONE_NUMBER_ID:
        raise ValueError("PHONE_NUMBER_ID is not set")
    
    url = f"https://graph.facebook.com/v17.0/{settings.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # Make sure the message is properly encoded
    if isinstance(message, bytes):
        message = message.decode('utf-8')
    
    # Remove any problematic characters that might cause encoding issues
    message = message.encode('utf-8', errors='ignore').decode('utf-8')
    
    # Log truncated message for debugging
    logger.info(f"Preparing to send WhatsApp message to {recipient_id}: {message[:100]}...")
    
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message}
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url, 
                headers=headers, 
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            logger.info(f"WhatsApp message sent successfully, status code: {response.status_code}")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error sending WhatsApp message: {e.response.status_code} - {e.response.text}")
        logger.error(traceback.format_exc())
        raise
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {str(e)}")
        logger.error(traceback.format_exc())
        raise

async def send_message(self, recipient_id: str, message: str):
    """Send message using a generic messaging API"""
    url = f"https://graph.facebook.com/v17.0/{settings.PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "text",
        "text": {"body": message}
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            logger.info(f"Message sent successfully to {recipient_id}: {result}")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error sending message: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "assistant_initialized": app.state.course_assistant is not None,
        "environment": "production" if os.getenv("ENV") == "production" else "development"
    }

@app.get("/webhook")
async def verify_webhook(request: Request):
    """WhatsApp webhook verification endpoint"""
    try:
        # Get query parameters with explicit error handling
        params = request.query_params
        mode = params.get('hub.mode', '')
        token = params.get('hub.verify_token', '')
        challenge = params.get('hub.challenge', '')
        
        logger.info(f"Webhook verification: mode={mode}, token={token}, challenge={challenge}")
        
        if mode == 'subscribe' and token == settings.WEBHOOK_VERIFY_TOKEN:
            logger.info("✅ Webhook verified successfully")
            return Response(content=challenge, media_type="text/plain")
        else:
            logger.error(f"❌ Webhook verification failed: Invalid token or mode")
            raise HTTPException(status_code=403, detail="Verification failed")
            
    except Exception as e:
        logger.error(f"❌ Webhook error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

whatsapp_service = WhatsAppService()

@app.post("/webhook")
async def webhook(request: Request):
    try:
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8', errors='replace')
        
        try:
            body = json.loads(body_text)
            
            # Extract message using Meta's structure (match their JavaScript example)
            messages = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
            
            if messages:
                message = messages[0]
                if message.get("type") == "text":
                    # Extract the text and sender
                    text = message.get("text", {}).get("body", "")
                    user_id = message.get("from")
                    message_id = message.get("id")
                    
                    # Get business phone ID from metadata (exactly as Meta does)
                    business_phone_id = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("metadata", {}).get("phone_number_id")
                    
                    # Process with assistant
                    logger.info(f"Processing message from {user_id}: {text}")
                    if app.state.course_assistant is None:
                        logger.info("Initializing course assistant for incoming message")
                        app.state.course_assistant = CourseAssistant()
                    
                    # Get response from assistant
                    assistant_response = await app.state.course_assistant.handle_message(user_id, text)
                    logger.info(f"Assistant response: {json.dumps(assistant_response, ensure_ascii=False)}")
                    
                    # Send response back to user
                    if assistant_response and assistant_response.get("type") == "text":
                        response_text = assistant_response["content"]
                        await whatsapp_service.send_message(user_id, response_text)
                        logger.info(f"Response sent to {user_id}")
                    else:
                        logger.error(f"Invalid assistant response: {assistant_response}")
                    
                    # Mark message as read (like Meta does)
                    await whatsapp_service.mark_message_as_read(message_id)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse webhook body as JSON: {body_text[:200]}...")
            return {"status": "error", "message": "Invalid JSON body"}
        
    except Exception as e:
        logger.error(f"Unhandled error in webhook: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.get("/debug/assistant")
async def debug_assistant():
    """Endpoint to check assistant status and troubleshoot issues"""
    try:
        # Make sure the logger is working
        logger.info("Debug assistant endpoint called")
        
        status = {
            "course_assistant_initialized": app.state.course_assistant is not None,
            "env_vars": {
                "PHONE_NUMBER_ID": settings.PHONE_NUMBER_ID is not None and len(settings.PHONE_NUMBER_ID) > 5,
                "WHATSAPP_TOKEN": settings.WHATSAPP_TOKEN is not None and len(settings.WHATSAPP_TOKEN) > 10,
                "WEBHOOK_VERIFY_TOKEN": settings.WEBHOOK_VERIFY_TOKEN is not None,
                "OPENAI_API_KEY": settings.OPENAI_API_KEY is not None and len(settings.OPENAI_API_KEY) > 10,
            },
            "file_paths": {
                "current_dir": os.path.abspath(os.curdir),
                "file_location": __file__
            }
        }
        
        # Test assistant if initialized
        if app.state.course_assistant is None:
            # Initialize assistant for testing
            logger.info("Initializing course assistant for testing")
            try:
                app.state.course_assistant = CourseAssistant()
                status["assistant_initialized_now"] = True
                logger.info("Course assistant initialized successfully in debug endpoint")
            except Exception as e:
                logger.error(f"Failed to initialize course assistant in debug endpoint: {str(e)}")
                status["initialization_error"] = str(e)
                status["initialization_traceback"] = traceback.format_exc()
        else:
            logger.info("Using existing course assistant")
        
        # Test the assistant
        try:
            logger.info("Testing assistant with a sample message")
            test_response = await app.state.course_assistant.handle_message(
                "debug_user", "Este es un mensaje de prueba para el asistente."
            )
            status["test_response"] = test_response
            logger.info(f"Test response received: {json.dumps(test_response, indent=2)}")
        except Exception as e:
            logger.error(f"Error testing assistant: {str(e)}")
            status["test_error"] = str(e)
            status["test_traceback"] = traceback.format_exc()
        
        return status
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

@app.get("/debug/last-messages")
async def get_last_messages():
    """Returns the last webhook messages received"""
    return {"messages": webhook_history}

@app.get("/debug/verify-phone/{phone_number}")
async def verify_phone(phone_number: str):
    """Verify if a phone number is valid and reachable"""
    try:
        url = f"https://graph.facebook.com/v17.0/{settings.PHONE_NUMBER_ID}"
        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                phone_data = response.json()
                
                # Try to send a test message
                send_url = f"https://graph.facebook.com/v17.0/{settings.PHONE_NUMBER_ID}/messages"
                send_data = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": phone_number,
                    "type": "text",
                    "text": {"body": "Este es un mensaje de prueba para verificar la conexión. Si lo recibes, significa que tu número está configurado correctamente."}
                }
                
                send_response = await client.post(
                    send_url, 
                    headers={**headers, "Content-Type": "application/json"}, 
                    json=send_data
                )
                
                if send_response.status_code == 200:
                    send_result = send_response.json()
                    return {
                        "status": "success",
                        "phone_data": phone_data,
                        "message_sent": True,
                        "message_id": send_result.get("messages", [{}])[0].get("id", "Unknown")
                    }
                else:
                    return {
                        "status": "error",
                        "phone_data": phone_data,
                        "message_sent": False,
                        "error": send_response.text
                    }
            else:
                return {
                    "status": "error",
                    "error": response.text
                }
    except Exception as e:
        logger.error(f"Error verifying phone: {str(e)}")
        return {"status": "error", "message": str(e)}

# Add this function to handle JSON encoding with Unicode characters
def json_serialize(obj):
    """Custom JSON serializer that properly handles Unicode characters"""
    return json.dumps(obj, ensure_ascii=False)

@app.post("/debug/simulate-whatsapp")
async def simulate_whatsapp_message(request: Request):
    """Test endpoint to simulate WhatsApp messages without going through the WhatsApp API"""
    try:
        # Parse request body with explicit encoding
        body_bytes = await request.body()
        body_text = body_bytes.decode('utf-8')
        data = json.loads(body_text)
        
        phone_number = data.get("phone_number")
        message_text = data.get("message")
        
        if not phone_number or not message_text:
            return {"status": "error", "message": "Both phone_number and message are required"}
            
        logger.info(f"Simulating WhatsApp message from {phone_number}: {message_text}")
        
        # Initialize assistant if needed
        if app.state.course_assistant is None:
            logger.info("Initializing course_assistant for simulation")
            try:
                app.state.course_assistant = CourseAssistant()
                logger.info("Course assistant initialized successfully for simulation")
            except Exception as e:
                logger.error(f"Failed to initialize course_assistant: {str(e)}")
                logger.error(traceback.format_exc())
                return {"status": "error", "message": f"Assistant initialization failed: {str(e)}"}
            
        # Process message directly
        try:
            logger.info("Calling handle_message on assistant for simulation")
            response = await app.state.course_assistant.handle_message(phone_number, message_text)
            logger.info(f"Got simulation response from assistant: {json_serialize(response)}")
            
            if response and response.get("type") == "text":
                # Just return the response without sending to WhatsApp
                return {
                    "status": "success", 
                    "response": response["content"], 
                    "would_send_to": phone_number
                }
            else:
                logger.error(f"Invalid response format from assistant in simulation: {response}")
                return {"status": "error", "message": "Invalid response format from assistant"}
        except Exception as e:
            logger.error(f"Error handling simulation message: {str(e)}")
            logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
            
    except Exception as e:
        logger.error(f"Error in simulate endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables"""
    return {
        "OPENAI_API_KEY": settings.OPENAI_API_KEY[:5] + "..." if settings.OPENAI_API_KEY else None,
        "WHATSAPP_TOKEN": settings.WHATSAPP_TOKEN[:5] + "...",
        "PHONE_NUMBER_ID": settings.PHONE_NUMBER_ID,
        "WEBHOOK_VERIFY_TOKEN": settings.WEBHOOK_VERIFY_TOKEN,
        "WABA_ID": settings.WABA_ID,
    }

@app.on_event("startup")
async def startup_event():
    """Initialize assistants when the app starts"""
    try:
        # Force reload environment variables and clear cache
        from dotenv import load_dotenv
        load_dotenv(override=True)
        from .config import clear_settings_cache
        clear_settings_cache()

        logger.info("Starting application initialization...")
        app.state.course_assistant = CourseAssistant()
        logger.info("Assistants initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize assistants: {str(e)}")
        logger.error(traceback.format_exc())

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the app shuts down"""
    logger.info("Application shutting down...")
