from datetime import datetime, date
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import io

from app.database import get_db
from app.models.entities import Loan, LoanDetail, Item, User, Fine, Category

router = APIRouter(prefix="/reports", tags=["Reports"])
templates = Jinja2Templates(directory="app/templates")

def get_admin_user(request: Request, db: Session):
    user_data = request.session.get("user")
    if not user_data:
        return None
    user = db.get(User, user_data["id"])
    if not user or user.role.name != "admin":
        return None
    return user

@router.get("/loans", response_class=HTMLResponse)
async def report_loans_page(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Akses khusus admin")
    loans = db.query(Loan).options(joinedload(Loan.user), joinedload(Loan.details).joinedload(LoanDetail.item)).order_by(Loan.created_at.desc()).all()
    return templates.TemplateResponse("reports/loans_report.html", {"request": request, "loans": loans})

@router.get("/stock", response_class=HTMLResponse)
async def report_stock_page(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Akses khusus admin")
    items = db.query(Item).options(joinedload(Item.category)).order_by(Item.name).all()
    return templates.TemplateResponse("reports/stock_report.html", {"request": request, "items": items})

@router.get("/fines", response_class=HTMLResponse)
async def report_fines_page(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Akses khusus admin")
    fines = db.query(Fine).options(joinedload(Fine.loan_detail).joinedload(LoanDetail.loan).joinedload(Loan.user)).all()
    return templates.TemplateResponse("reports/fines_report.html", {"request": request, "fines": fines})

@router.get("/export/loans-pdf")
async def export_loans_pdf(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Akses khusus admin")
    
    loans = db.query(Loan).options(joinedload(Loan.user)).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Laporan Rekapitulasi Peminjaman - PinjamKampus</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    data = [["ID", "Kode Pinjam", "Peminjam", "Tanggal Pinjam", "Batas Kembali", "Status"]]
    for l in loans:
        data.append([str(l.id), l.loan_code, l.user.name, l.borrow_date.strftime("%d-%m-%Y"), l.due_date.strftime("%d-%m-%Y"), l.status])

    table = Table(data, colWidths=[40, 150, 180, 100, 100, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Laporan_Peminjaman.pdf"})

@router.get("/export/stock-pdf")
async def export_stock_pdf(request: Request, db: Session = Depends(get_db)):
    user = get_admin_user(request, db)
    if not user:
        raise HTTPException(status_code=403, detail="Akses khusus admin")
    
    items = db.query(Item).options(joinedload(Item.category)).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("<b>Laporan Inventaris Barang - PinjamKampus</b>", styles["Title"]))
    elements.append(Spacer(1, 10))

    data = [["Kode", "Nama Barang", "Kategori", "Total Stok", "Tersedia", "Kondisi"]]
    for i in items:
        data.append([i.code, i.name, i.category.name if i.category else "-", str(i.total_stock), str(i.available_stock), i.condition])

    table = Table(data, colWidths=[100, 220, 140, 80, 80, 110])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#198754")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return Response(content=buffer.getvalue(), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=Laporan_Inventaris.pdf"})
