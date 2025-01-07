from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas import ClusterCreate, ResourceAllocation
from services import create_cluster, get_clusters_for_organization_by_name, allocate_resources, release_resources
from database import get_db

router = APIRouter()

@router.post("/create")
def create_cluster_route(cluster: ClusterCreate, db: Session = Depends(get_db)):
    new_cluster = create_cluster(cluster.dict(), db)
    return {"message": "Cluster created successfully", "cluster_id": new_cluster.id}

@router.get("/list/{org_name}")
def list_clusters_for_organization(org_name: str, db: Session = Depends(get_db)):
    clusters = get_clusters_for_organization_by_name(org_name, db)
    return {
        "organization_name": org_name,
        "clusters": [
            {
                "id": cluster.id,
                "name": cluster.name,
                "cpu": cluster.total_cpu,
                "ram": cluster.total_ram,
                "gpu": cluster.total_gpu,
                "allocated_cpu": cluster.allocated_cpu,
                "allocated_ram": cluster.allocated_ram,
                "allocated_gpu": cluster.allocated_gpu
            } for cluster in clusters
        ]
    }

@router.post("/allocate")
def allocate_resources_route(allocation: ResourceAllocation, db: Session = Depends(get_db)):
    updated_cluster = allocate_resources(allocation.cluster_name, allocation.organization_name, allocation.cpu, allocation.ram, allocation.gpu, db)
    return {
        "message": "Resources allocated successfully",
        "cluster": {
            "id": updated_cluster.id,
            "name": updated_cluster.name,
            "allocated_cpu": updated_cluster.allocated_cpu,
            "allocated_ram": updated_cluster.allocated_ram,
            "allocated_gpu": updated_cluster.allocated_gpu
        }
    }

@router.post("/release")
def release_resources_route(allocation: ResourceAllocation, db: Session = Depends(get_db)):
    updated_cluster = release_resources(allocation.cluster_name, allocation.organization_name, allocation.cpu, allocation.ram, allocation.gpu, db)
    return {
        "message": "Resources released successfully",
        "cluster": {
            "id": updated_cluster.id,
            "name": updated_cluster.name,
            "allocated_cpu": updated_cluster.allocated_cpu,
            "allocated_ram": updated_cluster.allocated_ram,
            "allocated_gpu": updated_cluster.allocated_gpu
        }
    }
