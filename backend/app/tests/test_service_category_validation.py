"""
Unit tests for service creation with category validation
Tests Requirements 10.1, 10.2, 10.3
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.models import User, UserRole, Vendor, Category, Service, Region
from app.core.security import get_password_hash, create_access_token


@pytest.fixture
def test_region(db: Session):
    """Create a test region"""
    region = db.query(Region).first()
    if not region:
        region = Region(
            name="Test Region",
            state="Test State",
            is_active=True
        )
        db.add(region)
        db.commit()
        db.refresh(region)
    return region


@pytest.fixture
def test_vendor(db: Session, test_region):
    """Create a test vendor user"""
    # Check if vendor already exists
    existing = db.query(User).filter(User.email == "vendor@test.com").first()
    if existing:
        db.delete(existing)
        db.commit()
    
    user = User(
        email="vendor@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Vendor",
        role=UserRole.VENDOR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    vendor = Vendor(
        user_id=user.id,
        region_id=test_region.id,
        business_name="Test Business",
        is_approved=True,
        is_visible=True
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    return user


@pytest.fixture
def test_category(db: Session):
    """Create a test category"""
    # Check if category already exists
    existing = db.query(Category).filter(Category.name == "Test Category").first()
    if existing:
        return existing
    
    category = Category(
        name="Test Category",
        description="Test category description",
        is_active=True
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@pytest.fixture
def vendor_token(test_vendor):
    """Get auth token for vendor"""
    access_token = create_access_token(test_vendor.id)
    return access_token


def test_create_service_without_category_fails(vendor_token):
    """Test that service creation fails when category_id is missing"""
    client = TestClient(app)
    
    # This should fail validation at the Pydantic level
    # since category_id is a required field
    response = client.post(
        "/api/v1/vendor/services",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "name": "Test Service",
            "description": "Test description",
            "base_price": 100.0,
            "duration_minutes": 60
            # category_id is missing
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_create_service_with_null_category_fails(vendor_token):
    """Test that service creation fails when category_id is null"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/vendor/services",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "category_id": None,
            "name": "Test Service",
            "description": "Test description",
            "base_price": 100.0,
            "duration_minutes": 60
        }
    )
    
    # Should fail validation
    assert response.status_code in [400, 422]


def test_create_service_with_invalid_category_fails(vendor_token):
    """Test that service creation fails when category doesn't exist"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/vendor/services",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "category_id": 99999,  # Non-existent category
            "name": "Test Service",
            "description": "Test description",
            "base_price": 100.0,
            "duration_minutes": 60
        }
    )
    
    assert response.status_code == 400
    assert "category" in response.json()["detail"].lower()


def test_create_service_with_valid_category_succeeds(vendor_token, test_category, db):
    """Test that service creation succeeds with valid category"""
    client = TestClient(app)
    
    response = client.post(
        "/api/v1/vendor/services",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "category_id": test_category.id,
            "name": "Test Service",
            "description": "Test description",
            "base_price": 100.0,
            "duration_minutes": 60
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["category_id"] == test_category.id
    assert data["name"] == "Test Service"
    
    # Verify in database
    service = db.query(Service).filter(Service.id == data["id"]).first()
    assert service is not None
    assert service.category_id == test_category.id


def test_service_category_integrity(vendor_token, test_category, db):
    """Test that all services have exactly one non-null category_id"""
    client = TestClient(app)
    
    # Create a service
    response = client.post(
        "/api/v1/vendor/services",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "category_id": test_category.id,
            "name": "Test Service",
            "base_price": 100.0,
            "duration_minutes": 60
        }
    )
    
    assert response.status_code == 200
    service_id = response.json()["id"]
    
    # Verify service has category_id
    service = db.query(Service).filter(Service.id == service_id).first()
    assert service.category_id is not None
    assert service.category_id == test_category.id


def test_error_message_for_missing_category(vendor_token):
    """Test that error message is clear when category is missing"""
    client = TestClient(app)
    
    # Try with category_id = 0 (falsy value)
    response = client.post(
        "/api/v1/vendor/services",
        headers={"Authorization": f"Bearer {vendor_token}"},
        json={
            "category_id": 0,
            "name": "Test Service",
            "base_price": 100.0,
            "duration_minutes": 60
        }
    )
    
    assert response.status_code == 400
    assert "category" in response.json()["detail"].lower()
    assert "required" in response.json()["detail"].lower()
