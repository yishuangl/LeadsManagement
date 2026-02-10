from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.dependencies import DbSession, get_current_user
from app.services.auth_service import authenticate_user, create_user

templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(request: Request, db: DbSession):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    user = await authenticate_user(db, str(username), str(password))
    if user is None:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"},
            status_code=401,
        )
    request.session["user_id"] = str(user.id)
    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
async def signup(request: Request, db: DbSession):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    user = await create_user(db, str(username), str(password))
    if user is None:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Username already taken"},
            status_code=409,
        )
    request.session["user_id"] = str(user.id)
    return RedirectResponse(url="/dashboard", status_code=303)


@router.post("/logout", dependencies=[Depends(get_current_user)])
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/auth/login", status_code=303)
