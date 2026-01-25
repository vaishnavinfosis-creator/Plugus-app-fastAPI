#!/bin/bash
# Prestart script for Docker container
# Runs before the main application starts

echo "=== Running prestart script ==="

# Wait for database to be ready
echo "Waiting for database..."
python << END
import time
import psycopg2
import os

database_url = os.environ.get('DATABASE_URL')
if not database_url:
    print("DATABASE_URL not set, skipping DB check")
    exit(0)

# Render uses postgres:// but psycopg2 needs postgresql://
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# Parse connection details
max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        conn = psycopg2.connect(database_url)
        conn.close()
        print("Database connection successful!")
        break
    except Exception as e:
        retry_count += 1
        print(f"Database not ready, attempt {retry_count}/{max_retries}: {e}")
        time.sleep(2)

if retry_count >= max_retries:
    print("Could not connect to database!")
    exit(1)
END

# Run database migrations
echo "Running migrations..."
cd /app
python -c "
from app.core.database import engine, Base
from app.models.models import *
print('Creating database tables...')
Base.metadata.create_all(bind=engine)
print('Tables created successfully!')
"

# Check if super admin exists, create if not
echo "Checking super admin..."
python -c "
from app.core.database import SessionLocal
from app.models.models import User, Region, Category
from app.core.security import get_password_hash
from app.models.models import UserRole

db = SessionLocal()

try:
    # Check for existing super admin
    admin = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
    if not admin:
        print('Creating default super admin...')
        
        # Create default region (only name is required per the model)
        region = db.query(Region).first()
        if not region:
            region = Region(name='Default Region', description='Default region for the platform')
            db.add(region)
            db.commit()
            db.refresh(region)
            print('Default region created')
        
        # Create super admin
        admin = User(
            email='admin@plugus.com',
            hashed_password=get_password_hash('admin123'),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            full_name='Super Admin'
        )
        db.add(admin)
        db.commit()
        print('Super admin created: admin@plugus.com / admin123')
        
        # Create default categories
        default_categories = ['Plumbing', 'Electrical', 'Cleaning', 'AC Repair', 'Carpentry', 'Painting']
        for cat_name in default_categories:
            if not db.query(Category).filter(Category.name == cat_name).first():
                db.add(Category(name=cat_name, is_default=True))
        db.commit()
        print('Default categories created')
    else:
        print('Super admin already exists')
except Exception as e:
    print(f'Error during admin creation: {e}')
    db.rollback()
    raise
finally:
    db.close()
"

echo "=== Prestart complete ==="
