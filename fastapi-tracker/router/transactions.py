from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field, ConfigDict
from database import SessionLocal
from typing import Annotated, Literal, Optional, List
from sqlalchemy.orm import Session
from router.users import decode_access_token
from models import Transaction
from fastapi.responses import JSONResponse
from datetime import date

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(decode_access_token)]


class CreateTransaction(BaseModel):
    title: str
    amount: float = Field(gt=0, description="Amount must be greater than zero")
    type: Literal["income", "expense"]
    category: str


class TransactionResponse(BaseModel):
    id: int
    title: str
    amount: float
    type: Literal["income", "expense"]
    category: str
    date: date
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class TransactionWithResponse(BaseModel):
    message: str
    transaction: TransactionResponse


@router.post(
    "", status_code=status.HTTP_201_CREATED, response_model=TransactionWithResponse
)
def create_transaction(
    user: user_dependency, db: db_dependency, payload: CreateTransaction
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    transaction_model = Transaction(
        **payload.model_dump(), user_id=user.get("id"), date=date.today()
    )
    db.add(transaction_model)
    db.commit()
    db.refresh(transaction_model)

    return {
        "message": "Transactions created successfully",
        "transaction": transaction_model,
    }


class TransactionListResponse(BaseModel):
    message: str
    transactions: List[TransactionResponse]


@router.get("", status_code=status.HTTP_200_OK, response_model=TransactionListResponse)
def my_transactions(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    data = db.query(Transaction).filter(Transaction.user_id == user.get("id")).all()

    return {"message": "Transactions retrieved successfully", "transactions": data}


@router.get(
    "/{id}", status_code=status.HTTP_200_OK, response_model=TransactionWithResponse
)
def get_transaction(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of transactions", example=1),
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    data = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.get("id"))
        .filter(Transaction.id == id)
        .first()
    )
    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    return {"message": "Transaction retrieved successfully", "transaction": data}


class UpdateTransaction(BaseModel):
    title: Optional[str] = None
    amount: float = Field(
        default=None, gt=0, description="Amount must be greater than zero"
    )
    type: Literal["income", "expense"] = None
    category: Optional[str] = None


@router.put(
    "/{id}", status_code=status.HTTP_200_OK, response_model=TransactionWithResponse
)
def update_transaction(
    user: user_dependency,
    db: db_dependency,
    payload: UpdateTransaction,
    id: int = Path(description="id of transactions", example=1),
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    data = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.get("id"))
        .filter(Transaction.id == id)
        .first()
    )

    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    update_data = payload.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(data, k, v)  # e.g todo.title = update_title

    db.commit()
    db.refresh(data)

    return {
        "message": "Transactions updated successfully",
        "transaction": data,
    }


@router.delete("/{id}")
def delete_transaction(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of transactions", example=1),
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    data = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.get("id"))
        .filter(Transaction.id == id)
        .first()
    )

    if data is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    db.query(Transaction).filter(Transaction.user_id == user.get("id")).filter(
        Transaction.id == id
    ).delete()

    db.commit()

    return JSONResponse({"message": "deleted successfully"}, status.HTTP_200_OK)


from typing import Optional, Literal


@router.get("/filter", status_code=status.HTTP_200_OK, response_model=TransactionListResponse)
def get_transactions(
    user: user_dependency,
    db: db_dependency,
    type: Optional[Literal["income", "expense"]] = None,
    category: Optional[str] = None,
    minimum_amount: Optional[float] = None,
    maximum_amount: Optional[float] = None,
):
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized user")

    query = (
        db.query(Transaction)
        .filter(Transaction.user_id == user.get("id"))
        .order_by(Transaction.date.desc())
    )

    # Conditionally apply filters
    if type is not None:
        query = query.filter(Transaction.type == type)

    if category is not None:
        query = query.filter(Transaction.category == category)

    if minimum_amount is not None:
        query = query.filter(Transaction.amount >= minimum_amount)

    if maximum_amount is not None:
        query = query.filter(Transaction.amount <= maximum_amount)

    # Execute query
    data = query.all()

    return {"message": "Transactions retrieved successfully", "transactions": data}
