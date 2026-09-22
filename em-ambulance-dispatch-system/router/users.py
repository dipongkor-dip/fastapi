from fastapi import APIRouter, HTTPException, status

from models import Users
from schemas import UpdateUser, UserResponse
from utils.auth import user_dependency, db_dependency

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_profile(user: user_dependency):
    return user


@router.put("/me", response_model=UserResponse)
def update_profile(
    data: UpdateUser,
    user: user_dependency,
    db: db_dependency,
):
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
