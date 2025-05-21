from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, date
import logging
import traceback
from pydantic import BaseModel, Field, EmailStr, ValidationError, field_validator
from typing import Optional, List

# Assuming db, config, assistant_logic are in the parent directory 'src'
from ..db import get_db
from ..config import settings # If needed by CRM logic, otherwise remove

logger = logging.getLogger(__name__)

# Setup templates
templates = Jinja2Templates(directory="src/templates")

router = APIRouter(
    tags=["CRM"], # Optional tag for API docs
)

# --- Pydantic Models for CRM ---
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class ContactSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(...)
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    event_type: Optional[str] = None
    event_date: Optional[datetime] = None # Store as datetime
    attendees: Optional[int] = None
    plan_interest: Optional[str] = None
    notes: Optional[str] = None
    added_on: datetime = Field(default_factory=datetime.now)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True # Needed for ObjectId
        json_encoders = {ObjectId: str}

# --- CRM Endpoints ---

@router.get("/", response_class=HTMLResponse, summary="CRM Dashboard", name="crm_dashboard_page")
async def crm_dashboard(request: Request, database: AsyncIOMotorDatabase = Depends(get_db)):
    """Serves the main CRM dashboard page, fetching contacts from the database."""
    try:
        contacts_cursor = database.contacts.find().sort("added_on", -1)
        contacts_list = await contacts_cursor.to_list(length=100) # Limit to 100 contacts for display
        # Validate data before sending to template
        contacts_models = []
        for c in contacts_list:
            try:
                contacts_models.append(ContactSchema.model_validate(c))
            except ValidationError as e:
                logger.warning(f"Skipping contact due to validation error: {c.get('_id', 'N/A')} - {e}")
                continue # Skip contacts that don't match the schema

    except Exception as e:
        logger.error(f"Error fetching contacts from DB for dashboard: {e}")
        logger.error(traceback.format_exc())
        contacts_models = [] # Ensure it's an empty list on error

    return templates.TemplateResponse("crm_dashboard.html", {
        "request": request,
        "contacts": contacts_models
    })

@router.post("/add_contact", summary="Add New Contact to MongoDB", name="add_contact")
async def add_contact_entry(request: Request, database: AsyncIOMotorDatabase = Depends(get_db)):
    """Handles form submission to add a new contact."""
    try:
        form_data = await request.form()
        logger.debug(f"Received form data: {form_data}")

        attendees_str = form_data.get("attendees")
        attendees_int = int(attendees_str) if attendees_str and attendees_str.isdigit() else None

        event_date_str = form_data.get("event_date")
        event_date_obj = None
        if event_date_str:
            try:
                parsed_date = date.fromisoformat(event_date_str)
                event_date_obj = datetime.combine(parsed_date, datetime.min.time())
            except ValueError:
                logger.warning(f"Invalid date format received: {event_date_str}")

        contact_data = {
            "name": form_data.get("name"),
            "phone": form_data.get("phone"),
            "email": form_data.get("email"),
            "company": form_data.get("company"),
            "event_type": form_data.get("event_type"),
            "event_date": event_date_obj,
            "attendees": attendees_int,
            "plan_interest": form_data.get("plan_interest"),
            "notes": form_data.get("notes"),
            "added_on": datetime.now()
        }

        # Validate using Pydantic model
        try:
            validated_contact = ContactSchema(**contact_data)
        except ValidationError as e:
            logger.error(f"Contact validation failed: {e}")
            # Ideally, return an error message to the user instead of just redirecting
            # For now, redirect back to the form
            # Consider adding flash messages or similar feedback
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        # Insert into MongoDB - Use model_dump to get dict suitable for DB
        insert_result = await database.contacts.insert_one(validated_contact.model_dump(by_alias=True, exclude={'id'}))
        logger.info(f"Inserted contact with ID: {insert_result.inserted_id}")

        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    except Exception as e:
        logger.error(f"Error adding contact to MongoDB: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Redirect even on error for now, but ideally show an error message
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/api/crm/contacts", response_model=List[ContactSchema], summary="Get All Contacts (API)")
async def get_all_contacts(database: AsyncIOMotorDatabase = Depends(get_db)):
    """API endpoint to retrieve all contacts from the database."""
    try:
        contacts_cursor = database.contacts.find().sort("added_on", -1)
        contacts_list = await contacts_cursor.to_list(length=1000) # Adjust length as needed
        # Validate each contact - Pydantic handles validation via response_model
        return contacts_list
    except Exception as e:
        logger.error(f"Error fetching contacts for API: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch contacts")

# You could add more CRM-specific API endpoints here (e.g., get contact by ID, update, delete)