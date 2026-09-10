from fastapi import FastAPI, Path, HTTPException, Query, Body
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
        data = json.load(f)
    return data


@app.get("/students")
def view_students():
    return load_data()


@app.get("/students/{id}")
def get_student(id: str = Path(..., description="id of students", example="S001")):
    data = load_data()
    if id in data:
        return data[id]
    else:
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

    sorted = list(data.values())

    sorted.sort(key=lambda x: x[sorted_by], reverse=order == "desc")

    return sorted


def save_data(data):
    with open("students.json", "w") as f:
        json.dump(data, f)


@app.post("/students")
def create_student(student: dict = Body()):
    data = load_data()

    stu_id = student["id"]

    data[stu_id] = student

    del data[stu_id]["id"]

    save_data(data)

    return {"message": "Student created successfully", "student": student}
