"""
Create Super Admin Script
Run: python -m scripts.create_super_admin
"""
import sys
sys.path.insert(0, '.')

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.models import User, UserRole, Region, Category


def create_super_admin():
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    db = SessionLocal()
    
    try:
        # Check if super admin exists
        admin = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN,
            User.is_active == True
        ).first()
        
        if admin:
            print(f"✓ Super Admin already exists: {admin.email}")
            print("  Only one Super Admin is allowed in the system.")
            return
        
        # Create super admin
        admin = User(
            email="admin@plugus.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Super Admin",
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("✓ Created Super Admin: admin@plugus.com / admin123")
        
        # Create default region
        region = db.query(Region).first()
        if not region:
            region = Region(name="Default Region", description="Default region")
            db.add(region)
            db.commit()
            print("✓ Created Default Region")
        
        # Create default categories
        default_categories = [
            ("Laundry", "shirt"),
            ("Car/Bike Service", "car-sport"),
            ("Mobile Repair", "phone-portrait"),
            ("Electrician", "flash"),
            ("A/C Service", "snow"),
            ("House Help", "home"),
        ]
        
        for name, icon in default_categories:
            existing = db.query(Category).filter(Category.name == name).first()
            if not existing:
                cat = Category(
                    name=name,
                    icon=icon,
                    is_active=True,
                    is_default=True,
                    created_by=admin.id
                )
                db.add(cat)
        
        db.commit()
        print("✓ Created default categories")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_super_admin()
