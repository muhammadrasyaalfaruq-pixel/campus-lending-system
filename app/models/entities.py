from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Text, DateTime, Date, ForeignKey, 
    Numeric, Boolean, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    student_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    role: Mapped["Role"] = relationship(back_populates="users")
    loans: Mapped[List["Loan"]] = relationship(
        "Loan", back_populates="user", foreign_keys="Loan.user_id"
    )
    approved_loans: Mapped[List["Loan"]] = relationship(
        "Loan", back_populates="approver", foreign_keys="Loan.approved_by"
    )
    notifications: Mapped[List["Notification"]] = relationship(back_populates="user")


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    items: Mapped[List["Item"]] = relationship(back_populates="category")


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_stock: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    available_stock: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    condition: Mapped[str] = mapped_column(String(50), default="Baik")  # Baik, Rusak Ringan, Rusak Berat
    image_path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    category: Mapped["Category"] = relationship(back_populates="items")
    loan_details: Mapped[List["LoanDetail"]] = relationship(back_populates="item")


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    loan_code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    borrow_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="pending"
    )  # pending, approved, rejected, borrowed, returned, overdue
    admin_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="loans")
    approver: Mapped[Optional["User"]] = relationship("User", foreign_keys=[approved_by], back_populates="approved_loans")
    details: Mapped[List["LoanDetail"]] = relationship(back_populates="loan", cascade="all, delete-orphan")


class LoanDetail(Base):
    __tablename__ = "loan_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    loan_id: Mapped[int] = mapped_column(ForeignKey("loans.id"), nullable=False)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    returned_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    condition_before: Mapped[str] = mapped_column(String(50), default="Baik")
    condition_after: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    return_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    return_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    loan: Mapped["Loan"] = relationship(back_populates="details")
    item: Mapped["Item"] = relationship(back_populates="loan_details")
    fine: Mapped[Optional["Fine"]] = relationship(back_populates="loan_detail", uselist=False)


class Fine(Base):
    __tablename__ = "fines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    loan_detail_id: Mapped[int] = mapped_column(ForeignKey("loan_details.id"), unique=True, nullable=False)
    days_late: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rate_per_day: Mapped[float] = mapped_column(Numeric(10, 2), default=5000.0, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), default="unpaid")  # unpaid, paid
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    loan_detail: Mapped["LoanDetail"] = relationship(back_populates="fine")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    loan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("loans.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="notifications")
