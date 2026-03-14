import pytest
from typing import Generator
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.models import User, UserRole
from app.core.security import get_password_hash, create_access_token

@pytest.fixture(scope="module")
def db() -> Generator:
    yield SessionLocal()

@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def super_admin_user(db) -> User:
    """Create a Super Admin user for testing"""
    # Check if super admin already exists
    existing = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
    if existing:
        return existing
    
    # Create new super admin
    user = User(
        email="superadmin@example.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.SUPER_ADMIN,
        is_active=True,
        full_name="Super Admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def super_admin_token_headers(super_admin_user: User) -> dict:
    """Generate authentication headers for Super Admin"""
    access_token = create_access_token(super_admin_user.id)
    return {"Authorization": f"Bearer {access_token}"}
