from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from models import User
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import jwt
from config import settings

router = APIRouter()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticate_user(db: db_dependency, username, password):
    user = db.query(User).filter(User.username == username).first()

    if user is None:
        return False

    if bcrypt_context.verify(password, user.password):
        return user
    else:
        return False


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})

    return jwt.encode(encode, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(status_code=404, detail="Unauthorized user")

        return {"username": username, "id": user_id}
    except:
        raise HTTPException(status_code=404, detail="Unauthorized user")


class CreateUser(BaseModel):
    username: str
    email: str
    password: str


@router.post("/register")
def create_user(db: db_dependency, new_user: CreateUser):
    user_model = User(
        username=new_user.username,
        email=new_user.email,
        password=bcrypt_context.hash(new_user.password),
    )

    db.add(user_model)
    db.commit()

    return JSONResponse({"message": "User created successfully"}, 201)


@router.post("/login")
def login(
    db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(401, "Unauthorized user")

    token = create_access_token(
        user.username,
        user.id,
        timedelta(settings.access_token_expire_minutes),
    )
    return {"access_token": token, "token_type": "Bearer"}
