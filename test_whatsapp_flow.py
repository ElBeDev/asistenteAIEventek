import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

class WhatsAppFlowTester:
    def __init__(self):
        self.base_url = "https://eventek-ia.uc.r.appspot.com"
        self.phone_number = "34644691478"
        self.whatsapp_token = os.getenv('WHATSAPP_TOKEN')
        self.phone_number_id = os.getenv('PHONE_NUMBER_ID')
        
    def test_incoming_message(self):
        """Simulate incoming WhatsApp message"""
        webhook_url = f"{self.base_url}/webhook"
        
        # Simulate WhatsApp webhook payload
        webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": self.phone_number_id,
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": self.phone_number,
                            "phone_number_id": self.phone_number_id
                        },
                        "messages": [{
                            "from": self.phone_number,
                            "id": f"wamid.test{datetime.now().timestamp()}",
                            "text": {
                                "body": "¿Qué es la medicina pleural?"
                            },
                            "timestamp": str(int(datetime.now().timestamp())),
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        
        print("\n🔍 Testing Incoming Message Flow...")
        print(f"URL: {webhook_url}")
        print(f"Payload: {json.dumps(webhook_data, indent=2)}")
        
        response = requests.post(webhook_url, json=webhook_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        return response

def run_flow_test():
    tester = WhatsAppFlowTester()
    
    print("\n🧪 Starting WhatsApp Flow Test")
    print("=" * 50)
    
    # Test incoming message
    webhook_response = tester.test_incoming_message()
    
    if webhook_response.status_code == 200:
        print("\n✅ Webhook received message successfully")
    else:
        print("\n❌ Webhook failed to process message")
        print(f"Error: {webhook_response.text}")

if __name__ == "__main__":
    run_flow_test()