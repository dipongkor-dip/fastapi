from fastapi import FastAPI, Depends, HTTPException, Path, status
import models
from database import engine, SessionLocal
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from models import Books, Reservations
from router import admin, auth
from router.auth import decode_access_token
from fastapi.responses import JSONResponse

app = FastAPI()

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router, tags=["Users"])
# app.include_router(admin.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def start():
    return "Running library server"


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(decode_access_token)]


@app.get("/books/all")
def get_books(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    books = db.query(Books).all()

    return books


@app.get("/books/{id}")
def get_book(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of books", example=1),
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    book = db.query(Books).filter(Books.id == id).first()

    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return book


@app.post("/reserve/{id}")
def reserve_book(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of books", example=1),
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    book = db.query(Books).filter(Books.id == id).first()

    if book is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    reservation_model = Reservations(book_id=id, user_id=user.get("id"))

    db.add(reservation_model)

    db.commit()

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Book reserved successfully"},
    )


@app.delete("/reserve/cancel/{id}")
def cancel_reservation(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of reservations", example=1),
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    reservation = db.query(Reservations).filter(Reservations.id == id).first()

    if reservation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    reservation.status = "cancelled"

    db.commit()

    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content={"message": "Reservation cancelled successfully"},
    )


@app.get("/reserve")
def my_reservation(
    user: user_dependency,
    db: db_dependency,
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    reservations = (
        db.query(Reservations).filter(Reservations.user_id == user.get("id")).all()
    )

    return reservations
