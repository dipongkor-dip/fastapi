from fastapi import APIRouter, HTTPException, Path, status
from models import Ambulance
from schemas import AmbulanceResponse
from enums import AmbulanceStatus
from utils.auth import driver_dependency, db_dependency

router = APIRouter()


@router.get("/", response_model=list[AmbulanceResponse])
def get_ambulances(db: db_dependency):
    return db.query(Ambulance).all()


@router.get("/available", response_model=list[AmbulanceResponse])
def get_available_ambulances(
    db: db_dependency,
):
    return (
        db.query(Ambulance).filter(Ambulance.status == AmbulanceStatus.AVAILABLE).all()
    )


@router.get("/{id}", response_model=AmbulanceResponse)
def get_ambulance(
    db: db_dependency,
    id: int = Path(..., description="id of ambulance", example=1),
):
    ambulance = db.query(Ambulance).filter(Ambulance.id == id).first()

    if ambulance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ambulance not found"
        )

    return ambulance


@router.get("/my/ambulance", response_model=AmbulanceResponse)
def get_my_ambulance(driver: driver_dependency, db: db_dependency):
    ambulance = db.query(Ambulance).filter(Ambulance.driver_id == driver.id).first()

    if ambulance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No ambulance assigned"
        )

    return ambulance


@router.put("/my/ambulance/status", response_model=AmbulanceResponse)
def update_my_ambulance_status(
    new_status: AmbulanceStatus,
    driver: driver_dependency,
    db: db_dependency,
):
    ambulance = db.query(Ambulance).filter(Ambulance.driver_id == driver.id).first()

    if ambulance is None:
        raise HTTPException(status_code=404, detail="No ambulance assigned")

    ambulance.status = new_status

    db.commit()
    db.refresh(ambulance)

    return ambulance
