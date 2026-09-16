from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from models import Users
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from database import SessionLocal
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import jwt

router = APIRouter()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl="login")


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
    phone: str


@router.post("/users")
def create_user(db: db_dependency, new_user: CreateUser):
    user_model = Users(
        email=new_user.email,
        username=new_user.username,
        firstname=new_user.firstname,
        lastname=new_user.lastname,
        role=new_user.role,
        password=bcrypt_context.hash(new_user.password),
        phone=new_user.phone,
    )

    db.add(user_model)
    db.commit()

    return JSONResponse(
        status_code=201,
        content={"message": "User created successfully"},
    )


def authenticate_user(db: db_dependency, username, password):
    user = db.query(Users).filter(Users.username == username).first()

    if user is None:
        return False

    if bcrypt_context.verify(password, user.password):
        return user
    else:
        return False


def create_access_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):
    encode = {"sub": username, "id": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})

    return jwt.encode(encode, "secret-key", algorithm="HS256")


def decode_access_token(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, "secret-key", algorithms=["HS256"])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: int = payload.get("role")

        if username is None or user_id is None or user_role is None:
            raise HTTPException(status_code=404, detail="Unauthorized user")

        return {"username": username, "id": user_id, "role": user_role}
    except:
        raise HTTPException(status_code=404, detail="Unauthorized user")


user_dependency = Annotated[dict, Depends(decode_access_token)]


@router.post("/login")
def login_user(
    db: db_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(401, "Unauthorized user")

    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=30)
    )
    return {"access_token": token, "token_type": "Bearer"}


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    firstname: str | None = None
    lastname: str | None = None
    isActive: bool
    role: str | None = None
    phone: str | None = None

    class Config:
        from_attributes = True  # Allows reading data directly from SQLAlchemy models


@router.get("/me", response_model=UserResponse)
def get_profile(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(401, "Unauthorized user")

    u = db.query(Users).filter(Users.id == user.get("id")).first()

    return u


class UpdateUser(BaseModel):
    username: Optional[str] = Field(default=None)
    firstname: Optional[str] = Field(default=None)
    lastname: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)


@router.put("/users")
def update_profile(user: user_dependency, db: db_dependency, payload: UpdateUser):
    if user is None:
        raise HTTPException(401, "Unauthorized user")

    u = db.query(Users).filter(Users.id == user.get("id")).first()

    update_user = payload.model_dump(exclude_unset=True)

    for k, v in update_user.items():
        setattr(u, k, v)

    db.commit()

    return JSONResponse(status_code=200, content={"message": "Updated successfully"})


class UpdatePassword(BaseModel):
    current_password: str
    new_password: str


@router.put("/users/pass")
def update_password(user: user_dependency, db: db_dependency, payload: UpdatePassword):
    if user is None:
        raise HTTPException(401, "Unauthorized user")

    u = db.query(Users).filter(Users.id == user.get("id")).first()

    if not bcrypt_context.verify(payload.current_password, u.password):
        raise HTTPException(401, "Wrong Password")

    u.password = bcrypt_context.hash(payload.new_password)

    db.add(u)
    db.commit()

    return JSONResponse(status_code=200, content={"message": "Updated successfully"})
