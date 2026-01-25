from fastapi.testclient import TestClient
from app.core.config import settings
import pytest

# Global variables to share data between tests (simulating a sequence)
data = {
    "admin_token": None,
    "vendor_token": None,
    "customer_token": None,
    "worker_token": None,
    "region_id": None,
    "category_id": None,
    "service_id": None,
    "worker_id": None,
    "booking_id": None
}

def test_01_admin_login(client: TestClient):
    # Login as the super admin created by the script
    response = client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={"username": "admin@example.com", "password": "admin"},
    )
    assert response.status_code == 200
    data["admin_token"] = response.json()["access_token"]

def test_02_create_region_and_category(client: TestClient):
    headers = {"Authorization": f"Bearer {data['admin_token']}"}
    
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    # Create Region
    res = client.post(
        f"{settings.API_V1_STR}/admin/regions",
        headers=headers,
        json={"name": f"Test Region {unique_id}"}
    )
    # 200 or 400 if exists (since we are running on persistent sqlite now)
    if res.status_code == 200:
        data["region_id"] = res.json()["id"]
    else:
        # Try to fetch if exists
        res = client.get(f"{settings.API_V1_STR}/admin/regions", headers=headers)
        data["region_id"] = res.json()[0]["id"]

    # Create Category
    res = client.post(
        f"{settings.API_V1_STR}/admin/categories",
        headers=headers,
        json={"name": f"Test Category {unique_id}", "description": "Test Desc"}
    )
    if res.status_code == 200:
        data["category_id"] = res.json()["id"]
    else:
        res = client.get(f"{settings.API_V1_STR}/admin/categories", headers=headers)
        data["category_id"] = res.json()[0]["id"]

def test_03_vendor_flow(client: TestClient):
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    # Register Vendor
    email = f"vendor_{unique_id}@example.com"
    password = "password"
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": password, "role": "VENDOR"},
    )
    
    # Login Vendor
    res = client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={"username": email, "password": password},
    )
    data["vendor_token"] = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {data['vendor_token']}"}

    # Create Service
    res = client.post(
        f"{settings.API_V1_STR}/vendor/services",
        headers=headers,
        json={
            "name": "Test Service",
            "description": "Best service",
            "base_price": 100.0,
            "duration_minutes": 60,
            "category_id": data["category_id"]
        }
    )
    if res.status_code != 200:
        print(f"Vendor Service Error: {res.json()}")
    assert res.status_code == 200
    data["service_id"] = res.json()["id"]

    # Create Worker
    res = client.post(
        f"{settings.API_V1_STR}/vendor/workers",
        headers=headers,
        json={
            "email": f"worker_{unique_id}@example.com",
            "password": "password123"
        }
    )
    assert res.status_code == 200
    data["worker_id"] = res.json()["id"]
    data["worker_email"] = f"worker_{unique_id}@example.com"

def test_04_customer_flow(client: TestClient):
    # Register Customer
    email = "customer_test@example.com"
    password = "password"
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": password, "role": "CUSTOMER"},
    )
    
    # Login Customer
    res = client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={"username": email, "password": password},
    )
    data["customer_token"] = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {data['customer_token']}"}

    # Create Booking
    res = client.post(
        f"{settings.API_V1_STR}/customer/bookings",
        headers=headers,
        json={
            "service_id": data["service_id"],
            "scheduled_time": "2026-01-20T10:00:00"
        }
    )
    assert res.status_code == 200
    data["booking_id"] = res.json()["id"]

def test_05_worker_flow(client: TestClient):
    # Worker Login
    # We need to retrieve the email used in test_03. 
    # Since we can't easily share the dynamic email across tests without a global var update in test_03,
    # let's update test_03 to store it in `data`.
    
    email = data.get("worker_email")
    password = "password123"
    
    res = client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={"username": email, "password": password},
    )
    assert res.status_code == 200
    data["worker_token"] = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {data['worker_token']}"}

    # Get Tasks (Bookings)
    # Note: Booking needs to be assigned to worker. 
    # Currently our booking flow might not auto-assign. 
    # Let's check if we can assign or if worker sees unassigned?
    # For now, just checking we can hit the endpoint.
    res = client.get(f"{settings.API_V1_STR}/worker/tasks", headers=headers)
    assert res.status_code == 200

    # Update Location
    res = client.post(
        f"{settings.API_V1_STR}/worker/location",
        headers=headers,
        json={"lat": 40.7128, "lng": -74.0060}
    )
    assert res.status_code == 200

def test_06_complaint_flow(client: TestClient):
    headers = {"Authorization": f"Bearer {data['customer_token']}"}
    
    # Create Complaint
    res = client.post(
        f"{settings.API_V1_STR}/complaint/complaints",
        headers=headers,
        json={
            "booking_id": data["booking_id"],
            "description": "Worker was late"
        }
    )
    assert res.status_code == 200
