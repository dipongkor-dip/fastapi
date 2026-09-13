from fastapi import FastAPI, Depends, HTTPException, Path
import models
from database import engine, SessionLocal
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from models import Todos
from pydantic import BaseModel, Field
from fastapi.responses import JSONResponse
from router import auth


app = FastAPI()

models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)



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
def get_todo(db: db_dependency, id: int = Path(description="id of todos", example=101)):
    data = db.query(Todos).filter(Todos.id == id).first()
    if data is not None:
        return data
    else:
        raise HTTPException(404, "Not found")


class Todo(BaseModel):
    title: str
    description: str = Field(max_length=100)
    priority: int = Field(gt=0, le=5)
    user_id : int


@app.post("/todos")
def create_todo(db: db_dependency, new_todo: Todo):
    todo_model = Todos(**new_todo.model_dump())
    db.add(todo_model)
    db.commit()

    return JSONResponse(
        content={"message": "To do created successfully"}, status_code=201
    )


class TodoUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str] = Field(default=None, max_length=100)
    priority: Optional[int] = Field(default=None, gt=0, le=5)
    completed: Optional[bool]


@app.put("/todos/{id}")
def update_todo(
    db: db_dependency,
    update_todo: TodoUpdate,
    id: int = Path(description="id of todos", example=1),
):

    todo = db.query(Todos).filter(Todos.id == id).first()
    if todo is None:
        raise HTTPException(404, "Not found")

    update_data = update_todo.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(todo, k, v)  # e.g todo.title = update_title

    db.commit()

    return JSONResponse({"message": "updated successfully"}, 200)


@app.delete("/todos/{id}")
def delete_todo(
    db: db_dependency,
    id: int = Path(description="id of todos", example=1),
):
    todo = db.query(Todos).filter(Todos.id == id).first()

    if todo is None:
        raise HTTPException(404, "Not found")

    db.query(Todos).filter(Todos.id == id).delete()

    db.commit()

    return JSONResponse({"message": "deleted successfully"}, 200)
