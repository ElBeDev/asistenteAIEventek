import motor.motor_asyncio
import logging
from .config import settings # Import settings to get the connection string

logger = logging.getLogger(__name__)

# Global variables to hold the client and database instances
client: motor.motor_asyncio.AsyncIOMotorClient | None = None
db: motor.motor_asyncio.AsyncIOMotorDatabase | None = None

async def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """
    Initializes the MongoDB connection if not already established
    and returns the database object.
    """
    global client, db
    if db is None:
        if not settings.MONGODB_CONNECTION_STRING:
            logger.error("MONGODB_CONNECTION_STRING is not set in the environment variables.")
            raise ValueError("MongoDB connection string is missing.")

        logger.info("Initializing MongoDB connection...")
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_CONNECTION_STRING)
            # Extract database name from connection string if present, otherwise default
            # A simple way is to assume the last part of the path is the DB name
            db_name = settings.MONGODB_CONNECTION_STRING.split('/')[-1].split('?')[0]
            if not db_name: # Default if parsing fails or not specified
                db_name = "eventek"
                logger.warning(f"Database name not found in connection string, defaulting to '{db_name}'.")

            db = client[db_name] # Get the database object
            # You can optionally add a check here to ensure connection works, e.g., client.admin.command('ping')
            await client.admin.command('ping') # Verify connection
            logger.info(f"Successfully connected to MongoDB database: '{db_name}'")
        except Exception as e:
            logger.exception(f"Failed to connect to MongoDB: {e}")
            # Reset globals on failure
            client = None
            db = None
            raise # Re-raise the exception to signal connection failure

    if db is None: # Should not happen if logic above is correct, but safety check
         raise RuntimeError("Database connection could not be established.")

    return db

async def close_db():
    """Closes the MongoDB connection."""
    global client, db
    if client:
        logger.info("Closing MongoDB connection...")
        client.close()
        client = None
        db = None
        logger.info("MongoDB connection closed.")

# Example of how to get a specific collection (optional helper)
# def get_contacts_collection():
#     if db is None:
#         raise RuntimeError("Database not initialized. Call get_db first.")
#     return db["contacts"]