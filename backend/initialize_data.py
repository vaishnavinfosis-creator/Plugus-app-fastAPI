"""
Initialize essential data in the database
"""
from app.core.database import SessionLocal
from app.models.models import Region, Category, User, UserRole

def initialize_data():
    """Add essential regions and categories"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        region_count = db.query(Region).count()
        category_count = db.query(Category).count()
        
        if region_count > 0 and category_count > 0:
            print(f"✅ Data already initialized ({region_count} regions, {category_count} categories)")
            return
        
        # Get superadmin ID for created_by field
        superadmin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
        if not superadmin:
            print("❌ Error: No superadmin found. Please run reset_database.py first.")
            return
        
        # Create regions if they don't exist
        if region_count == 0:
            print("📍 Creating regions...")
            regions = [
                Region(name="Mumbai", state="Maharashtra", description="Mumbai Metropolitan Region", is_active=True),
                Region(name="Delhi", state="Delhi", description="National Capital Region", is_active=True),
                Region(name="Bangalore", state="Karnataka", description="Bangalore Urban Region", is_active=True)
            ]
            for region in regions:
                db.add(region)
            db.commit()
            print(f"✅ Created {len(regions)} regions")
        
        # Create categories if they don't exist
        if category_count == 0:
            print("📂 Creating categories...")
            categories = [
                Category(name="Cleaning", description="Home and office cleaning services", is_active=True, is_default=True, created_by=superadmin.id),
                Category(name="Plumbing", description="Plumbing and water-related services", is_active=True, is_default=True, created_by=superadmin.id),
                Category(name="Electrical", description="Electrical repair and installation", is_active=True, is_default=True, created_by=superadmin.id)
            ]
            for category in categories:
                db.add(category)
            db.commit()
            print(f"✅ Created {len(categories)} categories")
        
        print("\n" + "="*60)
        print("🎉 Data Initialization Complete!")
        print("="*60)
        print(f"📍 Regions: {db.query(Region).count()}")
        print(f"📂 Categories: {db.query(Category).count()}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error initializing data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔄 DATA INITIALIZATION SCRIPT")
    print("="*60 + "\n")
    initialize_data()
