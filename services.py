from sqlalchemy.orm import Session
from models import User, Organization, Cluster, Deployment
from utils import get_password_hash, generate_invite_code, generate_unique_cluster_name
from utils import enqueue_deployment, dequeue_deployment, simulate_deployment_execution, delete_deployment_from_queue, list_queue
from fastapi import HTTPException
import threading
import time

scheduling_lock = threading.Lock()
cluster_locks = {}

def create_organization(org_name: str, db: Session):
    invite_code = generate_invite_code()
    new_org = Organization(name=org_name, invite_code=invite_code)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org


def create_user(username: str, password: str, db: Session):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(password)
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def join_existing_organization(username: str, password: str, invite_code: str, db: Session):
    org = db.query(Organization).filter(Organization.invite_code == invite_code).first()
    if not org:
        raise HTTPException(status_code=400, detail="Invalid invite code")

    existing_user = db.query(User).filter(User.username == username).first()
    if not existing_user:
        raise HTTPException(status_code=400, detail="User does not exist in the database")

    user_in_org = db.query(User).filter(User.username == username, User.organization_id == org.id).first()
    if user_in_org:
        raise HTTPException(status_code=400, detail=f"User already exists in the organization: {org.name}")

    # Link existing user to the organization
    existing_user.organization_id = org.id
    db.commit()
    return existing_user


def get_organization_invite_code(org_name: str, db: Session):
    org = db.query(Organization).filter(Organization.name == org_name).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org.invite_code


def get_users_in_organization(org_name: str, db: Session):
    org = db.query(Organization).filter(Organization.name == org_name).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    users = db.query(User).filter(User.organization_id == org.id).all()
    return [user.username for user in users]


def create_cluster(cluster_data: dict, db: Session):
    org = db.query(Organization).filter(Organization.name == cluster_data["organization_name"]).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    existing_cluster = db.query(Cluster).filter(Cluster.name == cluster_data["name"], Cluster.organization_id == org.id).first()
    if existing_cluster:
        raise HTTPException(status_code=400, detail="Cluster with the same name already exists in the organization")

    cluster = Cluster(
        name=cluster_data["name"],
        organization_id=org.id,
        total_cpu=cluster_data["total_cpu"],
        total_ram=cluster_data["total_ram"],
        total_gpu=cluster_data["total_gpu"]
    )
    db.add(cluster)
    db.commit()
    db.refresh(cluster)
    return cluster


def get_clusters_for_organization(organization_id: int, db: Session):
    clusters = db.query(Cluster).filter(Cluster.organization_id == organization_id).all()
    if not clusters:
        raise HTTPException(status_code=404, detail="No clusters found for this organization")
    return clusters


def get_clusters_for_organization_by_name(organization_name: str, db: Session):
    org = db.query(Organization).filter(Organization.name == organization_name).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    clusters = db.query(Cluster).filter(Cluster.organization_id == org.id).all()
    if not clusters:
        raise HTTPException(status_code=404, detail="No clusters found for this organization")
    return clusters


def get_cluster_by_name_and_org(cluster_name: str, organization_name: str, db: Session):
    org = db.query(Organization).filter(Organization.name == organization_name).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    cluster = db.query(Cluster).filter(Cluster.name == cluster_name, Cluster.organization_id == org.id).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found in the organization")

    return cluster


def allocate_resources(cluster_name: str, organization_name: str, cpu: int, ram: int, gpu: int, db: Session):
    cluster = get_cluster_by_name_and_org(cluster_name, organization_name, db)

    if cluster.allocated_cpu + cpu > cluster.total_cpu or \
       cluster.allocated_ram + ram > cluster.total_ram or \
       cluster.allocated_gpu + gpu > cluster.total_gpu:
        raise HTTPException(status_code=400, detail="Insufficient resources available in the cluster")

    cluster.allocated_cpu += cpu
    cluster.allocated_ram += ram
    cluster.allocated_gpu += gpu
    db.commit()
    db.refresh(cluster)
    return cluster


def release_resources(cluster_name: str, organization_name: str, cpu: int, ram: int, gpu: int, db: Session):
    cluster = get_cluster_by_name_and_org(cluster_name, organization_name, db)

    cluster.allocated_cpu -= cpu
    cluster.allocated_ram -= ram
    cluster.allocated_gpu -= gpu

    if cluster.allocated_cpu < 0 or cluster.allocated_ram < 0 or cluster.allocated_gpu < 0:
        raise HTTPException(status_code=400, detail="Cannot release more resources than allocated")

    db.commit()
    db.refresh(cluster)
    return cluster


