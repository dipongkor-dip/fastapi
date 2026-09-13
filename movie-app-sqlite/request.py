from pydantic import BaseModel, Field, StrictInt, StrictFloat
from enum import Enum
from typing import Annotated, Optional


class Genre(str, Enum):
    ACTION = "action"
    THRILLER = "thriller"
    COMEDY = "comedy"
    DRAMA = "drama"


class CreateMovie(BaseModel):
    id: Annotated[int, Field(..., example=1)]
    title: Annotated[str, Field(..., example="Hero Number 1")]
    director: Annotated[str, Field(..., example="Bunny")]
    genre: Annotated[Genre, Field(..., example="action")]
    duration: Annotated[int, Field(..., ge=0, example=10)]
    rating: Annotated[float, Field(..., ge=0, le=5, example=4.5)]


class UpdateMovie(BaseModel):
    title: Annotated[Optional[str], Field(default=None)]
    director: Annotated[Optional[str], Field(default=None)]
    genre: Annotated[Optional[Genre], Field(default=None)]
    duration: Annotated[Optional[int], Field(default=None, ge=0)]
    rating: Annotated[Optional[float], Field(default=None, ge=0, le=5)]
