import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.dependencies import CurrentUser, DbSession
from app.schemas.lead import LeadCreate, LeadResponse, LeadUpdate
from app.services import lead_service
from app.services.file_service import FileValidationError, save_resume

router = APIRouter(prefix="/api/leads", tags=["api"])


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
async def create_lead(
    db: DbSession,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    resume: UploadFile | None = File(None),
):
    resume_path = None
    if resume and resume.filename:
        try:
            resume_path = await save_resume(resume)
        except FileValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

    data = LeadCreate(first_name=first_name, last_name=last_name, email=email)
    lead = await lead_service.create_lead(db, data, resume_path)
    return lead


@router.get("", response_model=list[LeadResponse])
async def list_leads(db: DbSession, user: CurrentUser):
    return await lead_service.get_leads(db)


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: uuid.UUID, db: DbSession, user: CurrentUser):
    lead = await lead_service.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: uuid.UUID, data: LeadUpdate, db: DbSession, user: CurrentUser
):
    lead = await lead_service.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    return await lead_service.update_lead(db, lead, data)
