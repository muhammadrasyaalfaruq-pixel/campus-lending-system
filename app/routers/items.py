import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.entities import Category, Item

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./app/static/uploads"))
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))


def is_admin(request: Request) -> bool:
    user = request.session.get("user")
    return bool(user and user.get("role") == "admin")


def admin_redirect(request: Request):
    if not is_admin(request):
        return RedirectResponse("/auth/login", status_code=303)
    return None


def save_image(image: UploadFile | None) -> str | None:
    if not image or not image.filename:
        return None

    extension = Path(image.filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Foto harus berformat JPG, JPEG, PNG, atau GIF.")

    content = image.file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        raise ValueError("Ukuran foto maksimal 5 MB.")

    try:
        from io import BytesIO
        opened_image = Image.open(BytesIO(content))
        opened_image.verify()
    except (UnidentifiedImageError, OSError):
        raise ValueError("File foto tidak valid.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / filename
    file_path.write_bytes(content)
    return f"/static/uploads/{filename}"


def delete_image(image_path: str | None) -> None:
    if not image_path or not image_path.startswith("/static/uploads/"):
        return
    file_path = Path("app") / image_path.removeprefix("/static/")
    if file_path.is_file():
        file_path.unlink()


@router.get("/items", response_class=HTMLResponse)
@router.get("/items/", response_class=HTMLResponse)
async def item_catalog(request: Request, category: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Item).options(joinedload(Item.category)).order_by(Item.name)
    if category:
        query = query.filter(Item.category_id == category)
    return templates.TemplateResponse(
        "items/catalog.html",
        {
            "request": request,
            "items": query.all(),
            "categories": db.query(Category).order_by(Category.name).all(),
            "selected_category": category,
        },
    )


@router.get("/admin/items", response_class=HTMLResponse)
async def manage_items(request: Request, db: Session = Depends(get_db)):
    if redirect := admin_redirect(request):
        return redirect
    return templates.TemplateResponse(
        "admin/items.html",
        {
            "request": request,
            "items": db.query(Item).options(joinedload(Item.category)).order_by(Item.name).all(),
            "categories": db.query(Category).order_by(Category.name).all(),
        },
    )


@router.post("/admin/categories")
async def create_category(request: Request, name: str = Form(...), description: str = Form(""), db: Session = Depends(get_db)):
    if redirect := admin_redirect(request):
        return redirect
    name = name.strip()
    if name and not db.query(Category).filter(Category.name == name).first():
        db.add(Category(name=name, description=description.strip() or None))
        db.commit()
    return RedirectResponse("/admin/items", status_code=303)


@router.post("/admin/categories/{category_id}/update")
async def update_category(
    category_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    if redirect := admin_redirect(request):
        return redirect
    category = db.get(Category, category_id)
    if not category:
        return RedirectResponse("/admin/items", status_code=303)
    name = name.strip()
    duplicate = db.query(Category).filter(Category.name == name, Category.id != category_id).first()
    if name and not duplicate:
        category.name = name
        category.description = description.strip() or None
        db.commit()
    return RedirectResponse("/admin/items", status_code=303)

@router.post("/admin/categories/{category_id}/delete")
async def delete_category(category_id: int, request: Request, db: Session = Depends(get_db)):
    if redirect := admin_redirect(request):
        return redirect
    category = db.get(Category, category_id)
    if category and not category.items:
        db.delete(category)
        db.commit()
    return RedirectResponse("/admin/items", status_code=303)


@router.post("/admin/items")
async def create_item(
    request: Request,
    category_id: int = Form(...),
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    total_stock: int = Form(...),
    condition: str = Form("Baik"),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    if redirect := admin_redirect(request):
        return redirect
    if total_stock < 0 or not db.get(Category, category_id):
        return RedirectResponse("/admin/items", status_code=303)
    if db.query(Item).filter(Item.code == code.strip()).first():
        return RedirectResponse("/admin/items", status_code=303)
    try:
        image_path = save_image(image)
    except ValueError:
        return RedirectResponse("/admin/items", status_code=303)
    db.add(Item(
        category_id=category_id,
        code=code.strip().upper(),
        name=name.strip(),
        description=description.strip() or None,
        total_stock=total_stock,
        available_stock=total_stock,
        condition=condition,
        image_path=image_path,
    ))
    db.commit()
    return RedirectResponse("/admin/items", status_code=303)


@router.post("/admin/items/{item_id}/update")
async def update_item(
    item_id: int,
    request: Request,
    category_id: int = Form(...),
    code: str = Form(...),
    name: str = Form(...),
    description: str = Form(""),
    total_stock: int = Form(...),
    available_stock: int = Form(...),
    condition: str = Form("Baik"),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    if redirect := admin_redirect(request):
        return redirect
    item = db.get(Item, item_id)
    duplicate = db.query(Item).filter(Item.code == code.strip().upper(), Item.id != item_id).first()
    if not item or duplicate or total_stock < 0 or available_stock < 0 or available_stock > total_stock or not db.get(Category, category_id):
        return RedirectResponse("/admin/items", status_code=303)
    try:
        new_image = save_image(image)
    except ValueError:
        return RedirectResponse("/admin/items", status_code=303)
    if new_image:
        delete_image(item.image_path)
        item.image_path = new_image
    item.category_id = category_id
    item.code = code.strip().upper()
    item.name = name.strip()
    item.description = description.strip() or None
    item.total_stock = total_stock
    item.available_stock = available_stock
    item.condition = condition
    db.commit()
    return RedirectResponse("/admin/items", status_code=303)


@router.post("/admin/items/{item_id}/delete")
async def delete_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    if redirect := admin_redirect(request):
        return redirect
    item = db.get(Item, item_id)
    if item and not item.loan_details:
        delete_image(item.image_path)
        db.delete(item)
        db.commit()
    return RedirectResponse("/admin/items", status_code=303)
