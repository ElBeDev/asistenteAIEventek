import os
import logging
from dotenv import load_dotenv
from functools import lru_cache
from pydantic_settings import BaseSettings

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Required settings
    OPENAI_API_KEY: str
    WHATSAPP_TOKEN: str
    PHONE_NUMBER_ID: str
    WEBHOOK_VERIFY_TOKEN: str
    WABA_ID: str  # Changed from waba_id to match env var case

    # Assistant IDs
    MEDICINA_PLEURAL_ASSISTANT_ID: str | None = None  # Will be created if not set

    # Optional settings with defaults
    BASE_URL: str = "http://localhost:5000/api"
    PORT: int = int(os.getenv("PORT", "8080"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ('true', '1', 't')

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # App settings
    APP_NAME: str = "WhatsApp Medicina Pleural Bot"
    APP_VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"
        case_sensitive = True  # Changed to True to match exact case
        extra = "allow"  # Allow extra fields
        
        # Log when settings are loaded
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            logger.info("Loading application settings...")
            return init_settings, env_settings, file_secret_settings

@lru_cache()
def get_settings():
    """Get cached settings instance"""
    settings = Settings()
    
    # Validate critical settings
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY is not set!")
    
    if not settings.WHATSAPP_TOKEN:
        logger.error("WHATSAPP_TOKEN is not set!")
        
    if not settings.PHONE_NUMBER_ID:
        logger.error("PHONE_NUMBER_ID is not set!")
    
    # Log masked versions of sensitive settings
    logger.info(f"OPENAI_API_KEY: {settings.OPENAI_API_KEY[:5]}...{settings.OPENAI_API_KEY[-5:] if settings.OPENAI_API_KEY else ''}")
    logger.info(f"WHATSAPP_TOKEN: {settings.WHATSAPP_TOKEN[:5]}...{settings.WHATSAPP_TOKEN[-5:] if settings.WHATSAPP_TOKEN else ''}")
    logger.info(f"PHONE_NUMBER_ID: {settings.PHONE_NUMBER_ID}")
    
    return settings

# Add this function to config.py
def clear_settings_cache():
    """Clear the settings cache to reload environment variables"""
    get_settings.cache_clear()

# Create a global settings instance
settings = get_settings()