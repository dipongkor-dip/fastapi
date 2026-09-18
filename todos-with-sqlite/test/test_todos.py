from test.test_main import client
from main import app
from fastapi import status
from router.auth import decode_access_token
from database import SessionLocal
from models import Todos


def override_access_token():
    return {"id": 1, "username": "testUser", "role": "admin"}


def override_todo():
    db = SessionLocal()

    todo = Todos(
        title="testing",
        description="testing desc",
        priority=5,
        completed=True,
        user_id=1,
    )

    db.add(todo)
    db.commit()

    db.refresh(todo)  # Ensures the auto-generated id is loaded onto the object
    db.close()  # Clean up the session!

    return todo


app.dependency_overrides[decode_access_token] = override_access_token


def test_get_todos():
    response = client.get("/todos")
    assert response.status_code == status.HTTP_200_OK


def test_get_todo():
    db = SessionLocal()

    todo = db.query(Todos).filter(Todos.user_id == 1).order_by(Todos.id.desc()).first()
    db.close()  # Clean up the session right after querying!

    if todo is None:
        todo = override_todo()

    response = client.get(f"/todos/{todo.id}")
    assert response.status_code == status.HTTP_200_OK


def test_create_todo():
    db = SessionLocal()
    todo = db.query(Todos).filter(Todos.user_id == 1).order_by(Todos.id.asc()).first()

    if todo is not None:
        db.query(Todos).filter(Todos.id == todo.id).delete()
        db.commit()

    db.close()

    request_data = {
        "title": "testing title",
        "description": "testing desc again",
        "priority": 1,
        "completed": False,
        "user_id": 1,
    }
    response = client.post("/todos", json=request_data)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "To do created successfully"}


def test_update_todo():
    db = SessionLocal()
    todo = db.query(Todos).filter(Todos.user_id == 1).order_by(Todos.id.desc()).first()
    db.close()

    request_data = {"title": "testing title update"}
    response = client.put(f"/todos/{todo.id}", json=request_data)

    assert response.status_code == status.HTTP_200_OK


def test_delete_todo():
    db = SessionLocal()
    # Always ensure a todo exists before trying to delete it
    todo = db.query(Todos).filter(Todos.user_id == 1).order_by(Todos.id.desc()).first()
    db.close()

    if todo is None:
        todo = override_todo()

    response = client.delete(f"/todos/{todo.id}")
    assert response.status_code == status.HTTP_200_OK
