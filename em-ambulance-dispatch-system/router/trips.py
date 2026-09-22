from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Path, status

from enums import AmbulanceStatus, RequestStatus, TripStatus
from models import Ambulance, AmbulanceRequest, Trip
from schemas import TripResponse, UpdateFare
from utils.auth import (
    admin_dependency,
    db_dependency,
    driver_dependency,
    passenger_dependency,
)

router = APIRouter()


# =========================
# PASSENGER
# =========================
@router.get("/my", response_model=list[TripResponse])
def get_my_trips(passenger: passenger_dependency, db: db_dependency):
    return db.query(Trip).filter(Trip.passenger_id == passenger.id).all()


@router.get("/my/{id}", response_model=TripResponse)
def get_my_trip(
    passenger: passenger_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of trip", example=1),
):
    trip = (
        db.query(Trip).filter(Trip.id == id, Trip.passenger_id == passenger.id).first()
    )
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    return trip


# =========================
# DRIVER
# =========================
@router.get("/driver/my", response_model=list[TripResponse])
def get_driver_trips(driver: driver_dependency, db: db_dependency):
    return db.query(Trip).filter(Trip.driver_id == driver.id).all()


@router.post("/{id}/start", response_model=TripResponse)
def start_trip(
    driver: driver_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of trip", example=1),
):
    trip = db.query(Trip).filter(Trip.id == id, Trip.driver_id == driver.id).first()
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    if trip.status != TripStatus.ONGOING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Trip is not active"
        )
    trip.start_time = datetime.now(timezone.utc)
    db.commit()
    db.refresh(trip)
    return trip


@router.post("/{id}/complete", response_model=TripResponse)
def complete_trip(
    driver: driver_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of trip", example=1),
):
    trip = db.query(Trip).filter(Trip.id == id, Trip.driver_id == driver.id).first()
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    if trip.status != TripStatus.ONGOING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Trip is already completed"
        )

    trip.status = TripStatus.COMPLETED
    trip.end_time = datetime.now(timezone.utc)
    ambulance = db.query(Ambulance).filter(Ambulance.id == trip.ambulance_id).first()
    if ambulance:
        ambulance.status = AmbulanceStatus.AVAILABLE
    request = (
        db.query(AmbulanceRequest)
        .filter(AmbulanceRequest.id == trip.request_id)
        .first()
    )
    if request:
        request.status = RequestStatus.COMPLETED
    db.commit()
    db.refresh(trip)
    return trip


@router.put("/{id}/fare", response_model=TripResponse)
def update_fare(
    data: UpdateFare,
    driver: driver_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of trip", example=1),
):
    trip = db.query(Trip).filter(Trip.id == id, Trip.driver_id == driver.id).first()
    if trip is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found"
        )
    trip.fare = data.fare
    db.commit()
    db.refresh(trip)
    return trip


# =========================
# ADMIN
# =========================
@router.get("/admin/all", response_model=list[TripResponse])
def get_all_trips(admin: admin_dependency, db: db_dependency):
    return db.query(Trip).all()
