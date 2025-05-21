import requests
import os
from dotenv import load_dotenv
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def test_whatsapp_message():
    token = os.getenv('WHATSAPP_TOKEN')
    phone_number_id = os.getenv('PHONE_NUMBER_ID')
    
    url = f"https://graph.facebook.com/v22.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Simplified message format according to WhatsApp Business API specs
    data = {
        "messaging_product": "whatsapp",
        "to": "34644691478",
        "type": "text",
        "text": {
            "body": "Test message from Eventek IA"
        }
    }
    
    logger.info("📤 Testing message parameters...")
    logger.info(f"Token prefix: {token[:10]}...")
    logger.info(f"Phone Number ID: {phone_number_id}")
    logger.info(f"Request data: {data}")
    
    try:
        response = requests.post(
            url=url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info("✅ Message sent successfully")
            logger.info(f"Response: {response.json()}")
            return response.json()
        else:
            logger.error(f"❌ Failed with status code: {response.status_code}")
            logger.error(f"Response: {response.json()}")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    # Set debug logging for requests
    logging.getLogger("requests").setLevel(logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    
    test_whatsapp_message()