from fastapi import APIRouter, Depends
from pydantic import BaseModel
from models import Users
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session

router = APIRouter()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


class CreateUser(BaseModel):
    email: str
    username: str
    firstname: str
    lastname: str
    role: str
    password: str


@router.post("/users")
def create_user(db: db_dependency, new_user: CreateUser):
    user_model = Users(
        email=new_user.email,
        username=new_user.username,
        firstname=new_user.firstname,
        lastname=new_user.lastname,
        role=new_user.role,
        password=new_user.password,
    )

    db.add(user_model)
    db.commit()

    return JSONResponse(
        status_code=201,
        content={"message": "User created successfully"},
    )
