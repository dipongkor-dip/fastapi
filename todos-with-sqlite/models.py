from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(String(500))
    priority = Column(Integer)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True)
    username = Column(String(100), unique=True)
    firstname = Column(String(100))
    lastname = Column(String(100))
    isActive = Column(Boolean, default=True)
    role = Column(String(50))
    password = Column(String(255))
    phone = Column(String(20))