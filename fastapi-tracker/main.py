from fastapi import FastAPI, Depends
import models
from database import engine
from router import users, transactions

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


app.include_router(users.router, prefix="/auth", tags=["Users"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])


@app.get("/")
def start():
    return "Running Tracker Server"
