import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="PinjamKampus")

# Session secret for flash messages, CSRF, etc.
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change-me"))

# Mount static files (CSS, JS, uploads)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

from app.routers import auth, admin, items, loans, notifications, profile, reports
app.include_router(auth.router, prefix="/auth")
app.include_router(admin.router, prefix="/admin")
app.include_router(reports.router)
app.include_router(items.router)
app.include_router(loans.router)
app.include_router(notifications.router)
app.include_router(profile.router)
# app.include_router(items.router, prefix="/items")
# app.include_router(loans.router, prefix="/loans")
# app.include_router(admin.router, prefix="/admin")
