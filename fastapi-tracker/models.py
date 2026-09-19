from database import Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Enum as SQLEnum,
    CheckConstraint,
)
import enum


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    amount = Column(Float, nullable=False)
    type = Column(SQLEnum(TransactionType), nullable=False)
    category = Column(String(250))
    date = Column(Date)
    user_id = Column(Integer, ForeignKey("user.id"))

    # Enforces at the database level that amount must be greater than 0
    __table_args__ = (CheckConstraint("amount > 0", name="check_amount_positive"),)
