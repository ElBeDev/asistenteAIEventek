import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def register_account():
    # Get credentials
    token = os.getenv('WHATSAPP_TOKEN')
    phone_number_id = os.getenv('PHONE_NUMBER_ID')
    
    # API endpoint for registration (using phone_number_id)
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/register"
    
    # Registration payload
    data = {
        "messaging_product": "whatsapp",
        "pin": "317677",
        "verified_name": "Eventek IA"
    }
    
    # Headers with authentication
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\nRegistering WhatsApp Account...")
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        print(f"Status Code: {response.status_code}")
        if response.text:
            result = response.json()
            print("\nRegistration Results:")
            print("=====================")
            for key, value in result.items():
                print(f"{key}: {value}")
        else:
            print("✅ Registration successful!")
            
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Error registering account: {e}")
        if hasattr(e.response, 'json'):
            print("Error details:", e.response.json())
        return False

if __name__ == "__main__":
    register_account()