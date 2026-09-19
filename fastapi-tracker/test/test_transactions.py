from fastapi.testclient import TestClient
from main import app
from fastapi import status
from router.users import decode_access_token
from database import SessionLocal
from models import Transaction
from main import app
from datetime import date

client = TestClient(app)


def override_access_token():
    return {"id": 1, "username": "dip"}


def override_transaction():
    db = SessionLocal()

    traction = Transaction(
        title="testing transaction",
        amount=100.00,
        type="income",
        category="Phone",
        date=date.today(),  # Crucial: response_model requires this field!
        user_id=1,
    )

    db.add(traction)
    db.commit()
    db.refresh(traction)  # Ensures ID and attributes populate fully
    db.close()

    return traction


app.dependency_overrides[decode_access_token] = override_access_token


def test_my_transactions():
    response = client.get("/transactions")
    assert response.status_code == status.HTTP_200_OK


def test_get_transaction():
    db = SessionLocal()

    transaction = (
        db.query(Transaction)
        .filter(Transaction.user_id == 1)
        .order_by(Transaction.id.desc())
        .first()
    )

    db.close()

    if transaction is None:
        transaction = override_transaction()

    response = client.get(f"/transactions/{transaction.id}")
    assert response.status_code == status.HTTP_200_OK


def test_create_transaction():
    db = SessionLocal()

    todo = (
        db.query(Transaction)
        .filter(Transaction.user_id == 1)
        .order_by(Transaction.id.desc())
        .first()
    )

    if todo is not None:
        db.query(Transaction).filter(Transaction.id == todo.id).delete()
        db.commit()

    db.close()

    request_data = {
        "title": "testing transaction post",
        "amount": 200.00,
        "type": "income",
        "category": "Laptop",
        "user_id": 1,
    }
    response = client.post("/transactions", json=request_data)
    assert response.status_code == status.HTTP_201_CREATED


def test_update_transaction():
    db = SessionLocal()

    todo = (
        db.query(Transaction)
        .filter(Transaction.user_id == 1)
        .order_by(Transaction.id.desc())
        .first()
    )
    db.close()

    request_data = {
        "title": "testing transaction post update",
        "amount": 300.00,
    }

    response = client.put(f"/transactions/{todo.id}", json=request_data)
    assert response.status_code == status.HTTP_200_OK


def test_delete_transaction():
    db = SessionLocal()

    todo = (
        db.query(Transaction)
        .filter(Transaction.user_id == 1)
        .order_by(Transaction.id.desc())
        .first()
    )
    db.close()

    response = client.delete(f"/transactions/{todo.id}")
    assert response.status_code == status.HTTP_200_OK
