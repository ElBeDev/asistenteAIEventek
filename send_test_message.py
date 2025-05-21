import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Load environment variables
load_dotenv()

def ask_assistant(question: str):
    # Correct endpoint for the deployed assistant
    cloud_url = "https://eventek-ia.uc.r.appspot.com/debug/simulate-whatsapp"
    
    # Match the expected payload format from app.py
    data = {
        "phone_number": "34644691478",
        "message": question
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\n🤖 Consultando al asistente...")
        print(f"URL: {cloud_url}")
        print(f"Request Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(cloud_url, json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            return response_data.get('response', 'No pude obtener una respuesta del asistente.')
        else:
            return f"Error {response.status_code}: {response.text}"
    except Exception as e:
        print(f"❌ Error Assistant: {str(e)}")
        return f"Error al conectar con el asistente: {str(e)}"

def send_whatsapp_message(number: str, message: str):
    token = os.getenv('WHATSAPP_TOKEN')
    phone_number_id = os.getenv('PHONE_NUMBER_ID')
    
    url = f"https://graph.facebook.com/v19.0/{phone_number_id}/messages"
    
    # Format message for WhatsApp
    formatted_message = (
        "*Consulta sobre el Curso de Medicina Pleural*\n\n"
        f"{message}\n\n"
        "_Mensaje enviado por el asistente virtual de Eventek IA_"
    ).replace('"', '"').replace('"', '"')  # Fix smart quotes

    # WhatsApp payload with required fields
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": number.replace("+", ""),  # Remove + if present
        "type": "text",
        "text": {
            "body": formatted_message,
            "preview_url": False
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print(f"\n📤 Enviando mensaje a WhatsApp...")
        print(f"URL: {url}")
        print(f"Request Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Mensaje enviado correctamente")
            print(f"Message ID: {result['messages'][0]['id']}")
            return result
        else:
            print(f"\n❌ Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error WhatsApp: {str(e)}")
        return None

def handle_whatsapp_webhook(request_data: dict):
    """Handle incoming WhatsApp messages"""
    try:
        # Extract message data
        entry = request_data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']
        
        if 'messages' in value:
            message = value['messages'][0]
            
            # Get message details
            phone_number = message['from']
            message_text = message['text']['body']
            
            # Get response from assistant
            assistant_response = ask_assistant(message_text)
            
            # Send response back via WhatsApp
            if assistant_response and "Error" not in assistant_response:
                send_whatsapp_message(phone_number, assistant_response)
                
            return {"status": "success"}
            
    except Exception as e:
        print(f"❌ Error processing webhook: {str(e)}")
        return {"status": "error", "message": str(e)}

def verify_webhook(mode: str, token: str, challenge: str):
    """Verify WhatsApp webhook"""
    verify_token = os.getenv('WEBHOOK_VERIFY_TOKEN')
    
    if mode == 'subscribe' and token == verify_token:
        return int(challenge)
    else:
        raise ValueError('Invalid webhook verification request')

def test_interaction():
    test_number = "34644691478"
    test_questions = [
        "¿Qué es la medicina pleural?"
    ]
    
    print("\n🤖 Iniciando prueba de interacción...")
    
    for question in test_questions:
        print(f"\n📝 Pregunta: {question}")
        
        assistant_response = ask_assistant(question)
        print(f"\n🤔 Respuesta del asistente:\n{assistant_response}")
        
        if assistant_response and "Error" not in assistant_response:
            whatsapp_result = send_whatsapp_message(test_number, assistant_response)
            
            if whatsapp_result:
                print(f"\n✅ Mensaje enviado correctamente")
                print(f"Message ID: {whatsapp_result['messages'][0]['id']}")
            else:
                print(f"\n❌ Error al enviar mensaje")
        else:
            print("\n⚠️ No se envía mensaje debido a error en la respuesta del asistente")
        
        print("\n" + "-" * 50)

def test_webhook():
    """Test webhook handling"""
    # Simulate incoming WhatsApp message
    test_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "34644691478",
                        "text": {
                            "body": "¿Qué es la medicina pleural?"
                        }
                    }]
                }
            }]
        }]
    }
    
    print("\n🔄 Testing webhook handling...")
    result = handle_whatsapp_webhook(test_data)
    print(f"Result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    test_interaction()  # Test normal flow
    test_webhook()      # Test webhook handling