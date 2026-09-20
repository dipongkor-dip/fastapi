from fastapi import APIRouter, Depends, Path, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from database import SessionLocal
from models import Books, IssueRecords, Users, Reservations
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from router.auth import decode_access_token
from datetime import datetime, timedelta, timezone

router = APIRouter()
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl="login")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(decode_access_token)]


class BookCreate(BaseModel):
    title: str
    author: str
    category: str
    description: str = Field(default="", max_length=200)
    price: float = Field(default=0.9, ge=0)
    total_copies: int = Field(default=1, ge=0)


@router.post("/admin/books")
def create_book(user: user_dependency, db: db_dependency, new_book: BookCreate):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    book_model = Books(**new_book.model_dump(), available_copies=new_book.total_copies)

    db.add(book_model)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Book created successfully"},
    )


@router.get("/books")
def get_books(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    books = db.query(Books).all()
    return books


class UpdateBook(BaseModel):
    title: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    price: Optional[float] = Field(default=None, ge=0)
    total_copies: Optional[int] = Field(default=None, ge=0)
    available_copies: Optional[int] = Field(default=None, ge=0)


@router.put("/admin/books/{id}")
def update_book(
    user: user_dependency,
    db: db_dependency,
    payload: UpdateBook,
    id: int = Path(description="id of books", example=1),
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    book = db.query(Books).filter(Books.id == id).first()

    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    update_book = payload.model_dump(exclude_unset=True)

    for k, v in update_book.items():
        setattr(book, k, v)

    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Book updated successfully"},
    )


@router.delete("/admin/books/{id}")
def delete_book(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of books", example=1),
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    book = db.query(Books).filter(Books.id == id).first()

    if book is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    db.query(Books).filter(Books.id == id).delete()

    db.commit()

    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content={"message": "Book deleted successfully"},
    )


class IssueBook(BaseModel):
    book_id: int
    user_id: int


@router.post("/admin/books")
def create_book(user: user_dependency, db: db_dependency, new_issue: IssueBook):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    book = db.query(Books).filter(Books.id == new_issue.book_id).first()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Book Not found"
        )

    u = db.query(Users).filter(Users.id == new_issue.user_id).first()
    if u is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User Not found"
        )

    if book.available_copies <= 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No Copies Available"
        )

    loan_days = 10
    issue_date = datetime.now

    issue_model = IssueRecords(
        book_id=new_issue.book_id,
        user_id=new_issue.user_id,
        issue_date=datetime.now,
        due_date=issue_date + timedelta(days=loan_days),
    )

    book.available_copies -= 1

    reservation = (
        db.query(Reservations)
        .filter(
            Reservations.book_id == new_issue.book_id,
            Reservations.user_id == new_issue.user_id,
            Reservations.status == "pending",
        )
        .first()
    )

    if reservation is not None:
        reservation.status = "approved"

    db.add(issue_model)
    db.commit()

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "Book issued successfully"},
    )


def calculate_fine(due_date: datetime, return_date: datetime):
    overdue_days = (return_date.date() - due_date.date()).days
    FINE_PER_DAY = 20

    if overdue_days > 0:
        return round(overdue_days * FINE_PER_DAY, 2)
    else:
        return 0.00


@router.put("/admin/books/{id}")
def return_book(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of issues", example=1),
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    issue = db.query(IssueRecords).filter(IssueRecords.id == id).first()
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    return_date = datetime.now
    fine = calculate_fine(issue.due_date, return_date)

    issue.return_date = return_date
    issue.status = "returned"
    issue.fine_amount = fine

    book = db.query(Books).filter(Books.id == issue.book_id).first()
    if book is not None:
        book.available_copies += 1

    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Book returned successfully", "fine_amount": fine},
    )


@router.put("/admin/fine/pay/{id}")
def fine_paid(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of issues", example=1),
):
    if user is None or user.get("role") != "librarian":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    issue = db.query(IssueRecords).filter(IssueRecords.id == id).first()
    if issue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    issue.fine_paid = True

    db.commit()

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Fine paid successfully"},
    )
