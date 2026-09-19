from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from datetime import datetime


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    firstname = Column(String)
    lastname = Column(String)
    password = Column(String)
    isActive = Column(Boolean, default=True)
    role = Column(String)  # librarian or member


class Books(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    author = Column(String)
    category = Column(String)
    description = Column(String)
    price = Column(Float, default=0.0)
    total_copies = Column(Integer, default=5)
    available_copies = Column(Integer, default=3)
    image = Column(String, nullable=True)
    createAt = Column(DateTime, default=datetime.now)


class Reservations(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")
    date = Column(DateTime, default=datetime.now)
