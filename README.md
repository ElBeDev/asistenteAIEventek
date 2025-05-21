# Eventek AI Assistant - WhatsApp Bot

This project implements a WhatsApp bot powered by OpenAI's Assistants API and FastAPI. It serves as a virtual assistant for Eventek, providing information about their event services based on uploaded knowledge files. The bot interacts with users via WhatsApp and is designed for deployment on Google Cloud Run.

## Features

*   **WhatsApp Integration:** Receives and responds to user messages via the WhatsApp Business API.
*   **OpenAI Assistants API:** Leverages the power of OpenAI's GPT models and the Assistants API for natural language understanding and response generation.
*   **Knowledge Retrieval:** Uses the `file_search` tool within the Assistants API to answer questions based on the content of uploaded files (e.g., [`src/course_info.json`](d:\GitHub\asistenteAIEventek\src\course_info.json)).
*   **Conversation Management:** Maintains conversation history for context.
*   **FastAPI Backend:** Provides a robust and asynchronous API framework.
*   **Cloud Deployment:** Configured for deployment on Google Cloud Run ([`app.yaml`](#app.yaml)).
*   **Webhook Verification:** Handles WhatsApp webhook verification requests.

## Technology Stack

*   **Backend:** Python, FastAPI, Uvicorn
*   **AI:** OpenAI API (Assistants API, GPT-3.5-Turbo/GPT-4)
*   **Messaging:** WhatsApp Business API
*   **Deployment:** Google Cloud Run, Docker (implied for Cloud Run)
*   **Dependencies:** `openai`, `fastapi`, `uvicorn`, `python-dotenv`, `httpx`, `pytz`, `requests` (likely)

## Project Structure

```
.
├── .env                  # Environment variables (local development) - IMPORTANT: Add to .gitignore
├── .gitignore            # Git ignore file
├── app.yaml              # Google Cloud Run deployment configuration
├── main.py               # Entry point for running the app locally
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── roadmap.md            # Project planning/roadmap
├── zerror.txt            # Log file (consider adding to .gitignore)
├── src/                  # Source code directory
│   ├── __init__.py
│   ├── app.py            # FastAPI application setup and endpoints
│   ├── assistant_logic.py # Core logic for the OpenAI Assistant interaction (CourseAssistant)
│   ├── config.py         # Configuration loading (if used, otherwise env vars directly)
│   ├── course_info.json  # Knowledge base file for the assistant
│   ├── services/         # Service integrations (e.g., WhatsApp)
│   │   └── whatsapp_service.py # Logic for interacting with WhatsApp API (assumed)
│   └── __pycache__/      # Python cache files
├── scripts/              # Utility scripts
│   ├── setup_webhook.py  # Script to configure the WhatsApp webhook (assumed purpose)
│   ├── test_message_flow.py # Script to test message handling (assumed purpose)
│   └── verify_whatsapp.py # Script for webhook verification testing (assumed purpose)
└── tests/                # Unit and integration tests
    ├── __init__.py
    └── test_app.py       # Tests for the FastAPI application
```

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd asistenteAIEventek
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    .\venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set up Environment Variables:**
    Create a `.env` file in the project root directory and populate it with the necessary variables (see below). **Ensure `.env` is added to your `.gitignore` file.**

## Environment Variables

The following environment variables are required. You can set them in a `.env` file for local development or configure them in your deployment environment (like Google Cloud Run secrets or environment variables).

*   `OPENAI_API_KEY`: Your OpenAI API key.
*   `EVENTEK_ASSISTANT_ID`: The ID of your OpenAI Assistant. If set to `force_new` or left blank, the application ([`src/assistant_logic.py`](d:\GitHub\asistenteAIEventek\src\assistant_logic.py)) will attempt to create a new assistant and upload the [`src/course_info.json`](d:\GitHub\asistenteAIEventek\src\course_info.json) file. The new ID will be logged - **update this variable with the new ID** to avoid creating duplicates on subsequent runs.
*   `WHATSAPP_TOKEN`: Your WhatsApp Business API permanent token.
*   `PHONE_NUMBER_ID`: The Phone Number ID associated with your WhatsApp Business number.
*   `WABA_ID`: Your WhatsApp Business Account ID.
*   `WEBHOOK_VERIFY_TOKEN`: A secret token you define for verifying webhook requests from Meta.
*   `LOG_LEVEL`: Logging level (e.g., `DEBUG`, `INFO`, `WARNING`). Defaults to `INFO` if not set.

**Example `.env` file:**

```dotenv
# .env
OPENAI_API_KEY="sk-..."
EVENTEK_ASSISTANT_ID="asst_..." # Or leave blank/set to "force_new" on first run
WHATSAPP_TOKEN="EAA..."
PHONE_NUMBER_ID="1234567890..."
WABA_ID="9876543210..."
WEBHOOK_VERIFY_TOKEN="your_secret_verify_token"
LOG_LEVEL="DEBUG"
```

## Running Locally

1.  Ensure all environment variables are set (e.g., via the `.env` file).
2.  Run the FastAPI application using Uvicorn:
    ```bash
    python main.py
    ```
    Or directly with uvicorn:
    ```bash
    uvicorn src.app:app --host 0.0.0.0 --port 8080 --reload
    ```
    The application will be available at `http://localhost:8080`. The `/webhook` endpoint will be ready to receive messages from WhatsApp. You might need a tool like ngrok to expose your local endpoint publicly for WhatsApp webhook testing.

## Running Tests

(Assuming tests are set up with `pytest`)

1.  Make sure you are in the project root directory with the virtual environment activated.
2.  Run the tests:
    ```bash
    pytest
    ```

## Deployment (Google Cloud Run)

The project is configured for deployment on Google Cloud Run using the [`app.yaml`](#app.yaml) file.

1.  **Prerequisites:**
    *   Google Cloud SDK (`gcloud`) installed and configured.
    *   A Google Cloud Project with Billing enabled.
    *   Cloud Run API enabled.
    *   Secret Manager API enabled (recommended for storing secrets like API keys).
2.  **Configure Secrets (Recommended):**
    Store sensitive environment variables (like `OPENAI_API_KEY`, `WHATSAPP_TOKEN`, `WEBHOOK_VERIFY_TOKEN`) in Google Secret Manager and grant the Cloud Run service account access. Update [`app.yaml`](#app.yaml) to reference these secrets.
3.  **Deploy:**
    Navigate to the project root directory in your terminal and run:
    ```bash
    gcloud run deploy eventek-assistant --source . --region <your-gcp-region> --allow-unauthenticated
    ```
    *   Replace `<your-gcp-region>` with your desired region (e.g., `us-central1`).
    *   The `--allow-unauthenticated` flag makes the service publicly accessible, which is necessary for the WhatsApp webhook. Ensure your `/webhook` endpoint properly validates requests using the `WEBHOOK_VERIFY_TOKEN`.
4.  **Configure WhatsApp Webhook:**
    Once deployed, Google Cloud Run will provide a service URL (e.g., `https://eventek-assistant-xxxxx-uc.a.run.app`). Configure your WhatsApp Business App's webhook settings in the Meta Developer Portal:
    *   **Callback URL:** `https://<your-cloud-run-service-url>/webhook`
    *   **Verify Token:** The same value you set for the `WEBHOOK_VERIFY_TOKEN` environment variable.
    *   Subscribe to the `messages` webhook field.

## Utility Scripts (`scripts/`)

*   [`scripts/setup_webhook.py`](d:\GitHub\asistenteAIEventek\scripts\setup_webhook.py): (Assumed) Helps automate the initial setup or update of the WhatsApp webhook URL and subscriptions via an API call.
*   [`scripts/test_message_flow.py`](d:\GitHub\asistenteAIEventek\scripts\test_message_flow.py): (Assumed) Sends sample messages to the deployed or local webhook endpoint to test the end-to-end flow.
*   [`scripts/verify_whatsapp.py`](d:\GitHub\asistenteAIEventek\scripts\verify_whatsapp.py): (Assumed) Might simulate the GET verification request from WhatsApp to test the verification logic in [`src/app.py`](d:\GitHub\asistenteAIEventek\src\app.py).

(Add specific instructions for running these scripts if available).
