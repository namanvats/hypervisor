from fastapi.testclient import TestClient
from main import app
import uuid

client = TestClient(app)

def test_create_deployment(client):
    org_name = f"TestOrg-{uuid.uuid4()}"
    cluster_name = f"Cluster-{uuid.uuid4()}"
    client.post("/organization/create", json={"name": org_name})
    client.post("/cluster/create", json={
        "name": cluster_name,
        "organization_name": org_name,
        "total_cpu": 10,
        "total_ram": 10,
        "total_gpu": 10
    })
    response = client.post("/deployment/create", json={
        "cluster_name": cluster_name,
        "organization_name": org_name,
        "docker_image": "test-image",
        "required_cpu": 2,
        "required_ram": 2,
        "required_gpu": 1,
        "priority": 1
    })
    assert response.status_code == 200


def test_list_deployments(client):
    # Create a cluster and a deployment
    org_name = f"Org-{uuid.uuid4()}"
    cluster_name = f"Cluster-{uuid.uuid4()}"
    client.post("/organization/create", json={"name": org_name})
    client.post("/cluster/create", json={
        "name": cluster_name,
        "organization_name": org_name,
        "total_cpu": 10,
        "total_ram": 10,
        "total_gpu": 10
    })
    client.post("/deployment/create", json={
        "cluster_name": cluster_name,
        "organization_name": org_name,
        "docker_image": "test-image",
        "required_cpu": 2,
        "required_ram": 2,
        "required_gpu": 1,
        "priority": 1
    })

    # Test listing deployments
    response = client.get(f"/deployment/list/{cluster_name}")
    assert response.status_code == 200
    assert len(response.json()["deployments"]) > 0
