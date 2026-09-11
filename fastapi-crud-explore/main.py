from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from fastapi.responses import JSONResponse
import json

app = FastAPI()


@app.get("/")
def hello():
    return "Student Manager System API"


@app.get("/about")
def about():
    return "About page"


def load_data():
    with open("students.json", "r") as f:
        return json.load(f)


def save_data(data):
    with open("students.json", "w") as f:
        json.dump(data, f, indent=2)


@app.get("/students")
def view_students():
    return load_data()


@app.get("/students/{id}")
def get_student(id: str = Path(..., description="id of students", example="S001")):
    data = load_data()
    if id in data:
        return data[id]
    raise HTTPException(status_code=404, detail="Student not found")


@app.get("/data")
def view_data(
    sorted_by: str = Query(..., description="sort on the basis of class, roll, age"),
    order: str = Query("asc", description="choose order : asc or desc"),
):
    fields = ["class", "roll", "age"]

    if sorted_by not in fields:
        raise HTTPException(404, f"Invalid field, select from {fields}")

    if order not in ["asc", "desc"]:
        raise HTTPException(404, "Choose between asc or desc")

    data = load_data()
    result = list(data.values())
    result.sort(key=lambda x: x[sorted_by], reverse=order == "desc")
    return result


Score = Annotated[int, Field(..., ge=0, le=100)]


class Marks(BaseModel):
    math: Score
    science: Score
    english: Score


class Student(BaseModel):
    id: Annotated[str, Field(..., description="id of students", examples=["S001"])]
    name: Annotated[str, Field(..., description="Student name")]
    class_n: Annotated[int, Field(..., ge=1, le=100)]
    roll: Annotated[int, Field(..., gt=0, lt=101)]
    marks: Marks
    phone: Annotated[str, Field(..., pattern=r"^(013|017|016|018|019|014|015)\d{8}$")]
    age: Annotated[int, Field(..., ge=5, le=20)]


ScoreU = Annotated[Optional[int], Field(default=None)]


class MarksU(BaseModel):
    math: ScoreU
    science: ScoreU
    english: ScoreU


class StudentUpdate(BaseModel):
    id: Annotated[Optional[str], Field(default=None)]
    name: Annotated[Optional[str], Field(default=None)]
    class_n: Annotated[Optional[int], Field(default=None)]
    roll: Annotated[Optional[int], Field(default=None)]
    marks: MarksU
    phone: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None)]


@app.post("/students")
def create_student(student: Student):
    data = load_data()
    stu_id = student.id

    if stu_id in data:
        raise HTTPException(400, "Student with this id already exists")

    student_dict = student.model_dump(exclude=["id"])

    # id is used as the key, not stored in the value
    # del student_dict["id"] # alternative exclude

    data[stu_id] = student_dict

    save_data(data)
    return JSONResponse(
        status_code=201,
        content="Student created successfully",
    )


@app.put("/students/{id}")
def update_student(
    student: Student, id: str = Path(..., description="id of students", example="S001")
):
    data = load_data()

    if id not in data:
        raise HTTPException(404, "Student not found")

    # exclude_unset just given value update
    data[id].update(student.model_dump(exclude_unset=True))

    save_data(data)
    return JSONResponse(
        status_code=200,
        content="Student updated successfully",
    )


@app.delete("/students/{id}")
def delete_student(id: str = Path(..., description="id of students", example="S001")):
    data = load_data()

    if id not in data:
        raise HTTPException(404, "Student not found")

    del data[id]

    save_data(data)
    return JSONResponse(
        status_code=200,
        content="Student deleted",
    )
