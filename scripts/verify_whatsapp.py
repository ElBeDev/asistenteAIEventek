import requests
import os
from dotenv import load_dotenv

load_dotenv()

def verify_whatsapp_setup():
    token = os.getenv('WHATSAPP_TOKEN')
    phone_id = os.getenv('PHONE_NUMBER_ID')
    waba_id = os.getenv('WABA_ID')

    # Check business account
    business_url = f"https://graph.facebook.com/v22.0/{waba_id}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print("\n🔍 Checking WhatsApp Business Account...")
    response = requests.get(business_url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

    # Check phone number
    phone_url = f"https://graph.facebook.com/v22.0/{waba_id}/phone_numbers"
    
    print("\n📱 Checking Phone Numbers...")
    response = requests.get(phone_url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    verify_whatsapp_setup()