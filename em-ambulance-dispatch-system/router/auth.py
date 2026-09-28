import secrets
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database import get_db
from models import Users
from schemas import RegisterUser, TokenResponse, VerifyOTP
from utils.auth import (
    authenticate_user,
    create_access_token,
    hash_password,
    user_dependency,
    verify_password,
)
from utils.email_sending import send_email
from utils.redis import redis

router = APIRouter()
db_dependency = Annotated[Session, Depends(get_db)]


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(new_user: RegisterUser, db: db_dependency):
    existing_username = (
        db.query(Users).filter(Users.username == new_user.username).first()
    )
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    existing_email = db.query(Users).filter(Users.email == new_user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    user = Users(
        username=new_user.username,
        email=new_user.email,
        firstname=new_user.firstname,
        lastname=new_user.lastname,
        password=hash_password(new_user.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency,
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.username, user.id, user.role)
    return {
        "access_token": token,
        "token_type": "bearer",
    }


def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


@router.post("/send-otp")
def send_otp(email: str, db: db_dependency):

    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist",
        )

    otp = generate_otp()

    redis.set(
        f"password_reset_otp:{email}", otp, ex=300
    )  # Store OTP in Redis with a 5-minute expiration

    email_body = f"""
Hello,

Your password reset OTP is: {otp}

This OTP expires in 5 minutes.

If you did not request a password reset, please ignore this email.

Regards,
Ambulance Dispatch System
"""

    try:
        send_email(
            recipient_email=email,
            subject="Password Reset OTP",
            body=email_body,
        )

    except Exception as e:
        print("Email sending error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to send OTP email",
        )

    return {"message": "OTP has been sent to your email"}


@router.post("/verify-otp")
def verify_otp(data: VerifyOTP):

    redis_key = f"password_reset_otp:{data.email}"

    stored_otp = redis.get(redis_key)

    if stored_otp is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP expired or not found",
        )

    if stored_otp != data.otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    # OTP is correct.
    # Delete it so it cannot be reused.
    redis.delete(redis_key)

    # Mark this email as verified for password reset.
    verified_key = f"password_reset_verified:{data.email}"

    redis.setex(verified_key, 600, "true")  # Mark as verified for 10 minutes

    return {"message": "OTP verified successfully"}


@router.post("/reset-password")
def reset_password(email: str, new_password: str, db: db_dependency):

    verified_key = f"password_reset_verified:{email}"

    if not redis.exists(verified_key):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not verified or expired",
        )

    user = db.query(Users).filter(Users.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist",
        )

    user.password = hash_password(new_password)
    db.commit()

    # Remove the verified key after password reset
    redis.delete(verified_key)

    return {"message": "Password has been reset successfully"}


@router.post("/change-password")
def change_password(
    user: user_dependency,
    db: db_dependency,
    current_password: str,
    new_password: str,
):
    if not user.password or not verify_password(current_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    user.password = hash_password(new_password)
    db.commit()

    return {"message": "Password changed successfully"}
