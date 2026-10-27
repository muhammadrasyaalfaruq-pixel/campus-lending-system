from app.database import SessionLocal
from app.models.entities import Role, User
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

    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
