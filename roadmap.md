# WhatsApp Bot Implementation: Roadmap & Documentation

## Project Overview
This document outlines the WhatsApp bot implementation for the 4º Curso de Medicina Pleural y Broncoscopía 2025, including all steps taken, architecture decisions, implementation details, and deployment procedures.

## 1. Project Architecture

### Core Components
- **FastAPI Backend**: Handles webhook events and API endpoints
- **OpenAI Assistant Integration**: Processes natural language queries about the course
- **WhatsApp Business API**: Sends and receives messages through WhatsApp
- **Google Cloud Run**: Hosts the service with automatic scaling

### System Flow
1. User sends message to WhatsApp business number
2. WhatsApp forwards message to our webhook
3. Backend processes message and queries OpenAI Assistant
4. Assistant generates response with course information
5. Backend sends response back to user via WhatsApp API

## 2. Implementation Roadmap & Checkpoints

### Phase 1: Environment Setup ✅
- Created project structure with proper separation of concerns
- Set up configuration management with `.env` and `config.py`
- Implemented logging with detailed information for debugging

### Phase 2: Assistant Implementation ✅
- Created `CourseAssistant` class that manages conversations
- Implemented thread management for multiple users
- Added function tools for retrieving course information
- Set up file search capabilities for course documentation

### Phase 3: WhatsApp Integration ✅
- Created `WhatsAppService` for handling API communication
- Implemented webhook verification for Meta platform
- Added message processing and response formatting
- Built debugging endpoints for testing without WhatsApp

### Phase 4: Deployment & Infrastructure ✅
- Set up Google Cloud Run configuration
- Configured environment variables securely
- Implemented auto-scaling and resource management
- Established deployment workflow

### Phase 5: Testing & Validation ✅
- Verified webhook functioning with Meta platform
- Tested end-to-end message flow
- Confirmed proper handling of Spanish characters
- Validated assistant responses for accuracy

## 3. Implementation Details

### WhatsApp Business API Configuration
- **Phone Number**: +52 1 427 126 4163
- **Phone Number ID**: 601463503052178
- **WhatsApp Business Account ID**: 1213994217052647
- **Webhook URL**: https://whatsapp-bot-strcbht24q-uc.a.run.app/webhook
- **Verification Token**: 123456

### Key Environment Variables
```
OPENAI_API_KEY=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
ETNOSUR_ASSISTANT_ID=asst_IWLsZT9D9vAc4qAiqGCMUvgn
WHATSAPP_TOKEN=EAATDmvk3GEcBO6HkEKoRjsyZBIdQj3HuC7v9hjinVFM8v7HhCajWmYZCGZC4Nj1sPPPR4RtPYVjK1BFQnvZCE9dpOPGQHioiCCyQJE3ppOWJaFP4U0gnXMh8ZCuOqpkl5MUOku63r6nz7BsIZCF5lXcLh2nvhZAVZB1veksxJG0yVFKSbRDHvtCYeGFbH5NNg29CDAZDZD
PHONE_NUMBER_ID=601463503052178
WEBHOOK_VERIFY_TOKEN=123456
```

### Cloud Run Deployment
- **Service URL**: https://whatsapp-bot-strcbht24q-uc.a.run.app
- **Region**: us-central1
- **Auto-scaling**: 1-10 instances

## 4. Implementation Challenges & Solutions

### Challenge 1: WhatsApp Business API Registration
**Problem**: WhatsApp number showed "Pendiente" (Pending) status
**Solution**: Completed the Cloud API registration process and waited for Meta approval

### Challenge 2: Character Encoding Issues
**Problem**: Spanish characters (á, é, í, ó, ú) displayed incorrectly
**Solution**: Implemented proper UTF-8 encoding in all API communications

### Challenge 3: Project Configuration Mismatch
**Problem**: Deployment targeted wrong Google Cloud project
**Solution**: Updated gcloud configuration to use correct project ID

### Challenge 4: Environment Variable Management
**Problem**: Updating one env var replaced all others
**Solution**: Updated deployment to include all environment variables together

## 5. Testing & Debugging

### Test Scripts
- `test_send_whatsapp.py`: Tests direct message sending to a number
- `test_utf8.py`: Tests handling of Spanish characters
- `register_whatsapp_cloud.py`: Registers number with WhatsApp Cloud API

### Debugging Endpoints
- `/debug/assistant`: Checks assistant status and configuration
- `/debug/simulate-whatsapp`: Tests the bot without actual WhatsApp

### WhatsApp Message Testing
Successfully tested sending messages to personal number with response:
```
Success! Message ID: {
  "messaging_product": "whatsapp",
  "contacts": [
    {
      "input": "5219991234567",
      "wa_id": "5219991234567"
    }
  ],
  "messages": [
    {
      "id": "wamid.HBgNNTIxOTk5MTIzNDU2NxUCABEYEjlFMzc2QTE4QzQ4REE0NDAzQgA="    
    }
  ]
}
```

## 6. Deployment Commands

### Initial Deployment
```powershell
gcloud run deploy whatsapp-bot `
  --region us-central1 `
  --source . `
  --allow-unauthenticated `
  --set-env-vars="OPENAI_API_KEY=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" `
  --set-env-vars="ETNOSUR_ASSISTANT_ID=asst_IWLsZT9D9vAc4qAiqGCMUvgn" `
  --set-env-vars="WHATSAPP_TOKEN=EAATDmvk3GEcBO6HkEKoRjsyZBIdQj3HuC7v9hjinVFM8v7HhCajWmYZCGZC4Nj1sPPPR4RtPYVjK1BFQnvZCE9dpOPGQHioiCCyQJE3ppOWJaFP4U0gnXMh8ZCuOqpkl5MUOku63r6nz7BsIZCF5lXcLh2nvhZAVZB1veksxJG0yVFKSbRDHvtCYeGFbH5NNg29CDAZDZD" `
  --set-env-vars="PHONE_NUMBER_ID=601463503052178" `
  --set-env-vars="WEBHOOK_VERIFY_TOKEN=123456"
```

### Check Service URL
```powershell
gcloud run services describe whatsapp-bot --region us-central1 --format="value(status.url)"
```

### Monitor Logs
```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=whatsapp-bot" --limit=50
```

## 7. Future Enhancements

### Short-term Improvements
- Add support for image/media messages
- Implement quick replies for common questions
- Add analytics for message tracking

### Medium-term Enhancements
- Create admin dashboard for monitoring conversations
- Add message templates for course announcements
- Implement multi-language support

### Long-term Vision
- Integrate with course registration system
- Add payment processing capabilities
- Develop personalized learning pathways

## 8. Maintenance Guide

### Regular Tasks
- Monitor WhatsApp Business API token expiration
- Check Cloud Run service performance
- Update course information as needed

### Troubleshooting
- Use `/debug/assistant` endpoint to verify configuration
- Check logs with `gcloud logging read` command
- Test message flow with simulation endpoint

### Updates and Redeployment
1. Make code changes
2. Test locally with `run_local.py`
3. Deploy with `gcloud run deploy` command
4. Verify webhook is functioning

---

Document prepared: April 5, 2025