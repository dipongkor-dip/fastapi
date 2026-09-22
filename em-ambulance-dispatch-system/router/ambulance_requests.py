from fastapi import APIRouter, HTTPException, Path, status
from models import AmbulanceRequest, Ambulance, Trip
from schemas import CreateAmbulanceRequest, RequestResponse
from enums import RequestStatus, AmbulanceStatus, TripStatus
from utils.auth import (
    passenger_dependency,
    driver_dependency,
    admin_dependency,
    db_dependency,
)

router = APIRouter()


# =========================
# PASSENGER
# =========================
@router.post("/", response_model=RequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    data: CreateAmbulanceRequest, passenger: passenger_dependency, db: db_dependency,
):
    request = AmbulanceRequest(
        passenger_id=passenger.id,
        pickup_location=data.pickup_location,
        destination=data.destination,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get("/my", response_model=list[RequestResponse])
def get_my_requests(passenger: passenger_dependency, db: db_dependency):
    return (
        db.query(AmbulanceRequest)
        .filter(AmbulanceRequest.passenger_id == passenger.id)
        .all()
    )


@router.get("/my/{id}", response_model=RequestResponse)
def get_my_request(
    passenger: passenger_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of request", example=1),
):
    request = (
        db.query(AmbulanceRequest)
        .filter(
            AmbulanceRequest.id == id,
            AmbulanceRequest.passenger_id == passenger.id,
        )
        .first()
    )
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    return request


@router.post("/{id}/cancel", response_model=RequestResponse)
def cancel_request(
    passenger: passenger_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of request", example=1),
):
    request = (
        db.query(AmbulanceRequest)
        .filter(
            AmbulanceRequest.id == id,
            AmbulanceRequest.passenger_id == passenger.id,
        )
        .first()
    )
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    if request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending requests can be cancelled",
        )
    request.status = RequestStatus.CANCELLED
    db.commit()
    db.refresh(request)
    return request


# =========================
# DRIVER
# =========================
@router.get("/pending", response_model=list[RequestResponse])
def get_pending_requests(_: driver_dependency, db: db_dependency):
    return (
        db.query(AmbulanceRequest)
        .filter(AmbulanceRequest.status == RequestStatus.PENDING)
        .all()
    )


@router.post("/{id}/accept", response_model=RequestResponse)
def accept_request(
    driver: driver_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of request", example=1),
):
    request = db.query(AmbulanceRequest).filter(AmbulanceRequest.id == id).first()
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    if request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending"
        )

    ambulance = (
        db.query(Ambulance)
        .filter(
            Ambulance.driver_id == driver.id,
            Ambulance.status == AmbulanceStatus.AVAILABLE,
        )
        .first()
    )
    if ambulance is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No available ambulance assigned to you",
        )

    request.status = RequestStatus.ACCEPTED
    request.ambulance_id = ambulance.id
    ambulance.status = AmbulanceStatus.BUSY
    trip = Trip(
        request_id=request.id,
        passenger_id=request.passenger_id,
        driver_id=driver.id,
        ambulance_id=ambulance.id,
        status=TripStatus.ONGOING,
    )
    db.add(trip)
    db.commit()
    db.refresh(request)
    return request


@router.post("/{id}/reject", response_model=RequestResponse)
def reject_request(
    _: driver_dependency,
    db: db_dependency,
    id: int = Path(..., description="id of request", example=1),
):
    request = db.query(AmbulanceRequest).filter(AmbulanceRequest.id == id).first()
    if request is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )
    if request.status != RequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request is not pending"
        )

    request.status = RequestStatus.REJECTED
    db.commit()
    db.refresh(request)
    return request


# =========================
# ADMIN
# =========================
@router.get("/admin/all", response_model=list[RequestResponse])
def get_all_requests(admin: admin_dependency, db: db_dependency):
    return db.query(AmbulanceRequest).all()
