from __future__ import annotations

from typing import Optional, List, Annotated
from uuid import UUID, uuid4
from datetime import date
from pydantic import BaseModel, Field, StringConstraints
from decimal import Decimal

# ISBN-13 format validation
ISBNType = Annotated[str, StringConstraints(pattern=r"^978\d{10}$")]


class BookBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent Book ID (server-generated).",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440001"},
    )
    isbn: ISBNType = Field(
        ...,
        description="ISBN-13 number (978 followed by 10 digits).",
        json_schema_extra={"example": "9781234567890"},
    )
    title: str = Field(
        ...,
        description="Book title.",
        json_schema_extra={"example": "Introduction to Cloud Computing"},
    )
    author: str = Field(
        ...,
        description="Primary author name.",
        json_schema_extra={"example": "John Smith"},
    )
    co_authors: List[str] = Field(
        default_factory=list,
        description="List of co-authors.",
        json_schema_extra={"example": ["Jane Doe", "Bob Johnson"]},
    )
    publisher: str = Field(
        ...,
        description="Publishing company.",
        json_schema_extra={"example": "Tech Publications"},
    )
    publication_date: date = Field(
        ...,
        description="Date of publication (YYYY-MM-DD).",
        json_schema_extra={"example": "2023-01-15"},
    )
    edition: Optional[int] = Field(
        None,
        description="Edition number.",
        json_schema_extra={"example": 3},
    )
    pages: Optional[int] = Field(
        None,
        description="Number of pages.",
        json_schema_extra={"example": 456},
    )
    price: Optional[Decimal] = Field(
        None,
        description="Book price in USD.",
        json_schema_extra={"example": 89.99},
    )
    genre: Optional[str] = Field(
        None,
        description="Book genre or category.",
        json_schema_extra={"example": "Computer Science"},
    )
    available: bool = Field(
        default=True,
        description="Whether the book is currently available.",
        json_schema_extra={"example": True},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "isbn": "9781234567890",
                    "title": "Introduction to Cloud Computing",
                    "author": "John Smith",
                    "co_authors": ["Jane Doe"],
                    "publisher": "Tech Publications",
                    "publication_date": "2023-01-15",
                    "edition": 3,
                    "pages": 456,
                    "price": 89.99,
                    "genre": "Computer Science",
                    "available": True,
                }
            ]
        }
    }


class BookCreate(BaseModel):
    isbn: ISBNType = Field(
        ...,
        description="ISBN-13 number (978 followed by 10 digits).",
    )
    title: str = Field(..., description="Book title.")
    author: str = Field(..., description="Primary author name.")
    co_authors: List[str] = Field(default_factory=list, description="List of co-authors.")
    publisher: str = Field(..., description="Publishing company.")
    publication_date: date = Field(..., description="Date of publication (YYYY-MM-DD).")
    edition: Optional[int] = Field(None, description="Edition number.")
    pages: Optional[int] = Field(None, description="Number of pages.")
    price: Optional[Decimal] = Field(None, description="Book price in USD.")
    genre: Optional[str] = Field(None, description="Book genre or category.")
    available: bool = Field(default=True, description="Whether the book is currently available.")


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Book title.")
    author: Optional[str] = Field(None, description="Primary author name.")
    co_authors: Optional[List[str]] = Field(None, description="List of co-authors.")
    publisher: Optional[str] = Field(None, description="Publishing company.")
    publication_date: Optional[date] = Field(None, description="Date of publication (YYYY-MM-DD).")
    edition: Optional[int] = Field(None, description="Edition number.")
    pages: Optional[int] = Field(None, description="Number of pages.")
    price: Optional[Decimal] = Field(None, description="Book price in USD.")
    genre: Optional[str] = Field(None, description="Book genre or category.")
    available: Optional[bool] = Field(None, description="Whether the book is currently available.")
