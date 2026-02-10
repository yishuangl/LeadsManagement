import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import CurrentUser, DbSession
from app.services import lead_service
from app.services.file_service import get_resume_path

templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request, db: DbSession, user: CurrentUser):
    leads = await lead_service.get_leads(db)
    return templates.TemplateResponse(
        "dashboard/lead_list.html",
        {"request": request, "leads": leads},
    )


@router.post("/leads/{lead_id}/reach-out", response_class=HTMLResponse)
async def mark_reached_out(
    lead_id: uuid.UUID, request: Request, db: DbSession, user: CurrentUser
):
    lead = await lead_service.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = await lead_service.mark_reached_out(db, lead)
    return templates.TemplateResponse(
        "dashboard/lead_row.html",
        {"request": request, "lead": lead},
    )


@router.get("/leads/{lead_id}/resume")
async def download_resume(lead_id: uuid.UUID, db: DbSession, user: CurrentUser):
    lead = await lead_service.get_lead(db, lead_id)
    if lead is None or lead.resume_path is None:
        raise HTTPException(status_code=404, detail="Resume not found")
    file_path = get_resume_path(lead.resume_path)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Resume file not found")
    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )
