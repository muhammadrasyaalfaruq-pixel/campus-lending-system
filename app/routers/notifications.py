from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Notification, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/notifications", response_class=HTMLResponse)
async def list_notifications(request: Request, db: Session = Depends(get_db)):
    user_data = request.session.get("user")
    if not user_data:
        return RedirectResponse("/auth/login", status_code=303)
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == user_data["id"])
        .order_by(Notification.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "notifications/index.html",
        {"request": request, "notifications": notifs},
    )


@router.post("/notifications/{notif_id}/read")
async def mark_read(notif_id: int, request: Request, db: Session = Depends(get_db)):
    user_data = request.session.get("user")
    if not user_data:
        return RedirectResponse("/auth/login", status_code=303)
    notif = db.get(Notification, notif_id)
    if notif and notif.user_id == user_data["id"]:
        notif.is_read = True
        db.commit()
    return RedirectResponse("/notifications", status_code=303)
