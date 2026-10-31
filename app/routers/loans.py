import io
import os
from datetime import date, datetime, timedelta
from typing import List

import qrcode
from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.entities import Loan, LoanDetail, Item, User, Notification, Fine

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

MAX_ACTIVE_LOANS = int(os.getenv("MAX_ACTIVE_LOANS_PER_USER", "3"))
FINE_RATE = int(os.getenv("FINE_RATE_PER_DAY", "5000"))


def current_user(request: Request, db: Session) -> User | None:
    user_data = request.session.get("user")
    if not user_data:
        return None
    return db.get(User, user_data["id"])


@router.get("/loans/my", response_class=HTMLResponse)
async def my_loans(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    loans = (
        db.query(Loan)
        .options(joinedload(Loan.details).joinedload(LoanDetail.item))
        .filter(Loan.user_id == user.id)
        .order_by(Loan.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "loans/my_loans.html",
        {"request": request, "loans": loans},
    )

@router.get("/loans/{loan_id}/qr")
async def loan_qr(loan_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login diperlukan")

    loan = db.get(Loan, loan_id)
    if not loan or (loan.user_id != user.id and user.role.name != "admin"):
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status not in ("approved", "borrowed"):
        raise HTTPException(status_code=400, detail="QR hanya tersedia untuk pinjaman disetujui atau aktif")

    ticket_url = str(request.url_for("loan_ticket", loan_code=loan.loan_code))
    qr = qrcode.make(ticket_url)
    output = io.BytesIO()
    qr.save(output, format="PNG")
    output.seek(0)
    return StreamingResponse(output, media_type="image/png", headers={"Cache-Control": "no-store"})

@router.get("/loans/ticket/{loan_code}", response_class=HTMLResponse, name="loan_ticket")
async def loan_ticket(loan_code: str, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    loan = (
        db.query(Loan)
        .options(joinedload(Loan.user), joinedload(Loan.details).joinedload(LoanDetail.item))
        .filter(Loan.loan_code == loan_code)
        .first()
    )
    if not loan or (loan.user_id != user.id and user.role.name != "admin"):
        raise HTTPException(status_code=404, detail="Loan not found")

    return templates.TemplateResponse(
        "loans/ticket.html",
        {"request": request, "loan": loan},
    )

@router.get("/loans/{loan_id}/return-pdf")
async def user_return_pdf(loan_id: int, request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    loan = db.get(Loan, loan_id)
    if not loan or (loan.user_id != user.id and user.role.name != "admin"):
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status != "returned":
        raise HTTPException(status_code=400, detail="Bukti PDF hanya untuk pinjaman yang sudah dikembalikan")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(f"<b>Bukti Pengembalian Alat - {loan.loan_code}</b>", styles["Title"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Peminjam: {loan.user.name} | Tanggal Pinjam: {loan.borrow_date.strftime('%d-%m-%Y')} | Batas Kembali: {loan.due_date.strftime('%d-%m-%Y')}", styles["Normal"]))
    elements.append(Spacer(1, 15))

    data = [["Item", "Jumlah", "Kondisi Awal", "Kondisi Akhir", "Tanggal Kembali"]]
    for d in loan.details:
        data.append([
            d.item.name,
            str(d.quantity),
            d.condition_before or "Baik",
            d.condition_after or "Baik",
            d.return_date.strftime("%d-%m-%Y") if d.return_date else "-",
        ])

    table = Table(data, colWidths=[220, 60, 120, 120, 110])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
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
        headers={"Content-Disposition": f"attachment; filename=Bukti_{loan.loan_code}.pdf"},
    )

@router.get("/loans/request", response_class=HTMLResponse)
async def loan_form(request: Request, db: Session = Depends(get_db)):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    # Filter items with stock > 0
    items = db.query(Item).filter(Item.available_stock > 0).order_by(Item.name).all()
    return templates.TemplateResponse(
        "loans/request.html",
        {"request": request, "items": items},
    )


@router.post("/loans/request")
async def submit_loan(
    request: Request,
    item_ids: List[int] = Form(...),
    quantities: List[int] = Form(...),
    purpose: str = Form(...),
    db: Session = Depends(get_db),
):
    user = current_user(request, db)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)
    # Active loan limit
    active = db.query(Loan).filter(Loan.user_id == user.id, Loan.status.in_(["pending", "approved", "borrowed"]))
    if active.count() >= MAX_ACTIVE_LOANS:
        raise HTTPException(status_code=400, detail="Melebihi batas pinjaman aktif.")

    # Build loan details
    details = []
    for item_id, qty in zip(item_ids, quantities):
        item = db.get(Item, item_id)
        if not item or item.available_stock < qty:
            raise HTTPException(status_code=400, detail=f"Stok tidak cukup untuk {item.name if item else 'item'}.")
        details.append((item, qty))

    # Create loan record
    loan = Loan(
        user_id=user.id,
        loan_code=f"LN{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{user.id}",
        purpose=purpose,
        borrow_date=date.today(),
        due_date=date.today() + timedelta(days=7),
        status="pending",
    )
    db.add(loan)
    db.flush()  # get loan.id
    for item, qty in details:
        loan_detail = LoanDetail(
            loan_id=loan.id,
            item_id=item.id,
            quantity=qty,
            condition_before=item.condition,
        )
        db.add(loan_detail)
        # Reduce available stock immediately (optimistic)
        item.available_stock -= qty
    db.commit()

    # Notify admin
    admin_users = db.query(User).join(User.role).filter(User.role.has(name="admin")).all()
    for admin in admin_users:
        db.add(
            Notification(
                user_id=admin.id,
                loan_id=loan.id,
                title="Pengajuan pinjaman baru",
                message=f"{user.name} mengajukan pinjaman {loan.loan_code}.",
            )
        )
    db.commit()
    return RedirectResponse(url="/loans/my", status_code=303)


@router.get("/admin/loans", response_class=HTMLResponse)
async def admin_loans(request: Request, db: Session = Depends(get_db)):
    # Admin only
    if not request.session.get("user") or request.session["user"]["role"] != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    loans = (
        db.query(Loan)
        .options(joinedload(Loan.user), joinedload(Loan.details).joinedload(LoanDetail.item))
        .order_by(Loan.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "admin/loans.html",
        {"request": request, "loans": loans},
    )


@router.post("/admin/loans/{loan_id}/approve")
async def approve_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user") or request.session["user"]["role"] != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    loan = db.get(Loan, loan_id)
    if not loan or loan.status != "pending":
        raise HTTPException(status_code=400, detail="Loan not pending")
    loan.status = "approved"
    loan.approved_by = request.session["user"]["id"]
    db.commit()
    # Notify borrower
    db.add(
        Notification(
            user_id=loan.user_id,
            loan_id=loan.id,
            title="Pinjaman disetujui",
            message=f"Pengajuan {loan.loan_code} telah disetujui. Silakan ambil barang.",
        )
    )
    db.commit()
    return RedirectResponse(url="/admin/loans", status_code=303)


@router.post("/admin/loans/{loan_id}/reject")
async def reject_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user") or request.session["user"]["role"] != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    loan = db.get(Loan, loan_id)
    if not loan or loan.status != "pending":
        raise HTTPException(status_code=400, detail="Loan not pending")
    loan.status = "rejected"
    loan.approved_by = request.session["user"]["id"]
    # Restore stock
    for detail in loan.details:
        item = db.get(Item, detail.item_id)
        item.available_stock += detail.quantity
    db.commit()
    # Notify borrower
    db.add(
        Notification(
            user_id=loan.user_id,
            loan_id=loan.id,
            title="Pinjaman ditolak",
            message=f"Pengajuan {loan.loan_code} ditolak.",
        )
    )
    db.commit()
    return RedirectResponse(url="/admin/loans", status_code=303)


@router.post("/admin/loans/{loan_id}/borrow")
async def borrow_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user") or request.session["user"]["role"] != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    loan = db.get(Loan, loan_id)
    if not loan or loan.status != "approved":
        raise HTTPException(status_code=400, detail="Loan not approved")
    loan.status = "borrowed"
    db.commit()
    db.add(
        Notification(
            user_id=loan.user_id,
            loan_id=loan.id,
            title="Barang telah diserahkan",
            message=f"Peminjaman {loan.loan_code} aktif. Harap kembalikan sebelum {loan.due_date.strftime('%d-%m-%Y')}.",
        )
    )
    db.commit()
    return RedirectResponse(url="/admin/loans", status_code=303)


@router.post("/admin/loans/{loan_id}/return")
async def return_loan(
    loan_id: int,
    request: Request,
    condition_after: List[str] = Form(...),
    return_notes: List[str] = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("user") or request.session["user"]["role"] != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    loan = db.get(Loan, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.status != "borrowed":
        raise HTTPException(status_code=400, detail="Loan not borrowed")
    if len(condition_after) != len(loan.details) or len(return_notes) != len(loan.details):
        raise HTTPException(status_code=400, detail="Data pengembalian tidak lengkap")

    total_fine = 0
    today = date.today()
    for detail, final_condition, note in zip(loan.details, condition_after, return_notes):
        item = db.get(Item, detail.item_id)
        detail.returned_quantity = detail.quantity
        detail.return_date = today
        detail.condition_after = final_condition
        detail.return_note = note.strip() or None
        item.available_stock += detail.quantity
        # Calculate late days
        if today > loan.due_date:
            days_late = (today - loan.due_date).days
            fine_amount = days_late * FINE_RATE * detail.quantity
            total_fine += fine_amount
            fine = Fine(
                loan_detail_id=detail.id,
                days_late=days_late,
                rate_per_day=FINE_RATE,
                amount=fine_amount,
                payment_status="unpaid",
            )
            db.add(fine)
    loan.status = "returned"
    db.commit()
    # Notify borrower about fine if any
    if total_fine:
        db.add(
            Notification(
                user_id=loan.user_id,
                loan_id=loan.id,
                title="Denda pengembalian",
                message=f"Pengembalian {loan.loan_code} terlambat. Denda: Rp{total_fine:,}.",
            )
        )
        db.commit()
    return RedirectResponse(url="/admin/loans", status_code=303)
