from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import User
from app.services.auth_service import hash_password, verify_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_login(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/auth/login", status_code=303)
    return user


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    if isinstance(user, RedirectResponse):
        return user
    
    db_user = db.query(User).filter(User.id == user["id"]).first()
    return templates.TemplateResponse(
        "profile/edit.html",
        {"request": request, "user_data": db_user}
    )


@router.post("/profile/update")
async def update_profile(
    request: Request,
    name: str = Form(...),
    student_id: str = Form(None),
    phone: str = Form(None),
    db: Session = Depends(get_db)
):
    user = require_login(request)
    if isinstance(user, RedirectResponse):
        return user
    
    db_user = db.query(User).filter(User.id == user["id"]).first()
    if db_user:
        db_user.name = name.strip()
        db_user.student_id = student_id.strip() if student_id else None
        db_user.phone = phone.strip() if phone else None
        db.commit()
        
        request.session["user"]["name"] = db_user.name
        request.session.modified = True
    
    return RedirectResponse(url="/profile?msg=Profil berhasil diperbarui", status_code=303)


@router.post("/profile/change-password")
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
    db: Session = Depends(get_db)
):
    user = require_login(request)
    if isinstance(user, RedirectResponse):
        return user
    
    db_user = db.query(User).filter(User.id == user["id"]).first()
    if not db_user or not verify_password(old_password, db_user.password_hash):
        return RedirectResponse(url="/profile?error=Password lama salah", status_code=303)
    
    if new_password != new_password_confirm:
        return RedirectResponse(url="/profile?error=Password baru tidak cocok", status_code=303)
    
    db_user.password_hash = hash_password(new_password)
    db.commit()
    
    return RedirectResponse(url="/profile?msg=Password berhasil diubah", status_code=303)


@router.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    
    db_user = db.query(User).filter(User.id == user["id"]).first()
    return templates.TemplateResponse(
        "admin/settings.html",
        {"request": request, "user_data": db_user}
    )


@router.post("/admin/settings/update")
async def admin_settings_update(
    request: Request,
    name: str = Form(...),
    phone: str = Form(None),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    
    db_user = db.query(User).filter(User.id == user["id"]).first()
    if db_user:
        db_user.name = name.strip()
        db_user.phone = phone.strip() if phone else None
        db.commit()
        
        request.session["user"]["name"] = db_user.name
        request.session.modified = True
    
    return RedirectResponse(url="/admin/settings?msg=Pengaturan berhasil diperbarui", status_code=303)
