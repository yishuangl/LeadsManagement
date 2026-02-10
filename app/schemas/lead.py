import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.lead import LeadStatus


class LeadCreate(BaseModel):
    first_name: str
    last_name: str
    email: str


class LeadUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    status: LeadStatus | None = None


class LeadResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    resume_path: str | None
    status: LeadStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
