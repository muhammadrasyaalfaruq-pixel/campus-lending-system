from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    student_id: Optional[str] = None
    phone: Optional[str] = None
    password: str
    password_confirm: str

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Budi Santoso",
                "email": "budi@campus.ac.id",
                "student_id": "2024001",
                "phone": "081234567890",
                "password": "password123",
                "password_confirm": "password123"
            }
        }


class UserLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "budi@campus.ac.id",
                "password": "password123"
            }
        }


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role_id: int
    student_id: Optional[str] = None
    phone: Optional[str] = None

    class Config:
        from_attributes = True
