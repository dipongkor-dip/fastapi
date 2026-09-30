from fastapi import APIRouter, HTTPException, Path, Query, status
from sqlalchemy import or_
from models import Ambulance
from schemas import AmbulanceResponse, PaginatedAmbulanceResponse
from enums import AmbulanceStatus
from utils.auth import driver_dependency, db_dependency

router = APIRouter()


@router.get("/", response_model=PaginatedAmbulanceResponse)
def get_ambulances(
    db: db_dependency,
    status: AmbulanceStatus | None = None,
    search: str | None = Query(default=None, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=100),
):
    query = db.query(Ambulance)
    if status is not None:
        query = query.filter(Ambulance.status == status)
    search_term = search.strip() if search else ""
    if search_term:
        pattern = f"%{search_term}%"
        query = query.filter(
            or_(
                Ambulance.ambulance_number.ilike(pattern),
                Ambulance.ambulance_type.ilike(pattern),
                Ambulance.model.ilike(pattern),
            )
        )

    total = query.count()
    items = (
        query.order_by(Ambulance.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


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