def create_deployment(deployment_data: dict, db: Session):
    cluster = get_cluster_by_name_and_org(deployment_data["cluster_name"], deployment_data["organization_name"], db)

    new_deployment = Deployment(
        cluster_id=cluster.id,
        docker_image=deployment_data["docker_image"],
        required_cpu=deployment_data["required_cpu"],
        required_ram=deployment_data["required_ram"],
        required_gpu=deployment_data["required_gpu"],
        priority=deployment_data["priority"],
        status="in_queue"
    )
    db.add(new_deployment)
    db.commit()
    db.refresh(new_deployment)

    # Add deployment to Redis queue
    enqueue_deployment(deployment_data["cluster_name"], new_deployment.id, deployment_data["priority"])

    # Trigger scheduling
    schedule_deployments(deployment_data["cluster_name"], db)
    return new_deployment

cluster_locks = {}

def schedule_deployments(cluster_name, db):
    if cluster_name not in cluster_locks:
        cluster_locks[cluster_name] = threading.Lock()

    print(f"Scheduling deployments for cluster {cluster_name}...")
    cluster = db.query(Cluster).filter(Cluster.name == cluster_name).first()
    if not cluster:
        print(f"Cluster {cluster_name} not found.")
        return

    queue = list_queue(cluster_name)
    if not queue:
        print(f"No deployments in the queue for cluster {cluster_name}.")
        return
    print(f"Queue for {cluster_name}: {queue}")

    print(f"Attempting to acquire lock for cluster {cluster_name}...")
    lock = cluster_locks[cluster_name]
    acquired = lock.acquire(timeout=10)
    if not acquired:
        print(f"Failed to acquire lock for cluster {cluster_name}. Another thread may be holding it.")
        return

    try:
        while queue:
            deployment_id = dequeue_deployment(cluster_name)
            if not deployment_id:
                print(f"No deployments left to schedule for cluster {cluster_name}.")
                break

            deployment = db.query(Deployment).filter(Deployment.id == int(deployment_id)).first()
            if not deployment:
                print(f"Deployment {deployment_id} not found in the database.")
                continue

            # Check resource availability
            if cluster.allocated_cpu + deployment.required_cpu <= cluster.total_cpu and \
               cluster.allocated_ram + deployment.required_ram <= cluster.total_ram and \
               cluster.allocated_gpu + deployment.required_gpu <= cluster.total_gpu:
                # Allocate resources and mark deployment as running
                cluster.allocated_cpu += deployment.required_cpu
                cluster.allocated_ram += deployment.required_ram
                cluster.allocated_gpu += deployment.required_gpu
                deployment.status = "running"
                db.commit()

                print(f"Deployment {deployment.id} started on cluster {cluster_name}.")
                threading.Thread(
                    target=simulate_deployment_execution,
                    args=(
                        {
                            "deployment": deployment,
                            "cluster": cluster,
                            "cluster_name": cluster_name,
                            "db": db,
                        },
                        lock,
                        schedule_deployments,
                    ),
                ).start()
                return  # Stop further scheduling
            else:
                # Re-enqueue deployment if resources are insufficient
                enqueue_deployment(cluster_name, deployment.id, deployment.priority)
                print(f"Deployment {deployment_id} re-enqueued due to insufficient resources.")
                break
    finally:
        lock.release()
        print(f"Lock released for cluster {cluster_name}.")

def list_deployments(cluster_name: str, db: Session):
    cluster = db.query(Cluster).filter(Cluster.name == cluster_name).first()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    deployments = db.query(Deployment).filter(Deployment.cluster_id == cluster.id).all()
    return [
        {
            "id": deployment.id,
            "docker_image": deployment.docker_image,
            "status": deployment.status,
            "required_cpu": deployment.required_cpu,
            "required_ram": deployment.required_ram,
            "required_gpu": deployment.required_gpu,
            "priority": deployment.priority
        } for deployment in deployments
    ]


def delete_deployment(deployment_id: int, cluster_name: str, db: Session):
    """Deletes a deployment and releases resources if it is running."""
    deployment = db.query(Deployment).filter(Deployment.id == deployment_id).first()
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")

    delete_deployment_from_queue(cluster_name, deployment_id, db, schedule_deployments)

    return {"message": f"Deployment {deployment_id} deleted successfully."}