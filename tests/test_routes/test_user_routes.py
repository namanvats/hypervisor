from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_user(client):
    client.post("/organization/create", json={"name": "TestOrg"})

    # Create the user
    response = client.post(
        "/user/register",
        json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}

def test_create_duplicate_user(client):
    # Create the same user twice to test duplicate handling
    client.post("/organization/create", json={"name": "TestOrg"})
    client.post("/user/register", json={"username": "testuser", "password": "password123"})
    
    # Attempt to create the duplicate user
    response = client.post(
        "/user/register",
        json={"username": "testuser", "password": "password123"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already exists"}
