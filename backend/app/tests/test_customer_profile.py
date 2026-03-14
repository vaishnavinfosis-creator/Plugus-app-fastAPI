"""
Unit tests for customer profile management endpoints
Tests Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.models import User, UserRole, Address, PhoneNumber
from app.core.security import get_password_hash


@pytest.fixture
def customer_user(db: Session):
    """Create a test customer user"""
    user = User(
        email="customer@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test Customer",
        role=UserRole.CUSTOMER,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def customer_token(client: TestClient, customer_user: User):
    """Get authentication token for customer"""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "customer@test.com", "password": "password123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(customer_token: str):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {customer_token}"}


class TestProfileManagement:
    """Test customer profile management - Requirements 12.1, 12.2"""
    
    def test_get_profile(self, client: TestClient, auth_headers: dict, customer_user: User):
        """Test getting customer profile"""
        response = client.get("/api/v1/customer/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "customer@test.com"
        assert data["full_name"] == "Test Customer"
        assert data["role"] == "CUSTOMER"
    
    def test_update_profile_name(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test updating customer name - Requirement 12.1, 12.2"""
        response = client.put(
            "/api/v1/customer/profile",
            params={"full_name": "Updated Name"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Profile updated successfully"
        assert data["profile"]["full_name"] == "Updated Name"
        
        # Verify persistence in database
        db.refresh(customer_user)
        assert customer_user.full_name == "Updated Name"
    
    def test_update_profile_name_persistence(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test that name persists after update - Requirement 12.2"""
        # Update name
        client.put(
            "/api/v1/customer/profile",
            params={"full_name": "Persistent Name"},
            headers=auth_headers
        )
        
        # Get profile again to verify persistence
        response = client.get("/api/v1/customer/profile", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Persistent Name"


class TestAddressManagement:
    """Test address CRUD operations - Requirement 12.3, 12.5"""
    
    def test_create_address(self, client: TestClient, auth_headers: dict):
        """Test adding a new address"""
        address_data = {
            "label": "Home",
            "address_text": "123 Main St, City, State",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "is_default": True
        }
        
        response = client.post(
            "/api/v1/customer/addresses",
            json=address_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Home"
        assert data["address_text"] == "123 Main St, City, State"
        assert data["is_default"] is True
    
    def test_create_address_validation_empty_label(self, client: TestClient, auth_headers: dict):
        """Test address validation - empty label - Requirement 12.5"""
        address_data = {
            "label": "",
            "address_text": "123 Main St",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/customer/addresses",
            json=address_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "label is required" in response.json()["detail"].lower()
    
    def test_create_address_validation_empty_text(self, client: TestClient, auth_headers: dict):
        """Test address validation - empty text - Requirement 12.5"""
        address_data = {
            "label": "Home",
            "address_text": "",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/customer/addresses",
            json=address_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "address text is required" in response.json()["detail"].lower()
    
    def test_get_addresses(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test getting all addresses"""
        # Create test addresses
        address1 = Address(
            user_id=customer_user.id,
            label="Home",
            address_text="123 Main St",
            is_default=True
        )
        address2 = Address(
            user_id=customer_user.id,
            label="Office",
            address_text="456 Work Ave",
            is_default=False
        )
        db.add_all([address1, address2])
        db.commit()
        
        response = client.get("/api/v1/customer/addresses", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(addr["label"] == "Home" for addr in data)
        assert any(addr["label"] == "Office" for addr in data)
    
    def test_update_address(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test editing an address - Requirement 12.3"""
        # Create address
        address = Address(
            user_id=customer_user.id,
            label="Home",
            address_text="123 Main St",
            is_default=True
        )
        db.add(address)
        db.commit()
        db.refresh(address)
        
        # Update address
        updated_data = {
            "label": "Home Updated",
            "address_text": "789 New St",
            "is_default": False
        }
        
        response = client.put(
            f"/api/v1/customer/addresses/{address.id}",
            json=updated_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Home Updated"
        assert data["address_text"] == "789 New St"
        assert data["is_default"] is False
    
    def test_update_address_validation(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test address update validation - Requirement 12.5"""
        # Create address
        address = Address(
            user_id=customer_user.id,
            label="Home",
            address_text="123 Main St",
            is_default=True
        )
        db.add(address)
        db.commit()
        db.refresh(address)
        
        # Try to update with empty label
        updated_data = {
            "label": "",
            "address_text": "789 New St",
            "is_default": False
        }
        
        response = client.put(
            f"/api/v1/customer/addresses/{address.id}",
            json=updated_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "label is required" in response.json()["detail"].lower()
    
    def test_delete_address(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test deleting an address - Requirement 12.3"""
        # Create address
        address = Address(
            user_id=customer_user.id,
            label="Home",
            address_text="123 Main St",
            is_default=True
        )
        db.add(address)
        db.commit()
        db.refresh(address)
        
        # Delete address
        response = client.delete(
            f"/api/v1/customer/addresses/{address.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()
        
        # Verify deletion
        deleted_address = db.query(Address).filter(Address.id == address.id).first()
        assert deleted_address is None
    
    def test_delete_nonexistent_address(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent address"""
        response = client.delete(
            "/api/v1/customer/addresses/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_max_addresses_limit(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test maximum 2 addresses limit"""
        # Create 2 addresses
        address1 = Address(user_id=customer_user.id, label="Home", address_text="123 Main St")
        address2 = Address(user_id=customer_user.id, label="Office", address_text="456 Work Ave")
        db.add_all([address1, address2])
        db.commit()
        
        # Try to add third address
        address_data = {
            "label": "Vacation",
            "address_text": "789 Beach Rd",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/customer/addresses",
            json=address_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()


class TestPhoneNumberManagement:
    """Test phone number CRUD operations - Requirement 12.4, 12.5"""
    
    def test_create_phone(self, client: TestClient, auth_headers: dict):
        """Test adding a new phone number"""
        phone_data = {
            "number": "+1234567890",
            "is_default": True
        }
        
        response = client.post(
            "/api/v1/customer/phones",
            json=phone_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["number"] == "+1234567890"
        assert data["is_default"] is True
    
    def test_create_phone_validation_empty(self, client: TestClient, auth_headers: dict):
        """Test phone validation - empty number - Requirement 12.5"""
        phone_data = {
            "number": "",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/customer/phones",
            json=phone_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()
    
    def test_create_phone_validation_invalid_format(self, client: TestClient, auth_headers: dict):
        """Test phone validation - invalid format - Requirement 12.5"""
        phone_data = {
            "number": "abc123",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/customer/phones",
            json=phone_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_create_phone_validation_too_short(self, client: TestClient, auth_headers: dict):
        """Test phone validation - too short - Requirement 12.5"""
        phone_data = {
            "number": "123",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/customer/phones",
            json=phone_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_get_phones(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test getting all phone numbers"""
        # Create test phones
        phone1 = PhoneNumber(user_id=customer_user.id, number="+1234567890", is_default=True)
        phone2 = PhoneNumber(user_id=customer_user.id, number="+9876543210", is_default=False)
        db.add_all([phone1, phone2])
        db.commit()
        
        response = client.get("/api/v1/customer/phones", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert any(phone["number"] == "+1234567890" for phone in data)
        assert any(phone["number"] == "+9876543210" for phone in data)
    
    def test_update_phone(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test updating a phone number - Requirement 12.4"""
        # Create phone
        phone = PhoneNumber(user_id=customer_user.id, number="+1234567890", is_default=True)
        db.add(phone)
        db.commit()
        db.refresh(phone)
        
        # Update phone
        updated_data = {
            "number": "+9876543210",
            "is_default": False
        }
        
        response = client.put(
            f"/api/v1/customer/phones/{phone.id}",
            json=updated_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["number"] == "+9876543210"
        assert data["is_default"] is False
    
    def test_update_phone_validation(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test phone update validation - Requirement 12.5"""
        # Create phone
        phone = PhoneNumber(user_id=customer_user.id, number="+1234567890", is_default=True)
        db.add(phone)
        db.commit()
        db.refresh(phone)
        
        # Try to update with invalid number
        updated_data = {
            "number": "invalid",
            "is_default": False
        }
        
        response = client.put(
            f"/api/v1/customer/phones/{phone.id}",
            json=updated_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()
    
    def test_delete_phone(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test deleting a phone number"""
        # Create phone
        phone = PhoneNumber(user_id=customer_user.id, number="+1234567890", is_default=True)
        db.add(phone)
        db.commit()
        db.refresh(phone)
        
        # Delete phone
        response = client.delete(
            f"/api/v1/customer/phones/{phone.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()
        
        # Verify deletion
        deleted_phone = db.query(PhoneNumber).filter(PhoneNumber.id == phone.id).first()
        assert deleted_phone is None
    
    def test_delete_nonexistent_phone(self, client: TestClient, auth_headers: dict):
        """Test deleting non-existent phone"""
        response = client.delete(
            "/api/v1/customer/phones/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_max_phones_limit(self, client: TestClient, auth_headers: dict, db: Session, customer_user: User):
        """Test maximum 2 phone numbers limit"""
        # Create 2 phones
        phone1 = PhoneNumber(user_id=customer_user.id, number="+1234567890")
        phone2 = PhoneNumber(user_id=customer_user.id, number="+9876543210")
        db.add_all([phone1, phone2])
        db.commit()
        
        # Try to add third phone
        phone_data = {
            "number": "+5555555555",
            "is_default": False
        }
        
        response = client.post(
            "/api/v1/customer/phones",
            json=phone_data,
            headers=auth_headers
        )
        
        assert response.status_code == 400
        assert "maximum" in response.json()["detail"].lower()
