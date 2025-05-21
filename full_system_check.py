import requests
import asyncio

async def full_system_check():
    """Comprehensive check of WhatsApp integration configuration"""
    print("\n===== WHATSAPP INTEGRATION FULL SYSTEM CHECK =====\n")
    
    # Hardcoded raw values
    PHONE_NUMBER_ID = "630002156858819"
    WHATSAPP_TOKEN = "EAARaareJTTABOyJr5nkVMGMYo7g7MltXeovEi9ZBZCI5a5tWdspJmbPOmEMthwQJC8n4mPrP7vV7W2fh2y6NZAAiYdk0gXgvm6rMJdOMjZBhVyawX2KWb37Ys7ESuNZBZAuFzhTpuS4TRZANMWiAkMXQs9q8Jg18lFvCcIJWM8Uo0HSqkFji0TnxtoSychqmZCVbgAZDZD"
    WEBHOOK_VERIFY_TOKEN = "123456"
    WABA_ID = "1358661355330235"

    # Step 1: Check hardcoded values
    print(f"✅ PHONE_NUMBER_ID: {PHONE_NUMBER_ID}")
    print(f"✅ WHATSAPP_TOKEN: {WHATSAPP_TOKEN[:5]}...{WHATSAPP_TOKEN[-5:]}")
    print(f"✅ WEBHOOK_VERIFY_TOKEN: {WEBHOOK_VERIFY_TOKEN}")
    print(f"✅ WABA_ID: {WABA_ID}")
    
    # Step 2: Check phone number validity
    print("\n----- Phone Number Verification -----")
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            phone_data = response.json()
            print(f"✅ Phone number ID is valid: {PHONE_NUMBER_ID}")
            print(f"   Business: {phone_data.get('verified_name')}")
            print(f"   Display Number: {phone_data.get('display_phone_number')}")
            print(f"   Status: {phone_data.get('code_verification_status')}")
            print(f"   Quality Rating: {phone_data.get('quality_rating')}")
            
            webhook_url = phone_data.get('webhook_configuration', {}).get('application')
            if webhook_url:
                print(f"✅ Webhook URL configured: {webhook_url}")
            else:
                print(f"❌ No webhook URL configured!")
        else:
            print(f"❌ Error verifying phone number: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Error checking phone: {str(e)}")
        return
    
    # Step 3: Check webhook subscription
    print("\n----- Webhook Subscription -----")
    subscription_url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/subscribed_apps"
    try:
        response = requests.get(subscription_url, headers=headers)
        if response.status_code == 200:
            subscription = response.json()
            if "data" in subscription and subscription["data"]:
                print(f"✅ Webhook subscription active")
                for app in subscription["data"]:
                    print(f"   App Name: {app.get('name')}")
                    fields = app.get('subscribed_fields', [])
                    print(f"   Subscribed Fields: {', '.join(fields)}")
            else:
                print(f"❌ No webhook subscriptions found!")
                print("   You need to subscribe to webhook events.")
        else:
            print(f"❌ Error checking webhook subscription: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Error checking webhook subscription: {str(e)}")
    
    # Step 4: Verify app deployment (check if your webhook endpoint is accessible)
    print("\n----- Webhook Endpoint Verification -----")
    webhook_url = "https://medicina-pleural.uc.r.appspot.com/webhook"
    
    try:
        response = requests.get(webhook_url)
        print(f"Webhook endpoint status: {response.status_code}")
        
        if response.status_code < 500:
            print(f"✅ Webhook endpoint is accessible")
        else:
            print(f"❌ Webhook endpoint is not responding properly: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking webhook endpoint: {str(e)}")
    
    print("\n===== SYSTEM CHECK COMPLETE =====")

if __name__ == "__main__":
    asyncio.run(full_system_check())