import requests
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def setup_webhook():
    token = os.getenv('WHATSAPP_TOKEN')
    waba_id = os.getenv('WABA_ID')
    phone_number_id = os.getenv('PHONE_NUMBER_ID')
    
    # First, verify phone number
    phone_url = f"https://graph.facebook.com/v22.0/{phone_number_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    logger.info("🔍 Verifying phone number...")
    phone_response = requests.get(phone_url, headers=headers)
    if phone_response.status_code != 200:
        logger.error(f"Phone verification failed: {phone_response.json()}")
        return
    
    # Set up webhook subscription
    url = f"https://graph.facebook.com/v22.0/{waba_id}/subscribed_apps"
    
    data = {
        "subscribed_fields": ["messages", "message_template_status_update"]
    }
    
    logger.info(f"🔗 Setting up webhook for WABA ID: {waba_id}")
    logger.info(f"URL: {url}")
    
    response = requests.post(url, headers=headers, json=data)
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Response: {response.json()}")

if __name__ == "__main__":
    setup_webhook()