import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_webhook():
    # Get credentials
    token = os.getenv('WHATSAPP_TOKEN')
    phone_number_id = os.getenv('PHONE_NUMBER_ID')
    webhook_verify_token = os.getenv('WEBHOOK_VERIFY_TOKEN')

    # Webhook URL
    webhook_url = "https://eventek-ia.uc.r.appspot.com/webhook"

    # Test webhook verification
    verify_params = {
        "hub.mode": "subscribe",
        "hub.verify_token": webhook_verify_token,
        "hub.challenge": "test_challenge"
    }

    try:
        print("\nTesting Webhook Verification...")
        response = requests.get(webhook_url, params=verify_params)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response.status_code == 200
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error testing webhook: {e}")
        return False

if __name__ == "__main__":
    test_webhook()