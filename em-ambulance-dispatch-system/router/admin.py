from fastapi import APIRouter, HTTPException, Path, status

from models import Ambulance, Users
from schemas import (
    AmbulanceResponse,
    CreateAmbulance,
    CreateDriver,
    UserResponse,
)
from enums import UserRole
from utils.auth import (
    admin_dependency,
    db_dependency,
    hash_password,
    superadmin_dependency,
)
from schemas import RegisterUser

router = APIRouter()


@router.post(
    "/create-admin", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_admin(_: superadmin_dependency, db: db_dependency, new_admin: RegisterUser):
    existing_admin = db.query(Users).filter(Users.username == new_admin.username).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin already exists",
        )

    existing_email = db.query(Users).filter(Users.email == new_admin.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    admin = Users(
        username=new_admin.username,
        email=new_admin.email,
        firstname=new_admin.firstname,
        lastname=new_admin.lastname,
        password=hash_password(new_admin.password),
        role=UserRole.ADMIN,
    )

    db.add(admin)
    db.commit()
    db.refresh(admin)

    return admin


@router.get("/users", response_model=list[UserResponse])
def get_all_users(_: admin_dependency, db: db_dependency):
    return db.query(Users).all()


@router.get("/users/{id}", response_model=UserResponse)
def get_user(
    _: admin_dependency,
    db: db_dependency,
    id: int = Path(description="id of users", example=1),
):
    user = db.query(Users).filter(Users.id == id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.delete("/users/{id}")
def deactivate_user(
    _: admin_dependency,
    db: db_dependency,
    id: int = Path(description="id of users", example=1),
):
    user = db.query(Users).filter(Users.id == id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    user.is_active = False
    db.commit()
    return {"message": "User deactivated successfully"}


@router.post(
    "/drivers", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_driver(data: CreateDriver, _: admin_dependency, db: db_dependency):
    if db.query(Users).filter(Users.username == data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )
    if db.query(Users).filter(Users.email == data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
        )
    driver = Users(
        username=data.username,
        email=data.email,
        firstname=data.firstname,
        lastname=data.lastname,
        password=hash_password(data.password),
        role=UserRole.DRIVER,
    )
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.get("/drivers", response_model=list[UserResponse])
def get_drivers(_: admin_dependency, db: db_dependency):
    return db.query(Users).filter(Users.role == UserRole.DRIVER).all()


@router.post(
    "/ambulances", response_model=AmbulanceResponse, status_code=status.HTTP_201_CREATED
)
def create_ambulance(data: CreateAmbulance, _: admin_dependency, db: db_dependency):
    if (
        db.query(Ambulance)
        .filter(Ambulance.ambulance_number == data.ambulance_number)
        .first()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ambulance number already exists",
        )
    if data.driver_id is not None:
        driver = db.query(Users).filter(Users.id == data.driver_id).first()
        if driver is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found"
            )
        if driver.role != UserRole.DRIVER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected user is not a driver",
            )
    ambulance = Ambulance(**data.model_dump())
    db.add(ambulance)
    db.commit()
    db.refresh(ambulance)
    return ambulance


@router.put("/ambulances/{id}", response_model=AmbulanceResponse)
def update_ambulance(
    _: admin_dependency,
    db: db_dependency,
    data: CreateAmbulance,
    id: int = Path(..., description="id of ambulance", example=1),
):
    ambulance = db.query(Ambulance).filter(Ambulance.id == id).first()
    if ambulance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ambulance not found"
        )
    if data.driver_id is not None:
        driver = db.query(Users).filter(Users.id == data.driver_id).first()
        if driver is None or driver.role != UserRole.DRIVER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid driver"
            )
    for field, value in data.model_dump().items():
        setattr(ambulance, field, value)
    db.commit()
    db.refresh(ambulance)
    return ambulance


@router.delete("/ambulances/{id}")
def delete_ambulance(
    _: admin_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of ambulance", example=1),
):
    ambulance = db.query(Ambulance).filter(Ambulance.id == id).first()
    if ambulance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ambulance not found"
        )
    db.delete(ambulance)
    db.commit()
    return {"message": "Ambulance deleted successfully"}
