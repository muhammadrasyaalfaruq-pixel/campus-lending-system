from app.database import SessionLocal
from app.models.entities import Category, Item, Role, User
from app.services.auth_service import hash_password

def seed_data():
    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print("Role admin dibuat.")

        user_role = db.query(Role).filter(Role.name == "user").first()
        if not user_role:
            user_role = Role(name="user")
            db.add(user_role)
            db.commit()
            db.refresh(user_role)
            print("Role user dibuat.")

        admin_user = db.query(User).filter(User.email == "admin@kampus.ac.id").first()
        if not admin_user:
            admin_user = User(
                name="Administrator",
                email="admin@kampus.ac.id",
                password_hash=hash_password("admin123"),
                role_id=admin_role.id
            )
            db.add(admin_user)
            db.commit()
            print("Akun admin dibuat: admin@kampus.ac.id / admin123")
        else:
            print("Akun admin sudah ada.")

        demo_user = db.query(User).filter(User.email == "mahasiswa@kampus.ac.id").first()
        if not demo_user:
            demo_user = User(
                name="Budi Santoso",
                email="mahasiswa@kampus.ac.id",
                student_id="20230001",
                phone="081234567890",
                password_hash=hash_password("user123"),
                role_id=user_role.id,
            )
            db.add(demo_user)
            db.commit()
            print("Akun user dibuat: mahasiswa@kampus.ac.id / user123")
        else:
            print("Akun user sudah ada.")

        categories = [
            ("Multimedia", "Peralatan foto, video, dan presentasi."),
            ("Laboratorium", "Peralatan praktikum dan penelitian."),
            ("Kegiatan Kampus", "Peralatan untuk acara dan organisasi mahasiswa."),
        ]
        category_map = {}
        for name, description in categories:
            category = db.query(Category).filter(Category.name == name).first()
            if not category:
                category = Category(name=name, description=description)
                db.add(category)
                db.commit()
                db.refresh(category)
                print(f"Kategori dibuat: {name}")
            category_map[name] = category

        items = [
            ("Kamera DSLR Canon", "CAM-001", "Kamera untuk dokumentasi acara dan tugas multimedia.", 3, "Multimedia"),
            ("Proyektor Epson", "PRO-001", "Proyektor HD untuk presentasi kelas dan kegiatan kampus.", 4, "Multimedia"),
            ("Tripod Kamera", "TRI-001", "Tripod stabil untuk pengambilan foto dan video.", 5, "Multimedia"),
            ("Multimeter Digital", "LAB-001", "Alat ukur tegangan, arus, dan resistansi.", 6, "Laboratorium"),
            ("Mikroskop Digital", "LAB-002", "Mikroskop digital untuk praktikum biologi.", 2, "Laboratorium"),
            ("Speaker Portable", "EVT-001", "Speaker portable untuk seminar dan kegiatan mahasiswa.", 3, "Kegiatan Kampus"),
            ("Kursi Lipat", "EVT-002", "Kursi lipat untuk acara dan kegiatan organisasi.", 20, "Kegiatan Kampus"),
        ]
        for name, code, description, stock, category_name in items:
            if not db.query(Item).filter(Item.code == code).first():
                db.add(Item(
                    name=name,
                    code=code,
                    description=description,
                    total_stock=stock,
                    available_stock=stock,
                    condition="Baik",
                    category_id=category_map[category_name].id,
                ))
                print(f"Alat dibuat: {name}")
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
