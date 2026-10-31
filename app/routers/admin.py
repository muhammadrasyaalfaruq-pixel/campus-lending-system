import io
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.entities import Category, Item, Loan, LoanDetail, Role, User
from app.services.auth_service import hash_password

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    user = request.session.get("user")
    if not user or user.get("role") != "admin":
        return None
    return user

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)

    stats = {
        "users": db.query(User).count(),
        "items_count": db.query(Item).count(),
        "categories_count": db.query(Category).count(),
        "pending_loans": db.query(Loan).filter(Loan.status == "pending").count(),
        "approved_loans": db.query(Loan).filter(Loan.status == "approved").count(),
        "borrowed_loans": db.query(Loan).filter(Loan.status == "borrowed").count(),
        "returned_loans": db.query(Loan).filter(Loan.status == "returned").count(),
        "overdue_loans": db.query(Loan).filter(Loan.status == "overdue").count(),
        "rejected_loans": db.query(Loan).filter(Loan.status == "rejected").count(),
        "total_loans": db.query(Loan).count(),
    }
    recent_loans = (
        db.query(Loan)
        .options(joinedload(Loan.user))
        .order_by(Loan.created_at.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "stats": stats, "recent_loans": recent_loans},
    )

# ── Users management ──────────────────────────────────────────────────────────

@router.get("/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    users = db.query(User).options(joinedload(User.role)).order_by(User.created_at.desc()).all()
    roles = db.query(Role).order_by(Role.name).all()
    return templates.TemplateResponse(
        "admin/users.html",
        {"request": request, "users": users, "roles": roles},
    )

@router.post("/users")
async def create_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    student_id: str = Form(""),
    phone: str = Form(""),
    password: str = Form(...),
    role_id: int = Form(...),
    db: Session = Depends(get_db),
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    if not db.query(User).filter(User.email == email.strip()).first():
        db.add(User(
            name=name.strip(),
            email=email.strip(),
            student_id=student_id.strip() or None,
            phone=phone.strip() or None,
            password_hash=hash_password(password),
            role_id=role_id,
        ))
        db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_page(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    user = db.get(User, user_id)
    if not user:
        return RedirectResponse("/admin/users", status_code=303)
    roles = db.query(Role).order_by(Role.name).all()
    return templates.TemplateResponse(
        "admin/user_edit.html",
        {"request": request, "user": user, "roles": roles},
    )

@router.post("/users/{user_id}/update")
async def update_user(
    user_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    student_id: str = Form(""),
    phone: str = Form(""),
    role_id: int = Form(...),
    new_password: str = Form(""),
    db: Session = Depends(get_db),
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    user = db.get(User, user_id)
    if not user:
        return RedirectResponse("/admin/users", status_code=303)
    duplicate = db.query(User).filter(User.email == email.strip(), User.id != user_id).first()
    if duplicate:
        return RedirectResponse("/admin/users", status_code=303)
    user.name = name.strip()
    user.email = email.strip()
    user.student_id = student_id.strip() or None
    user.phone = phone.strip() or None
    user.role_id = role_id
    if new_password.strip():
        user.password_hash = hash_password(new_password.strip())
    db.commit()
    # Refresh session if editing self
    if request.session.get("user", {}).get("id") == user_id:
        request.session["user"]["name"] = user.name
        request.session["user"]["email"] = user.email
    return RedirectResponse("/admin/users", status_code=303)

@router.post("/users/{user_id}/delete")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    # Prevent self-delete
    if request.session.get("user", {}).get("id") == user_id:
        return RedirectResponse("/admin/users", status_code=303)
    user = db.get(User, user_id)
    if user and not user.loans:
        db.delete(user)
        db.commit()
    return RedirectResponse("/admin/users", status_code=303)

# ── Roles management ──────────────────────────────────────────────────────────

@router.post("/roles")
async def create_role(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    name = name.strip()
    if name and not db.query(Role).filter(Role.name == name).first():
        db.add(Role(name=name))
        db.commit()
    return RedirectResponse("/admin/users", status_code=303)

@router.post("/roles/{role_id}/delete")
async def delete_role(role_id: int, request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)
    role = db.get(Role, role_id)
    if role and not role.users:
        db.delete(role)
        db.commit()
    return RedirectResponse("/admin/users", status_code=303)

# ── PDF report ────────────────────────────────────────────────────────────────

@router.get("/reports/loans/pdf")
async def export_loans_pdf(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)

    loans = (
        db.query(Loan)
        .options(joinedload(Loan.user), joinedload(Loan.details).joinedload(LoanDetail.item))
        .order_by(Loan.created_at.desc())
        .all()
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Laporan Riwayat Peminjaman - PinjamKampus</b>", styles["Title"]))
    elements.append(Spacer(1, 15))

    data = [["Kode", "Peminjam", "Tgl Pinjam", "Batas Kembali", "Tgl Kembali", "Status", "Alat & Qty"]]
    for loan in loans:
        items_str = ", ".join([f"{d.item.name} ({d.quantity})" for d in loan.details]) if loan.details else "-"
        # actual return = latest detail return_date that is set
        detail_dates = [d.return_date for d in loan.details if d.return_date]
        actual_ret = max(detail_dates).strftime("%d-%m-%Y") if detail_dates else "-"
        due_date = loan.due_date.strftime("%d-%m-%Y") if loan.due_date else "-"
        borrow_date = loan.borrow_date.strftime("%d-%m-%Y") if loan.borrow_date else "-"
        data.append([
            loan.loan_code,
            loan.user.name if loan.user else "-",
            borrow_date,
            due_date,
            actual_ret,
            loan.status.upper(),
            items_str,
        ])

    table = Table(data, colWidths=[100, 120, 75, 85, 75, 70, 245])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ])
    )
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=laporan-peminjaman.pdf"},
    )
