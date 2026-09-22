from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Numeric,
)
from database import Base
from enums import (
    UserRole,
    AmbulanceStatus,
    RequestStatus,
    TripStatus,
    PaymentStatus,
    PaymentMethod,
)


def utc_now():
    return datetime.now(timezone.utc)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    firstname = Column(String(100), nullable=False)
    lastname = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.PASSENGER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class Ambulance(Base):
    __tablename__ = "ambulances"

    id = Column(Integer, primary_key=True, index=True)
    ambulance_number = Column(String(50), unique=True, nullable=False, index=True)
    ambulance_type = Column(String(100), nullable=False)
    model = Column(String(100), nullable=True)
    capacity = Column(Integer, default=1, nullable=False)
    status = Column(
        SQLEnum(AmbulanceStatus), default=AmbulanceStatus.AVAILABLE, nullable=False
    )
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)


class AmbulanceRequest(Base):
    __tablename__ = "ambulance_requests"

    id = Column(Integer, primary_key=True, index=True)
    passenger_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"), nullable=True)
    pickup_location = Column(String(500), nullable=False)
    destination = Column(String(500), nullable=False)
    status = Column(
        SQLEnum(RequestStatus), default=RequestStatus.PENDING, nullable=False
    )
    request_time = Column(DateTime, default=utc_now, nullable=False)


class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(
        Integer, ForeignKey("ambulance_requests.id"), nullable=False, unique=True
    )
    passenger_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ambulance_id = Column(Integer, ForeignKey("ambulances.id"), nullable=False)
    status = Column(SQLEnum(TripStatus), default=TripStatus.ONGOING, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    fare = Column(Numeric(10, 2), default=0.00, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    trip_id = Column(Integer, ForeignKey("trips.id"), nullable=False, unique=True)
    passenger_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(
        SQLEnum(PaymentMethod), default=PaymentMethod.SSLCOMMERZ, nullable=False
    )
    status = Column(
        SQLEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False
    )
    transaction_id = Column(String(100), unique=True, nullable=True, index=True)
    ssl_session_key = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    receipt_url = Column(String(500), nullable=True)
