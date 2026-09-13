from fastapi import FastAPI, Depends, Path, HTTPException, Query
import models
from db import engine, SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from models import Movies
from request import CreateMovie, UpdateMovie

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@app.get("/")
def root():
    return JSONResponse({"message": "Movies app server is running"}, 200)


@app.get("/movies/sort")
def all_movies(
    db: db_dependency,
    sorted_by: str = Query(..., description="sort on the basis of duration, rating"),
    order: str = Query("asc", description="choose order : asc or desc"),
):
    fields = ["duration", "rating"]

    if sorted_by not in fields:
        raise HTTPException(404, f"Invalid field, select from {fields}")

    if order not in ["asc", "desc"]:
        raise HTTPException(404, "Choose between asc or desc")

    sort_fields = {"duration": Movies.duration, "rating": Movies.rating}

    column = sort_fields[sorted_by]

    result = (
        db.query(Movies)
        .order_by(column.asc() if order == "asc" else column.desc())
        .all()
    )

    return result


@app.post("/create_movies")
def create_movie(db: db_dependency, payload: CreateMovie):
    mod = Movies(**payload.model_dump())
    db.add(mod)
    db.commit()

    return JSONResponse({"message": "Movie created successfully"}, 201)


@app.get("/movies")
def get_movies(db: db_dependency):
    data = db.query(Movies).all()
    return data


@app.get("/movies/{id}")
def get_movie(
    db: db_dependency, id: int = Path(..., description="id of movies", example=1)
):
    data = db.query(Movies).filter(Movies.id == id).first()
    if data is None:
        return JSONResponse({"message": "Not found"}, 404)
    return data


@app.put("/movies/{id}")
def update_movie(
    db: db_dependency,
    payload: UpdateMovie,
    id: int = Path(..., description="id of movies", example=1),
):
    movie = db.query(Movies).filter(Movies.id == id).first()
    if movie is None:
        raise HTTPException(404, "Not found")

    update_data = payload.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(movie, k, v)  # e.g todo.title = update_title

    db.commit()

    return JSONResponse({"message": "Movie updated successfully"}, 200)


@app.delete("/movies/{id}")
def delete_movie(
    db: db_dependency, id: int = Path(..., description="id of movies", example=1)
):
    movie = db.query(Movies).filter(Movies.id == id).first()
    if movie is None:
        raise HTTPException(404, "Not found")

    db.query(Movies).filter(Movies.id == id).delete()

    db.commit()
    return JSONResponse({"message": "Deleted successfully"}, 200)
