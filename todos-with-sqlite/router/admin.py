from fastapi import APIRouter, Depends, HTTPException, Path
from database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from router.auth import decode_access_token
from models import Users, Todos
from fastapi.responses import JSONResponse

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(decode_access_token)]


@router.get("/admin/users")
def get_users(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(401, "Authentication Failed")

    return db.query(Users).all()


@router.get("/admin/todos")
def get_todos(user: user_dependency, db: db_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(401, "Authentication Failed")

    return db.query(Todos).all()


@router.delete("/admin/todos/{id}")
def get_todos(
    user: user_dependency,
    db: db_dependency,
    id: int = Path(description="id of todos", example=1),
):
    if user is None or user.get("role") != "admin":
        raise HTTPException(401, "Authentication Failed")

    todo = db.query(Todos).filter(Todos.id == id).first()

    if todo is None:
        raise HTTPException(404, "Not found")

    db.query(Todos).filter(Todos.id == id).delete()

    db.commit()

    return JSONResponse(content={"message": "deleted successfully"}, status_code=200)
