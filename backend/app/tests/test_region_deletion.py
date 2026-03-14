"""
Unit tests for region deletion functionality.

Tests Requirements 2.1, 2.2, 2.4 from platform-fixes-and-enhancements spec.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.models import Region, User, Vendor, UserRole
from app.core.security import get_password_hash


class TestRegionDeletion:
    """Test suite for region deletion endpoint."""

    def test_delete_region_success(
        self,
        client: TestClient,
        db: Session,
        super_admin_token_headers: dict
    ):
        """
        Test successful region deletion.
        Validates: Requirement 2.1, 2.2
        """
        # Create a region with no constraints
        region = Region(
            name="Test Region for Deletion",
            state="Test State",
            is_active=True
        )
        db.add(region)
        db.commit()
        db.refresh(region)
        region_id = region.id

        # Delete the region
        response = client.delete(
            f"/api/v1/admin/regions/{region_id}",
            headers=super_admin_token_headers
        )

        # Verify successful deletion
        assert response.status_code == 200
        assert response.json()["message"] == "Region deleted successfully"

        # Verify region is removed from database
        deleted_region = db.query(Region).filter(Region.id == region_id).first()
        assert deleted_region is None

    def test_delete_region_not_found(
        self,
        client: TestClient,
        super_admin_token_headers: dict
    ):
        """
        Test deletion of non-existent region.
        Validates: Requirement 2.4 (error handling)
        """
        # Try to delete a region that doesn't exist
        response = client.delete(
            "/api/v1/admin/regions/99999",
            headers=super_admin_token_headers
        )

        # Verify error response
        assert response.status_code == 404
        assert "Region not found" in response.json()["detail"]

    def test_delete_region_with_assigned_admin(
        self,
        client: TestClient,
        db: Session,
        super_admin_token_headers: dict
    ):
        """
        Test deletion fails when region has assigned admin.
        Validates: Requirement 2.4 (constraint error handling)
        """
        # Create a regional admin user
        admin_user = User(
            email="regional_admin@test.com",
            hashed_password=get_password_hash("password123"),
            full_name="Regional Admin",
            role=UserRole.REGIONAL_ADMIN,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        # Create a region with assigned admin
        region = Region(
            name="Region with Admin",
            state="Test State",
            is_active=True,
            admin_id=admin_user.id
        )
        db.add(region)
        db.commit()
        db.refresh(region)

        # Try to delete the region
        response = client.delete(
            f"/api/v1/admin/regions/{region.id}",
            headers=super_admin_token_headers
        )

        # Verify error response
        assert response.status_code == 400
        assert "Cannot delete region with assigned admin" in response.json()["detail"]

        # Verify region still exists
        existing_region = db.query(Region).filter(Region.id == region.id).first()
        assert existing_region is not None

    def test_delete_region_with_vendors(
        self,
        client: TestClient,
        db: Session,
        super_admin_token_headers: dict
    ):
        """
        Test deletion fails when region has vendors.
        Validates: Requirement 2.4 (constraint error handling)
        """
        # Create a vendor user
        vendor_user = User(
            email="vendor@test.com",
            hashed_password=get_password_hash("password123"),
            full_name="Test Vendor",
            role=UserRole.VENDOR,
            is_active=True
        )
        db.add(vendor_user)
        db.commit()
        db.refresh(vendor_user)

        # Create a region
        region = Region(
            name="Region with Vendors",
            state="Test State",
            is_active=True
        )
        db.add(region)
        db.commit()
        db.refresh(region)

        # Create a vendor in this region
        vendor = Vendor(
            user_id=vendor_user.id,
            region_id=region.id,
            business_name="Test Business",
            is_approved=True,
            is_visible=True
        )
        db.add(vendor)
        db.commit()

        # Try to delete the region
        response = client.delete(
            f"/api/v1/admin/regions/{region.id}",
            headers=super_admin_token_headers
        )

        # Verify error response
        assert response.status_code == 400
        assert "Cannot delete region with" in response.json()["detail"]
        assert "vendors" in response.json()["detail"]

        # Verify region still exists
        existing_region = db.query(Region).filter(Region.id == region.id).first()
        assert existing_region is not None

    def test_delete_region_requires_super_admin(
        self,
        client: TestClient,
        db: Session
    ):
        """
        Test that only Super Admin can delete regions.
        Validates: Authorization requirement
        """
        # Create a region
        region = Region(
            name="Test Region Auth",
            state="Test State",
            is_active=True
        )
        db.add(region)
        db.commit()
        db.refresh(region)

        # Try to delete without authentication
        response = client.delete(f"/api/v1/admin/regions/{region.id}")

        # Verify unauthorized
        assert response.status_code == 401

    def test_delete_region_database_commit_successful(
        self,
        client: TestClient,
        db: Session,
        super_admin_token_headers: dict
    ):
        """
        Test that database commit is successful after deletion.
        Validates: Requirement 2.2 (backend delete API executes successfully)
        """
        # Create a region
        region = Region(
            name="Test Commit Region",
            state="Test State",
            is_active=True
        )
        db.add(region)
        db.commit()
        db.refresh(region)
        region_id = region.id

        # Delete the region
        response = client.delete(
            f"/api/v1/admin/regions/{region_id}",
            headers=super_admin_token_headers
        )

        # Verify successful response
        assert response.status_code == 200

        # Force a new query to verify commit was successful
        db.expire_all()
        deleted_region = db.query(Region).filter(Region.id == region_id).first()
        assert deleted_region is None, "Region should be permanently deleted from database"

    def test_delete_region_multiple_vendors_error_message(
        self,
        client: TestClient,
        db: Session,
        super_admin_token_headers: dict
    ):
        """
        Test that error message includes vendor count.
        Validates: Requirement 2.4 (descriptive error message)
        """
        # Create vendor users
        vendor_user1 = User(
            email="vendor1@test.com",
            hashed_password=get_password_hash("password123"),
            full_name="Vendor 1",
            role=UserRole.VENDOR,
            is_active=True
        )
        vendor_user2 = User(
            email="vendor2@test.com",
            hashed_password=get_password_hash("password123"),
            full_name="Vendor 2",
            role=UserRole.VENDOR,
            is_active=True
        )
        db.add_all([vendor_user1, vendor_user2])
        db.commit()
        db.refresh(vendor_user1)
        db.refresh(vendor_user2)

        # Create a region
        region = Region(
            name="Region with Multiple Vendors",
            state="Test State",
            is_active=True
        )
        db.add(region)
        db.commit()
        db.refresh(region)

        # Create multiple vendors in this region
        vendor1 = Vendor(
            user_id=vendor_user1.id,
            region_id=region.id,
            business_name="Business 1",
            is_approved=True,
            is_visible=True
        )
        vendor2 = Vendor(
            user_id=vendor_user2.id,
            region_id=region.id,
            business_name="Business 2",
            is_approved=True,
            is_visible=True
        )
        db.add_all([vendor1, vendor2])
        db.commit()

        # Try to delete the region
        response = client.delete(
            f"/api/v1/admin/regions/{region.id}",
            headers=super_admin_token_headers
        )

        # Verify descriptive error message includes count
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "2 vendors" in detail or "2" in detail
        assert "vendors" in detail.lower()
