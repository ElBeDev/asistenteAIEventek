import httpx
import logging
import json
import traceback
from ..config import get_settings

class WhatsAppService:
    def __init__(self):
        self.settings = get_settings()
        self.api_url = "https://graph.facebook.com/v17.0"
        self.token = self.settings.WHATSAPP_TOKEN
        self.phone_number_id = self.settings.PHONE_NUMBER_ID
        self.waba_id = self.settings.WABA_ID  # Add this line
        self.logger = logging.getLogger("whatsapp_service")
    
    async def send_message(self, recipient_id: str, message: str):
        """Send text message to WhatsApp user"""
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        # Properly handle text encoding
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        
        # Remove any problematic characters
        cleaned_message = message.encode('utf-8', errors='ignore').decode('utf-8')
        
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": "text",
            "text": {"body": cleaned_message}
        }
        
        self.logger.info(f"Sending message to {recipient_id}, length: {len(cleaned_message)}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                self.logger.info(f"Message sent successfully to {recipient_id}")
                return result
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error sending message: {e.response.status_code} - {e.response.text}")
            self.logger.error(traceback.format_exc())
            raise
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise
    
    async def check_phone_status(self, phone_number: str):
        """Check if a phone number is valid for WhatsApp messaging"""
        test_url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Send a minimal "Typing" indicator which is less intrusive
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
            "type": "reaction",
            "reaction": {
                "message_id": "test_message_id",
                "emoji": "👍"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(test_url, headers=headers, json=data)
                
                # Even if this fails, we get information about whether the number exists
                result = {
                    "status_code": response.status_code,
                    "response": response.json() if response.status_code < 300 else response.text,
                    "is_valid": response.status_code == 200
                }
                
                return result
        except Exception as e:
            self.logger.error(f"Error checking phone status: {str(e)}")
            return {
                "status_code": 500,
                "response": str(e),
                "is_valid": False
            }

    async def check_webhook_subscription(self):
        """Check webhook subscriptions using WABA_ID"""
        url = f"{self.api_url}/{self.waba_id}/subscribed_apps"  # Use WABA_ID here
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                self.logger.info(f"Webhook subscription status: {response.status_code}")
                self.logger.info(response.json())
                return response.json()
        except Exception as e:
            self.logger.error(f"Error checking webhook subscription: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    async def check_message_metrics(self):
        """Check message delivery stats"""
        url = f"{self.api_url}/{self.phone_number_id}/insights"
        headers = {"Authorization": f"Bearer {self.token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                self.logger.info(f"Message metrics response: {response.status_code}")
                self.logger.info(response.json())
                return response.json()
        except Exception as e:
            self.logger.error(f"Error checking message metrics: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

    async def mark_message_as_read(self, message_id: str):
        """Mark a WhatsApp message as read"""
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)
                response.raise_for_status()
                self.logger.info(f"Message marked as read: {message_id}")
                return response.json()
        except Exception as e:
            self.logger.error(f"Error marking message as read: {str(e)}")
            raise