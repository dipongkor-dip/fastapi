from database import Base
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    amount = Column(Float)
    type = Column(String(500))
    category = Column(String(250))
    date = Column(Date)
    user_id = Column(Integer, ForeignKey("user.id"))
