from sqlalchemy.exc import IntegrityError

from config import settings
from database import SessionLocal
from enums import UserRole
from models import Users
from utils.auth import hash_password


def create_default_superadmin() -> dict[str, bool | str]:
    db = SessionLocal()
    try:
        existing_superadmin = (
            db.query(Users)
            .filter(
                Users.email == settings.superadmin_email,
                Users.role == UserRole.SUPERADMIN,
            )
            .first()
        )
        if existing_superadmin:
            return {
                "message": "Superadmin already exists",
                "created": False,
            }

        existing_user = (
            db.query(Users)
            .filter(
                (Users.username == settings.superadmin_username)
                | (Users.email == settings.superadmin_email)
            )
            .first()
        )
        if existing_user:
            raise RuntimeError(
                "Configured superadmin username or email is already in use"
            )

        superadmin = Users(
            username=settings.superadmin_username,
            email=settings.superadmin_email,
            firstname=settings.superadmin_firstname,
            lastname=settings.superadmin_lastname,
            password=hash_password(settings.superadmin_password),
            role=UserRole.SUPERADMIN,
        )
        db.add(superadmin)
        db.commit()
        print("Default superadmin created successfully.")
    except IntegrityError as error:
        db.rollback()
        raise RuntimeError("Could not create the default superadmin") from error
    finally:
        db.close()
