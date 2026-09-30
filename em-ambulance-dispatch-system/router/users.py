from fastapi import APIRouter, HTTPException, Query, status

from models import Users
from schemas import UpdateUser, UserResponse, UsernameAvailabilityResponse
from utils.auth import user_dependency, db_dependency

router = APIRouter()


@router.get(
    "/username-availability", response_model=UsernameAvailabilityResponse
)
def check_username_availability(
    user: user_dependency,
    db: db_dependency,
    username: str = Query(..., min_length=3, max_length=100),
):
    normalized_username = username.strip()
    if len(normalized_username) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must contain at least 3 non-whitespace characters",
        )

    existing_user = (
        db.query(Users)
        .filter(
            Users.username == normalized_username,
            Users.id != user.id,
        )
        .first()
    )
    return {"available": existing_user is None}


@router.get("/me", response_model=UserResponse)
def get_profile(user: user_dependency):
    return user


@router.put("/me", response_model=UserResponse)
def update_profile(
    data: UpdateUser,
    user: user_dependency,
    db: db_dependency,
):
    if data.username is not None and data.username != user.username:
        existing_username = (
            db.query(Users)
            .filter(Users.username == data.username, Users.id != user.id)
            .first()
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
        user.username = data.username

    if data.email is not None:
        existing = (
            db.query(Users).filter(Users.email == data.email, Users.id != user.id).first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )
        user.email = data.email

    if data.firstname is not None:
        user.firstname = data.firstname

    if data.lastname is not None:
        user.lastname = data.lastname

    db.commit()
    db.refresh(user)
    return user


@router.delete("/me")
def delete_my_account(user: user_dependency, db: db_dependency):
    user.is_active = False
    db.commit()
    return {"message": "Account deactivated successfully"}


