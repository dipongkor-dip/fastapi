from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from enums import (
    UserRole,
    AmbulanceStatus,
    RequestStatus,
    TripStatus,
)


# ========================= # AUTH # =========================
class RegisterUser(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    firstname: str
    lastname: str
    password: str = Field(min_length=6)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class OAuthCodeExchange(BaseModel):
    code: str


# ========================= # USER # =========================
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    firstname: str
    lastname: str
    role: UserRole
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UsernameAvailabilityResponse(BaseModel):
    available: bool


class UpdateUser(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=100)
    firstname: str | None = None
    lastname: str | None = None
    email: EmailStr | None = None


class PasswordStatusResponse(BaseModel):
    has_password: bool


class SetPasswordRequest(BaseModel):
    new_password: str = Field(min_length=6)


# ========================= # DRIVER # =========================
class CreateDriver(BaseModel):
    username: str = Field(min_length=3)
    email: EmailStr
    firstname: str
    lastname: str
    password: str = Field(min_length=6)


# ========================= # AMBULANCE # =========================
class CreateAmbulance(BaseModel):
    ambulance_number: str
    ambulance_type: str
    model: str | None = None
    capacity: int = Field(default=1, ge=1)
    driver_id: int | None = None


class UpdateAmbulance(BaseModel):
    ambulance_type: str | None = None
    model: str | None = None
    capacity: int | None = Field(
        default=None,
        ge=1,
    )
    driver_id: int | None = None
    status: AmbulanceStatus | None = None


class AmbulanceResponse(BaseModel):
    id: int

    ambulance_number: str
    ambulance_type: str
    model: str | None
    capacity: int
    status: AmbulanceStatus
    driver_id: int | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PaginatedAmbulanceResponse(BaseModel):
    items: list[AmbulanceResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ========================= # AMBULANCE REQUEST # =========================
class CreateAmbulanceRequest(BaseModel):
    pickup_location: str
    destination: str


class RequestResponse(BaseModel):
    id: int
    passenger_id: int
    ambulance_id: int | None
    pickup_location: str
    destination: str
    status: RequestStatus
    request_time: datetime
    model_config = ConfigDict(from_attributes=True)


# ========================= # TRIP # =========================
class TripResponse(BaseModel):
    id: int
    request_id: int
    passenger_id: int
    driver_id: int
    ambulance_id: int
    status: TripStatus
    start_time: datetime | None
    end_time: datetime | None
    fare: float
    model_config = ConfigDict(from_attributes=True)


class UpdateFare(BaseModel):
    fare: float = Field(ge=0)


class VerifyOTP(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


# ========================= # PAYMENT # =========================
class PaymentResponse(BaseModel):
    id: int
    trip_id: int
    amount: float
    status: str
    payment_url: str
