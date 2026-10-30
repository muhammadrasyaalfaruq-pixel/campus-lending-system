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
            ("Komputer & IT", "Perangkat komputer dan jaringan untuk kebutuhan akademik."),
            ("Olahraga", "Peralatan olahraga untuk unit kegiatan mahasiswa."),
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
            ("Kamera DSLR Canon", "CAM-001", "Kamera untuk dokumentasi acara dan tugas multimedia.", 3, "Multimedia", "/static/uploads/camera.jpg"),
            ("Proyektor Epson", "PRO-001", "Proyektor HD untuk presentasi kelas dan kegiatan kampus.", 4, "Multimedia", "/static/uploads/projector.jpg"),
            ("Tripod Kamera", "TRI-001", "Tripod stabil untuk pengambilan foto dan video.", 5, "Multimedia", "/static/uploads/tripod.jpg"),
            ("Multimeter Digital", "LAB-001", "Alat ukur tegangan, arus, dan resistansi.", 6, "Laboratorium", "/static/uploads/multimeter.jpg"),
            ("Mikroskop Digital", "LAB-002", "Mikroskop digital untuk praktikum biologi.", 2, "Laboratorium", "/static/uploads/microscope.jpg"),
            ("Speaker Portable", "EVT-001", "Speaker portable untuk seminar dan kegiatan mahasiswa.", 3, "Kegiatan Kampus", "/static/uploads/speaker.jpg"),
            ("Kursi Lipat", "EVT-002", "Kursi lipat untuk acara dan kegiatan organisasi.", 20, "Kegiatan Kampus", "/static/uploads/chair.jpg"),
            ("Laptop ASUS VivoBook", "IT-001", "Laptop untuk presentasi, praktikum, dan kerja kelompok.", 8, "Komputer & IT", "/static/uploads/laptop.jpg"),
            ("Mouse Wireless", "IT-002", "Mouse nirkabel untuk kebutuhan praktikum komputer.", 15, "Komputer & IT", "/static/uploads/mouse.jpg"),
            ("Router WiFi", "IT-003", "Router untuk praktik konfigurasi jaringan komputer.", 4, "Komputer & IT", "/static/uploads/router.jpg"),
            ("Kabel HDMI", "IT-004", "Kabel HDMI untuk menghubungkan laptop ke proyektor.", 12, "Komputer & IT", "/static/uploads/hdmi.jpg"),
            ("Bola Futsal", "SPT-001", "Bola futsal untuk latihan dan pertandingan antar mahasiswa.", 10, "Olahraga", "/static/uploads/futsal.jpg"),
            ("Raket Badminton", "SPT-002", "Raket badminton untuk kegiatan unit olahraga kampus.", 12, "Olahraga", "/static/uploads/badminton.jpg"),
            ("Bola Voli", "SPT-003", "Bola voli untuk latihan dan pertandingan kampus.", 8, "Olahraga", "/static/uploads/volleyball.jpg"),
            ("Matras Olahraga", "SPT-004", "Matras untuk senam, latihan bela diri, dan kegiatan olahraga.", 6, "Olahraga", "/static/uploads/mat.jpg"),
        ]
        for name, code, description, stock, category_name, image_path in items:
            existing = db.query(Item).filter(Item.code == code).first()
            if not existing:
                db.add(Item(
                    name=name,
                    code=code,
                    description=description,
                    total_stock=stock,
                    available_stock=stock,
                    condition="Baik",
                    category_id=category_map[category_name].id,
                    image_path=image_path,
                ))
                print(f"Alat dibuat: {name}")
            elif not existing.image_path:
                existing.image_path = image_path
                print(f"Image diupdate: {name}")
        db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
