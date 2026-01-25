from app.core.database import SessionLocal
from app.models import User, UserRole
from app.core.security import get_password_hash
import sys

def create_super_admin():
    db = SessionLocal()
    email = "admin@example.com"
    password = "admin"
    
    try:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"User {email} already exists.")
            return

        user = User(
            email=email,
            hashed_password=get_password_hash(password),
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(user)
        db.commit()
        print(f"Super Admin created successfully.")
        print(f"Email: {email}")
        print(f"Password: {password}")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
