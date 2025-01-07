from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas import UserCreate, JoinOrganization
from services import create_user, join_existing_organization
from database import get_db

router = APIRouter()

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = create_user(user.username, user.password, db)
    return {"message": "User registered successfully"}

@router.post("/join")
def join_organization(data: JoinOrganization, db: Session = Depends(get_db)):
    new_user = join_existing_organization(data.username, data.password, data.invite_code, db)
    return {"message": f"User {data.username} joined organization successfully"}