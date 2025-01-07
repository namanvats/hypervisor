from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas import OrganizationCreate
from services import create_organization, get_organization_invite_code,get_users_in_organization
from database import get_db

router = APIRouter()

@router.post("/create")
def register_organization(org: OrganizationCreate, db: Session = Depends(get_db)):
    new_org = create_organization(org.name, db)
    return {"message": "Organization created successfully", "invite_code": new_org.invite_code}

@router.get("/get-invite-code/{org_name}")
def get_invite_code(org_name: str, db: Session = Depends(get_db)):
    invite_code = get_organization_invite_code(org_name, db)
    return {"invite_code": invite_code}

@router.get("/list-users/{org_name}")
def list_users_in_organization(org_name: str, db: Session = Depends(get_db)):
    users = get_users_in_organization(org_name, db)
    return {"organization": org_name, "users": users}