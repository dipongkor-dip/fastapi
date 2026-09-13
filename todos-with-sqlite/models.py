from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey


class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    completed = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"))


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    firstname = Column(String)
    lastname = Column(String)
    isActive = Column(Boolean, default=True)
    role = Column(String)
    password = Column(String)
