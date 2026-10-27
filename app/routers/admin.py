import io
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import Category, Item, Loan, User

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
        "items": db.query(Item).count(),
        "categories": db.query(Category).count(),
        "pending_loans": db.query(Loan).filter(Loan.status == "pending").count(),
    }
    recent_loans = db.query(Loan).order_by(Loan.created_at.desc()).limit(5).all()
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "stats": stats, "recent_loans": recent_loans},
    )


@router.get("/reports/loans/pdf")
async def export_loans_pdf(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=303)

    loans = db.query(Loan).order_by(Loan.created_at.desc()).all()

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

    data = [["Kode", "Peminjam", "Tgl Pinjam", "Tgl Rencana Kembali", "Tgl Kembali", "Status", "Alat & Qty"]]
    for loan in loans:
        items_str = ", ".join([f"{d.item.name} ({d.quantity})" for d in loan.details]) if loan.details else "-"
        actual_ret = loan.actual_return_date.strftime("%d-%m-%Y") if loan.actual_return_date else "-"
        ret_date = loan.return_date.strftime("%d-%m-%Y") if loan.return_date else "-"
        borrow_date = loan.borrow_date.strftime("%d-%m-%Y") if loan.borrow_date else "-"
        data.append([
            loan.loan_code,
            loan.user.name if loan.user else "-",
            borrow_date,
            ret_date,
            actual_ret,
            loan.status.upper(),
            items_str,
        ])

    table = Table(data, colWidths=[80, 110, 80, 100, 80, 80, 240])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
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
