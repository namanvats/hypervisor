from sqlalchemy.orm import Session
from models import Organization, Cluster, Deployment
from schemas import DeploymentCreate
from services import create_deployment

def test_scheduling(test_db: Session):
    # Step 1: Create an organization
    org = Organization(name="TestOrg", invite_code="TEST123")
    test_db.add(org)
    test_db.commit()

    # Step 2: Create a cluster associated with the organization
    cluster = Cluster(
        name="TestCluster",
        organization_id=org.id,
        total_cpu=10,
        total_ram=20,
        total_gpu=5,
    )
    test_db.add(cluster)
    test_db.commit()

    print("Clusters:", test_db.query(Cluster).all())

    # Step 3: Attempt to create a deployment
    deployment_data = {
        "cluster_name": "TestCluster",
        "organization_name": "TestOrg",
        "docker_image": "test/image",
        "required_cpu": 2,
        "required_ram": 4,
        "required_gpu": 1,
        "priority": 1,
    }

    deployment = DeploymentCreate(**deployment_data)

    create_deployment(deployment.dict(), test_db)

    # Step 4: Verify that the deployment is successfully created (add your own assertions as needed)
    deployments = test_db.query(Deployment).filter_by(cluster_id=cluster.id).all()
    assert len(deployments) == 1
    assert deployments[0].docker_image == "test/image"