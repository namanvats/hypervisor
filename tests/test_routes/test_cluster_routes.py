# File: tests/test_routes/test_cluster_routes.py
from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

def test_create_cluster(client):
    org_name = f"TestOrg-{uuid.uuid4()}"
    client.post("/organization/create", json={"name": org_name})
    response = client.post("/cluster/create", json={
        "name": f"Cluster-{uuid.uuid4()}",
        "organization_name": org_name,
        "total_cpu": 10,
        "total_ram": 10,
        "total_gpu": 10
    })
    assert response.status_code == 200

def test_list_clusters():
    response = client.get("/cluster/list/TestOrg")
    assert response.status_code == 200
    assert len(response.json()["clusters"]) > 0
