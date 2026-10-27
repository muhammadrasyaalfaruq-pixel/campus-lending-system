import os
from datetime import date, datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
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


@router.post("/admin/loans/{loan_id}/return")
async def return_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    if not request.session.get("user") or request.session["user"]["role"] != "admin":
        return RedirectResponse(url="/auth/login", status_code=303)
    loan = db.get(Loan, loan_id)
    if not loan or loan.status != "borrowed":
        raise HTTPException(status_code=400, detail="Loan not borrowed")
    # Process each detail
    total_fine = 0
    for detail in loan.details:
        item = db.get(Item, detail.item_id)
        # Restore stock
        item.available_stock += detail.return_quantity or detail.quantity
        # Calculate late days
        today = date.today()
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
