"""
Database Reset Script
Cleans the database and creates a fresh superadmin user
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, engine
from app.models.models import User, UserRole
from app.core.security import get_password_hash

# Superadmin credentials
SUPERADMIN_EMAIL = "naresh@plugus.net"
SUPERADMIN_PASSWORD = "Naresh@plugus99044"
SUPERADMIN_NAME = "Naresh Kumar"


def reset_database():
    """Drop all tables and recreate them"""
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("📦 Creating fresh tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset complete!")


def create_superadmin():
    """Create superadmin user"""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    
    try:
        print(f"👤 Creating superadmin user: {SUPERADMIN_EMAIL}")
        
        # Check if any Super Admin already exists
        existing_super_admin = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN,
            User.is_active == True
        ).first()
        
        # Check if user with this email already exists
        existing_user = db.query(User).filter(User.email == SUPERADMIN_EMAIL).first()
        
        if existing_user:
            # If the existing user is already a Super Admin, just update password
            if existing_user.role == UserRole.SUPER_ADMIN:
                print("⚠️  Superadmin user already exists, updating password...")
                existing_user.hashed_password = get_password_hash(SUPERADMIN_PASSWORD)
                existing_user.is_active = True
                existing_user.full_name = SUPERADMIN_NAME
                db.commit()
                print("✅ Superadmin password updated!")
            else:
                # If existing user is not Super Admin but another Super Admin exists
                if existing_super_admin:
                    print(f"❌ Error: A Super Admin already exists ({existing_super_admin.email})")
                    print("   Only one Super Admin is allowed in the system.")
                    print("   Cannot convert this user to Super Admin.")
                    return
                # Convert existing user to Super Admin
                print("⚠️  Converting existing user to Super Admin...")
                existing_user.role = UserRole.SUPER_ADMIN
                existing_user.hashed_password = get_password_hash(SUPERADMIN_PASSWORD)
                existing_user.is_active = True
                existing_user.full_name = SUPERADMIN_NAME
                db.commit()
                print("✅ User converted to Super Admin!")
        else:
            # Check if another Super Admin already exists
            if existing_super_admin:
                print(f"❌ Error: A Super Admin already exists ({existing_super_admin.email})")
                print("   Only one Super Admin is allowed in the system.")
                print("   Cannot create a new Super Admin.")
                return
            
            # Create new superadmin user
            superadmin = User(
                email=SUPERADMIN_EMAIL,
                hashed_password=get_password_hash(SUPERADMIN_PASSWORD),
                full_name=SUPERADMIN_NAME,
                role=UserRole.SUPER_ADMIN,
                is_active=True
            )
            db.add(superadmin)
            db.commit()
            db.refresh(superadmin)
            print(f"✅ Superadmin user created with ID: {superadmin.id}")
        
        print("\n" + "="*60)
        print("🎉 Database Reset Complete!")
        print("="*60)
        print(f"📧 Email: {SUPERADMIN_EMAIL}")
        print(f"🔑 Password: {SUPERADMIN_PASSWORD}")
        print(f"👤 Role: SUPER_ADMIN")
        print("="*60)
        print("\nYou can now login with these credentials at:")
        print("http://localhost:8081 (Frontend)")
        print("http://127.0.0.1:8000/docs (API Docs)")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error creating superadmin: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main function"""
    print("\n" + "="*60)
    print("🔄 DATABASE RESET SCRIPT")
    print("="*60)
    print("⚠️  WARNING: This will delete ALL data in the database!")
    print("="*60 + "\n")
    
    # Confirm action
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Database reset cancelled.")
        return
    
    print("\n🚀 Starting database reset...\n")
    
    # Reset database
    reset_database()
    
    # Create superadmin
    create_superadmin()


if __name__ == "__main__":
    main()
