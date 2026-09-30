from contextlib import asynccontextmanager

from fastapi import FastAPI

import models
from database import engine
from router import (
    admin,
    ambulance_requests,
    ambulances,
    auth,
    trips,
    users,
    payments,
    socialAuth,
)
from utils.bootstrap import create_default_superadmin
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from starlette.middleware.sessions import SessionMiddleware
from config import settings

@asynccontextmanager
async def lifespan(_: FastAPI):
    create_default_superadmin()
    yield


app = FastAPI(
    title="Ambulance Management System",
    version="1.0.0",
    lifespan=lifespan,
)

# 1. Trust proxy headers so FastAPI knows it's running on HTTPS when deployed
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    max_age=600,
    same_site="lax",
    https_only=settings.backend_url.startswith("https://"),
)

origins = ["http://localhost:5173", settings.frontend_url]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

models.Base.metadata.create_all(bind=engine)

# Routers /api/v1
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(socialAuth.router, prefix="/api/v1/auth", tags=["Social Authentication"])

app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])

app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])

app.include_router(ambulances.router, prefix="/api/v1/ambulances", tags=["Ambulances"])

app.include_router(
    ambulance_requests.router, prefix="/api/v1/requests", tags=["Ambulance Requests"]
)
app.include_router(trips.router, prefix="/api/v1/trips", tags=["Trips"])


app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])


@app.get("/")
def start():
    return {"message": "Ambulance Management Server Running"}
