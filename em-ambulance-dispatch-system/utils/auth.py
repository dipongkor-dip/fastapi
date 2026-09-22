from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from enums import UserRole
from models import Users

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_dependency = Annotated[Session, Depends(get_db)]


def hash_password(password: str):
    return bcrypt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Users).filter(Users.username == username).first()

    if user is None or not user.is_active:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(username: str, user_id: int, role: UserRole):
    expires = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {
        "sub": username,
        "id": user_id,
        "role": role.value,
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def get_current_user(
    token: Annotated[str, Depends(oauth2_bearer)],
    db: db_dependency,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        username = payload.get("sub")
        user_id = payload.get("id")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Users).filter(Users.id == user_id).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


user_dependency = Annotated[Users, Depends(get_current_user)]


def get_current_superadmin(
    current_user: user_dependency,
):
    if current_user.role != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="SuperAdmin access required")

    return current_user


superadmin_dependency = Annotated[Users, Depends(get_current_superadmin)]


def get_current_admin(current_user: user_dependency):
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPERADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


admin_dependency = Annotated[Users, Depends(get_current_admin)]


def get_current_driver(current_user: user_dependency):
    if current_user.role != UserRole.DRIVER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Driver access required",
        )
    return current_user


driver_dependency = Annotated[Users, Depends(get_current_driver)]


def get_current_passenger(current_user: user_dependency):
    if current_user.role != UserRole.PASSENGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Passenger access required",
        )
    return current_user


passenger_dependency = Annotated[Users, Depends(get_current_passenger)]
