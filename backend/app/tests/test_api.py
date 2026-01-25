from fastapi.testclient import TestClient
from app.core.config import settings

def test_read_main(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Multi-Role Service Marketplace API"}

def test_create_user(client: TestClient):
    # Create a random email to avoid conflict
    import random
    import string
    random_str = ''.join(random.choices(string.ascii_lowercase, k=5))
    email = f"test_{random_str}@example.com"
    
    response = client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": "password123", "role": "CUSTOMER"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert "id" in data

def test_login(client: TestClient):
    # Use the user created above or create new one
    import random
    import string
    random_str = ''.join(random.choices(string.ascii_lowercase, k=5))
    email = f"login_{random_str}@example.com"
    password = "password123"
    
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"email": email, "password": password, "role": "CUSTOMER"},
    )
    
    response = client.post(
        f"{settings.API_V1_STR}/auth/login/access-token",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
