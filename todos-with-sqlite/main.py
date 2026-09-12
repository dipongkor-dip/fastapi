from fastapi import FastAPI, Depends, HTTPException
import models
from database import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from models import Todos
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def start():
    return "Running todos server"


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/todos")
def get_todos(db: db_dependency):
    return db.query(Todos).all()


@app.get("/todos/{id}")
def get_todo(db: db_dependency, id: int):
    data = db.query(Todos).filter(Todos.id == id).first()
    if data is not None:
        return data
    else:
        raise HTTPException(404, "Not found")


class Todo(BaseModel):
    id: int
    title: str
    description: str = Field(max_length=100)
    priority: int = Field(gt=0, le=5)
    completed: bool = Field(default=False)


@app.post("/todos")
def create_todo(db: db_dependency, new_todo: Todo):
    todo_model = Todos(**new_todo.model_dump())
    db.add(todo_model)
    db.commit()

    return JSONResponse(
        content={"message": "To do created successfully"}, status_code=201
    )
