# filepath: d:\GitHub\asistenteAIEventek\src\crm\data.py
import os
import motor.motor_asyncio
from dotenv import load_dotenv
from bson import ObjectId # For handling MongoDB ObjectIds if needed
import logging

load_dotenv()

logger = logging.getLogger(__name__)

MONGO_DETAILS = os.getenv("MONGODB_CONNECTION_STRING")
if not MONGO_DETAILS:
    logger.error("MONGODB_CONNECTION_STRING not found in environment variables.")
    # Handle the error appropriately, maybe raise an exception or exit
    # For now, we'll let it proceed, but connection will fail
    client = None
    db = None
else:
    try:
        client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
        # Replace 'crm_database' with your actual database name
        db = client.crm_database
        logger.info("Successfully connected to MongoDB.")
        # Example: Get a reference to a collection named 'contacts'
        contact_collection = db.get_collection("contacts")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        client = None
        db = None
        contact_collection = None # Ensure it's None if connection fails

# Helper function to parse MongoDB ObjectId to string
def contact_helper(contact) -> dict:
    return {
        "id": str(contact["_id"]),
        "name": contact.get("name"),
        "email": contact.get("email"),
        "phone": contact.get("phone"),
        # Add other fields as needed
    }

# Example function to retrieve all contacts
async def retrieve_contacts():
    contacts = []
    if contact_collection is not None:
        async for contact in contact_collection.find():
            contacts.append(contact_helper(contact))
    else:
        logger.warning("Contact collection is not available. Cannot retrieve contacts.")
    return contacts

# Example function to add a new contact (you'll need data validation later)
async def add_contact(contact_data: dict) -> dict:
    if contact_collection is not None:
        contact = await contact_collection.insert_one(contact_data)
        new_contact = await contact_collection.find_one({"_id": contact.inserted_id})
        return contact_helper(new_contact)
    else:
        logger.warning("Contact collection is not available. Cannot add contact.")
        return None # Or raise an error