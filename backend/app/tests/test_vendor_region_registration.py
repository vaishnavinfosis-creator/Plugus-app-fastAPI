"""
Tests for vendor registration with region selection
Requirements: 8.1, 8.2, 8.3
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.models import User, Vendor, Region, UserRole
from app.core.database import get_db


class TestVendorRegionRegistration:
    """Test vendor registration requires region selection"""

    def test_vendor_registration_requires_region_id(self, client: TestClient, db: Session):
        """Test that vendor registration fails without region_id"""
        # Create a region first
        region = Region(name="Test Region", is_active=True)
        db.add(region)
        db.commit()

        # Attempt to register vendor without region_id
        response = client.post("/api/v1/auth/register", json={
            "email": "vendor_no_region@test.com",
            "password": "password123",
            "role": "VENDOR"
        })

        assert response.status_code == 400
        assert "Region selection is required" in response.json()["detail"]

    def test_vendor_registration_validates_region_exists(self, client: TestClient, db: Session):
        """Test that vendor registration validates region_id exists"""
        response = client.post("/api/v1/auth/register", json={
            "email": "vendor_invalid_region@test.com",
            "password": "password123",
            "role": "VENDOR",
            "region_id": 9999  # Non-existent region
        })

        assert response.status_code == 400
        assert "Invalid region selected" in response.json()["detail"]

    def test_vendor_registration_with_valid_region(self, client: TestClient, db: Session):
        """Test successful vendor registration with valid region_id"""
        # Create a region
        region = Region(name="North Region", is_active=True)
        db.add(region)
        db.commit()
        db.refresh(region)

        # Register vendor with valid region
        response = client.post("/api/v1/auth/register", json={
            "email": "vendor_valid@test.com",
            "password": "password123",
            "role": "VENDOR",
            "region_id": region.id
        })

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "vendor_valid@test.com"
        assert data["role"] == "VENDOR"

        # Verify vendor was created with correct region
        vendor = db.query(Vendor).filter(Vendor.user_id == data["id"]).first()
        assert vendor is not None
        assert vendor.region_id == region.id

    def test_customer_registration_does_not_require_region(self, client: TestClient, db: Session):
        """Test that customer registration works without region_id"""
        response = client.post("/api/v1/auth/register", json={
            "email": "customer_no_region@test.com",
            "password": "password123",
            "role": "CUSTOMER"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "customer_no_region@test.com"
        assert data["role"] == "CUSTOMER"

        # Verify no vendor profile was created
        vendor = db.query(Vendor).filter(Vendor.user_id == data["id"]).first()
        assert vendor is None

    def test_vendor_assigned_to_selected_region(self, client: TestClient, db: Session):
        """Test that vendor is assigned to the selected region (Requirement 8.2)"""
        # Create multiple regions
        region1 = Region(name="Region 1", is_active=True)
        region2 = Region(name="Region 2", is_active=True)
        db.add_all([region1, region2])
        db.commit()
        db.refresh(region1)
        db.refresh(region2)

        # Register vendor with region2
        response = client.post("/api/v1/auth/register", json={
            "email": "vendor_region2@test.com",
            "password": "password123",
            "role": "VENDOR",
            "region_id": region2.id
        })

        assert response.status_code == 200
        user_id = response.json()["id"]

        # Verify vendor is assigned to region2, not region1
        vendor = db.query(Vendor).filter(Vendor.user_id == user_id).first()
        assert vendor.region_id == region2.id
        assert vendor.region_id != region1.id
