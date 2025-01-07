from fastapi.testclient import TestClient
from main import app
import uuid


client = TestClient(app)


def test_create_organization(client):
    org_name = f"TestOrg-{uuid.uuid4()}"
    response = client.post("/organization/create", json={"name": org_name})
    assert response.status_code == 200
    assert "invite_code" in response.json()

def test_create_user(client):
    username = f"user-{uuid.uuid4()}"
    client.post("/organization/create", json={"name": f"Org-{uuid.uuid4()}"})
    response = client.post(
        "/user/register", json={"username": username, "password": "password123"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "User registered successfully"}
