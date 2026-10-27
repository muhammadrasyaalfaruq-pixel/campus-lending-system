from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import User, Role
from app.services.auth_service import hash_password, verify_password
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
async def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    student_id: str = Form(None),
    phone: str = Form(None),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != password_confirm:
        return templates.TemplateResponse("auth/register.html", {
            "request": request, 
            "error": "Password tidak cocok"
        })

    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse("auth/register.html", {
            "request": request, 
            "error": "Email sudah terdaftar"
        })

    # Get default role (user)
    role = db.query(Role).filter(Role.name == "user").first()
    if not role:
        # Create roles if not exist
        admin_role = Role(name="admin")
        user_role = Role(name="user")
        db.add(admin_role)
        db.add(user_role)
        db.commit()
        role = user_role

    new_user = User(
        name=name,
        email=email,
        student_id=student_id,
        phone=phone,
        password_hash=hash_password(password),
        role_id=role.id
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse(url="/auth/login?msg=Registrasi berhasil, silakan login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, msg: str = None):
    return templates.TemplateResponse("auth/login.html", {"request": request, "msg": msg})


@router.post("/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse("auth/login.html", {
            "request": request, 
            "error": "Email atau password salah"
        })

    # Set session
    request.session["user"] = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.name
    }

    if user.role.name == "admin":
        return RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
