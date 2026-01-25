import sys
import os
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import Category, Region, Vendor, User, UserRole
from app.core.security import get_password_hash

def seed_data():
    db = SessionLocal()
    try:
        print("Starting database seed...")

        # 1. Create Categories
        categories_data = [
            {"name": "Plumbing", "description": "Pipe repairs, installation, and maintenance", "icon": "water"},
            {"name": "Electrical", "description": "Wiring, lighting, and electrical repairs", "icon": "flash"},
            {"name": "Cleaning", "description": "Home and office cleaning services", "icon": "sparkles"},
            {"name": "Gardening", "description": "Lawn care, landscaping, and maintenance", "icon": "leaf"},
            {"name": "Painting", "description": "Interior and exterior painting", "icon": "color-palette"},
        ]

        print("Seeding Categories...")
        for cat_data in categories_data:
            existing = db.query(Category).filter(Category.name == cat_data["name"]).first()
            if not existing:
                category = Category(
                    name=cat_data["name"],
                    description=cat_data["description"],
                    icon=cat_data["icon"],
                    is_active=True,
                    created_by=1  # Assuming Super Admin ID 1 exists
                )
                db.add(category)
        db.commit()

        # 2. Create Regions
        regions_data = ["Downtown", "North Suburbs", "South Bay", "West Side"]
        
        print("Seeding Regions...")
        for region_name in regions_data:
            existing = db.query(Region).filter(Region.name == region_name).first()
            if not existing:
                region = Region(name=region_name, is_active=True)
                db.add(region)
        db.commit()

        # 3. Create Vendors
        # Get region IDs
        downtown = db.query(Region).filter(Region.name == "Downtown").first()
        north = db.query(Region).filter(Region.name == "North Suburbs").first()
        south = db.query(Region).filter(Region.name == "South Bay").first()
        west = db.query(Region).filter(Region.name == "West Side").first()

        vendors_data = [
            {
                "email": "joe@plumbing.com",
                "business_name": "Joe's Plumbing",
                "phone": "555-0101",
                "region_id": downtown.id if downtown else None,
                "is_approved": True
            },
            {
                "email": "sparky@electric.com",
                "business_name": "Sparky Electric",
                "phone": "555-0102",
                "region_id": north.id if north else None,
                "is_approved": False
            },
            {
                "email": "clean@shine.com",
                "business_name": "Clean & Shine",
                "phone": "555-0103",
                "region_id": south.id if south else None,
                "is_approved": True
            },
            {
                "email": "green@thumb.com",
                "business_name": "Green Thumb",
                "phone": "555-0104",
                "region_id": west.id if west else None,
                "is_approved": False
            }
        ]

        print("Seeding Vendors...")
        for v_data in vendors_data:
            if not v_data["region_id"]:
                continue
                
            existing_user = db.query(User).filter(User.email == v_data["email"]).first()
            if not existing_user:
                # Create User
                user = User(
                    email=v_data["email"],
                    hashed_password=get_password_hash("password123"),
                    role=UserRole.VENDOR,
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)

                # Create Vendor Profile
                vendor = Vendor(
                    user_id=user.id,
                    business_name=v_data["business_name"],
                    region_id=v_data["region_id"],
                    is_approved=v_data["is_approved"],
                    is_visible=v_data["is_approved"],
                    description=f"Professional services by {v_data['business_name']}"
                )
                db.add(vendor)
        db.commit()

        print("Database seed completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
