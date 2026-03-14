"""
Unit tests for Regional Admin management endpoints
Tests Requirements 5.1, 5.2, 5.3, 5.4, 5.5
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import User, UserRole, Region


def test_create_admin_with_duplicate_email(
    client: TestClient,
    db: Session,
    super_admin_token_headers: dict
):
    """Test that creating an admin with duplicate email returns error"""
    # Create a region first
    region = Region(
        name="Test Region for Duplicate Email",
        state="Test State",
        is_active=True
    )
    db.add(region)
    db.commit()
    db.refresh(region)
    
    # Create first admin
    admin_data = {
        "admin_in": {
            "email": "duplicate@example.com",
            "password": "password123"
        },
        "region_id": region.id
    }
    
    response = client.post(
        "/api/v1/admin/admins",
        json=admin_data,
        headers=super_admin_token_headers
    )
    assert response.status_code == 200
    
    # Try to create another admin with same email
    region2 = Region(
        name="Test Region 2 for Duplicate Email",
        state="Test State 2",
        is_active=True
    )
    db.add(region2)
    db.commit()
    db.refresh(region2)
    
    admin_data2 = {
        "admin_in": {
            "email": "duplicate@example.com",
            "password": "password456"
        },
        "region_id": region2.id
    }
    
    response = client.post(
        "/api/v1/admin/admins",
        json=admin_data2,
        headers=super_admin_token_headers
    )
    
    # Should return 400 with "Email already exists" message
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"
    
    # Cleanup
    admin = db.query(User).filter(User.email == "duplicate@example.com").first()
    if admin:
        admin.is_active = False
        db.commit()
    db.delete(region)
    db.delete(region2)
    db.commit()


def test_get_admins_includes_region_info(
    client: TestClient,
    db: Session,
    super_admin_token_headers: dict
):
    """Test that get_admins returns region information for each admin"""
    # Create a region
    region = Region(
        name="Test Region for Admin Display",
        state="Test State",
        is_active=True
    )
    db.add(region)
    db.commit()
    db.refresh(region)
    
    # Create an admin
    admin_data = {
        "admin_in": {
            "email": "regionadmin@example.com",
            "password": "password123"
        },
        "region_id": region.id
    }
    
    response = client.post(
        "/api/v1/admin/admins",
        json=admin_data,
        headers=super_admin_token_headers
    )
    assert response.status_code == 200
    admin_id = response.json()["id"]
    
    # Get all admins
    response = client.get(
        "/api/v1/admin/admins",
        headers=super_admin_token_headers
    )
    assert response.status_code == 200
    admins = response.json()
    
    # Find our admin
    our_admin = next((a for a in admins if a["id"] == admin_id), None)
    assert our_admin is not None
    
    # Verify region information is included
    assert our_admin["region"] is not None
    assert our_admin["region"]["id"] == region.id
    assert our_admin["region"]["name"] == "Test Region for Admin Display"
    
    # Cleanup
    admin = db.query(User).filter(User.id == admin_id).first()
    if admin:
        admin.is_active = False
        db.commit()
    db.delete(region)
    db.commit()


def test_delete_admin_clears_region_assignment(
    client: TestClient,
    db: Session,
    super_admin_token_headers: dict
):
    """Test that deleting an admin clears the region's admin_id"""
    # Create a region
    region = Region(
        name="Test Region for Admin Deletion",
        state="Test State",
        is_active=True
    )
    db.add(region)
    db.commit()
    db.refresh(region)
    
    # Create an admin
    admin_data = {
        "admin_in": {
            "email": "deleteadmin@example.com",
            "password": "password123"
        },
        "region_id": region.id
    }
    
    response = client.post(
        "/api/v1/admin/admins",
        json=admin_data,
        headers=super_admin_token_headers
    )
    assert response.status_code == 200
    admin_id = response.json()["id"]
    
    # Verify region has admin assigned
    db.refresh(region)
    assert region.admin_id == admin_id
    
    # Delete the admin
    response = client.delete(
        f"/api/v1/admin/admins/{admin_id}",
        headers=super_admin_token_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Admin removed"
    
    # Verify admin is deactivated
    admin = db.query(User).filter(User.id == admin_id).first()
    assert admin is not None
    assert admin.is_active is False
    
    # Verify region's admin_id is cleared
    db.refresh(region)
    assert region.admin_id is None
    
    # Cleanup
    db.delete(region)
    db.commit()


def test_delete_admin_not_found(
    client: TestClient,
    super_admin_token_headers: dict
):
    """Test that deleting non-existent admin returns 404"""
    response = client.delete(
        "/api/v1/admin/admins/999999",
        headers=super_admin_token_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Admin not found"
