# -*- coding: utf-8 -*-
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Import settings, db functions, assistant logic
from .config import settings
from .db import get_db, close_db
from .assistant_logic import CourseAssistant, initialize_assistant

# Import the routers
from .routers import crm, whatsapp

# --- Setup logging ---
# Get the root log level from settings (e.g., DEBUG, INFO, WARNING)
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
# Configure the root logger
logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Set higher levels for noisy libraries ---
# Keep httpx, httpcore, openai at WARNING unless you need their detailed logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)

# Set pymongo loggers to WARNING to hide DEBUG and INFO messages
logging.getLogger("pymongo").setLevel(logging.WARNING)
# You could be more specific if needed, e.g.:
# logging.getLogger("pymongo.command").setLevel(logging.WARNING)
# logging.getLogger("pymongo.connection").setLevel(logging.WARNING)
# logging.getLogger("pymongo.topology").setLevel(logging.WARNING)

# Get the main application logger
logger = logging.getLogger("whatsapp_bot") # Or "eventek_assistant" or your main logger name

# --- Global Variables ---
# Store assistant instance globally or manage via dependency injection
assistant_instance: CourseAssistant | None = None

# --- FastAPI App Setup ---
app = FastAPI(
    title="Eventek Assistant & CRM",
    description="Handles WhatsApp interactions and provides a simple CRM.",
    version="0.1.0"
)

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for simplicity, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static Files ---
# Mount static files
app.mount("/static", StaticFiles(directory="src/static"), name="static")

# --- Dependency for Assistant ---
# Function to get the initialized assistant instance
async def get_assistant() -> CourseAssistant:
    if assistant_instance is None:
        # This should ideally not happen if startup event works correctly
        logger.error("Assistant instance is None when requested by dependency!")
        raise RuntimeError("Assistant not initialized")
    return assistant_instance

# --- Event Handlers (Startup/Shutdown) ---
@app.on_event("startup")
async def startup_event():
    global assistant_instance
    logger.info("Application startup: Initializing database connection...")
    try:
        await get_db() # Initialize DB connection pool
        logger.info("Database connection established.")
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to connect to database during startup: {e}", exc_info=True)

    logger.info("Initializing OpenAI Assistant...")
    try:
        # assistant_instance = await initialize_assistant( # OLD WAY
        #     settings.OPENAI_API_KEY,
        #     settings.EVENTEK_ASSISTANT_ID
        # )
        assistant_instance = await initialize_assistant() # NEW WAY - NO ARGUMENTS
        # Provide the instance to the dependency system
        app.dependency_overrides[CourseAssistant] = lambda: assistant_instance
        logger.info("Assistant initialized successfully")
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize OpenAI assistant during startup: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown: Closing database connection...")
    await close_db()
    logger.info("Database connection closed.")

# --- Include Routers ---
app.include_router(crm.router)
app.include_router(whatsapp.router)

logger.info("FastAPI application configured.")
