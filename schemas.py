from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class OrganizationCreate(BaseModel):
    name: str

class JoinOrganization(BaseModel):
    username: str
    password: str
    invite_code: str

class ClusterCreate(BaseModel):
    name: str
    organization_name: str
    total_cpu: int
    total_ram: int
    total_gpu: int

class ResourceAllocation(BaseModel):
    cluster_name: str
    organization_name: str
    cpu: int
    ram: int
    gpu: int

class DeploymentCreate(BaseModel):
    cluster_name: str
    organization_name: str
    docker_image: str
    required_cpu: int
    required_ram: int
    required_gpu: int
    priority: int