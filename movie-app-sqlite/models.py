from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Enum as SQLEnum
from enum import Enum

Base = declarative_base()


class Genre(Enum):
    action = "action"
    thriller = "thriller"
    comedy = "comedy"
    drama = "drama"


class Movies(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    director = Column(String)
    genre = Column(SQLEnum(Genre))
    duration = Column(Integer)
    rating = Column(Float)
