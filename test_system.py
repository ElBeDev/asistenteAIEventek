import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

class SystemTester:
    def __init__(self):
        self.base_url = "https://eventek-ia.uc.r.appspot.com"
        self.phone_number = "34644691478"  # Your registered WhatsApp number
        self.whatsapp_token = os.getenv('WHATSAPP_TOKEN')
        self.phone_number_id = os.getenv('PHONE_NUMBER_ID')

    def test_assistant_endpoint(self, question: str):
        """Test the assistant endpoint directly"""
        url = f"{self.base_url}/debug/simulate-whatsapp"
        
        data = {
            "phone_number": self.phone_number,
            "message": question
        }
        
        print(f"\n🤖 Testing Assistant...")
        print(f"Question: {question}")
        
        try:
            response = requests.post(url, json=data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    def test_whatsapp_sending(self, message: str):
        """Test sending a WhatsApp message"""
        url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        
        data = {
            "messaging_product": "whatsapp",
            "to": self.phone_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json"
        }
        
        print(f"\n📱 Testing WhatsApp...")
        print(f"Message: {message}")
        
        try:
            response = requests.post(url, json=data, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return response.json() if response.status_code == 200 else None
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None

    def test_webhook_verification(self):
        """Test webhook verification"""
        verify_token = os.getenv('WEBHOOK_VERIFY_TOKEN')
        challenge = "test_challenge"
        
        url = f"{self.base_url}/webhook"
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": verify_token,
            "hub.challenge": challenge
        }
        
        print(f"\n🔗 Testing Webhook Verification...")
        
        try:
            response = requests.get(url, params=params)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False

    def test_webhook_handler(self):
        """Test webhook message handling"""
        # Simulate a WhatsApp incoming message
        test_webhook_data = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "34644691478",
                            "phone_number_id": self.phone_number_id
                        },
                        "contacts": [{
                            "profile": {
                                "name": "Test User"
                            },
                            "wa_id": "34644691478"
                        }],
                        "messages": [{
                            "from": "34644691478",
                            "text": {
                                "body": "Test message"
                            },
                            "timestamp": "1234567890",
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }

        url = f"{self.base_url}/webhook"
        response = requests.post(url, json=test_webhook_data)
        print(f"\n📥 Testing Webhook Handler...")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200

def run_tests():
    tester = SystemTester()
    
    # Test cases for the assistant
    test_questions = [
        "¿Qué es la medicina pleural?",
        "¿Cuándo es el curso?",
        "¿Quiénes son los ponentes?",
        "¿Cuál es el costo del curso?"
    ]
    
    print("\n🧪 Starting System Tests...")
    print("=" * 50)
    
    # 1. Test webhook verification
    print("\nTest 1: Webhook Verification")
    tester.test_webhook_verification()
    
    # 2. Test assistant responses
    print("\nTest 2: Assistant Responses")
    for question in test_questions:
        response = tester.test_assistant_endpoint(question)
        if response:
            # 3. Test WhatsApp sending for each successful response
            print("\nTest 3: WhatsApp Message Sending")
            tester.test_whatsapp_sending(response.get('response', ''))
        
        print("-" * 50)
    
    # Add webhook handler test
    print("\nTest 4: Webhook Message Handler")
    tester.test_webhook_handler()

if __name__ == "__main__":
    run_tests()