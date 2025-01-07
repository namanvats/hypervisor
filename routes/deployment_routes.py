from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas import DeploymentCreate
from services import create_deployment, list_deployments, delete_deployment
from database import get_db
from utils import list_queue

router = APIRouter()

@router.post("/create")
def create_deployment_route(deployment: DeploymentCreate, db: Session = Depends(get_db)):
    new_deployment = create_deployment(deployment.dict(), db)
    return {"message": "Deployment created successfully", "deployment_id": new_deployment.id}

@router.get("/list/{cluster_name}")
def list_deployments_route(cluster_name: str, db: Session = Depends(get_db)):
    deployments = list_deployments(cluster_name, db)
    return {"cluster_name": cluster_name, "deployments": deployments}

@router.get("/queue/{cluster_name}")
def list_queue_route(cluster_name: str):
    queue = list_queue(cluster_name)
    return {
        "cluster_name": cluster_name,
        "queue": [{"deployment_id": int(item[0]), "priority": item[1]} for item in queue]
    }

@router.delete("/delete/{deployment_id}")
def delete_deployment_route(deployment_id: int, cluster_name: str, db: Session = Depends(get_db)):
    result = delete_deployment(deployment_id, cluster_name, db)
    return result