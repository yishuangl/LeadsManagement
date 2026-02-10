from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.dependencies import DbSession
from app.schemas.lead import LeadCreate
from app.services import lead_service
from app.services.email_service import send_attorney_notification, send_prospect_confirmation
from app.services.file_service import FileValidationError, save_resume

templates = Jinja2Templates(
    directory=Path(__file__).resolve().parent.parent / "templates"
)

router = APIRouter(tags=["public"])


@router.get("/", response_class=HTMLResponse)
async def interest_form(request: Request):
    return templates.TemplateResponse(
        "public/interest_form.html", {"request": request}
    )


@router.post("/submit")
async def submit_interest(
    request: Request,
    background_tasks: BackgroundTasks,
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
            return templates.TemplateResponse(
                "public/interest_form.html",
                {
                    "request": request,
                    "error": str(e),
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                },
                status_code=400,
            )

    data = LeadCreate(first_name=first_name, last_name=last_name, email=email)
    await lead_service.create_lead(db, data, resume_path)

    background_tasks.add_task(send_prospect_confirmation, email, first_name)
    background_tasks.add_task(send_attorney_notification, first_name, last_name, email)

    return RedirectResponse(url="/thank-you", status_code=303)


@router.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    return templates.TemplateResponse("public/thank_you.html", {"request": request})
