from __future__ import annotations

from typing import Optional, List, Annotated
from uuid import UUID, uuid4
from datetime import date, time
from pydantic import BaseModel, Field, StringConstraints
from enum import Enum

# Columbia course code format: 4-letter department + 4-digit number
CourseCodeType = Annotated[str, StringConstraints(pattern=r"^[A-Z]{4}\d{4}$")]


class Semester(str, Enum):
    FALL = "Fall"
    SPRING = "Spring"
    SUMMER = "Summer"


class DayOfWeek(str, Enum):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class CourseBase(BaseModel):
    id: UUID = Field(
        default_factory=uuid4,
        description="Persistent Course ID (server-generated).",
        json_schema_extra={"example": "550e8400-e29b-41d4-a716-446655440002"},
    )
    course_code: CourseCodeType = Field(
        ...,
        description="Course code (4-letter department + 4-digit number).",
        json_schema_extra={"example": "COMS4111"},
    )
    title: str = Field(
        ...,
        description="Course title.",
        json_schema_extra={"example": "Introduction to Databases"},
    )
    description: Optional[str] = Field(
        None,
        description="Course description.",
        json_schema_extra={"example": "An introduction to database concepts and SQL."},
    )
    instructor: str = Field(
        ...,
        description="Primary instructor name.",
        json_schema_extra={"example": "Dr. Jane Smith"},
    )
    credits: int = Field(
        ...,
        ge=1,
        le=6,
        description="Number of credit hours (1-6).",
        json_schema_extra={"example": 3},
    )
    semester: Semester = Field(
        ...,
        description="Semester when the course is offered.",
        json_schema_extra={"example": "Fall"},
    )
    year: int = Field(
        ...,
        ge=2020,
        le=2030,
        description="Academic year.",
        json_schema_extra={"example": 2024},
    )
    max_enrollment: Optional[int] = Field(
        None,
        ge=1,
        description="Maximum number of students that can enroll.",
        json_schema_extra={"example": 150},
    )
    current_enrollment: int = Field(
        default=0,
        ge=0,
        description="Current number of enrolled students.",
        json_schema_extra={"example": 87},
    )
    meeting_days: List[DayOfWeek] = Field(
        default_factory=list,
        description="Days of the week when the course meets.",
        json_schema_extra={"example": ["Monday", "Wednesday"]},
    )
    start_time: Optional[time] = Field(
        None,
        description="Course start time.",
        json_schema_extra={"example": "10:10:00"},
    )
    end_time: Optional[time] = Field(
        None,
        description="Course end time.",
        json_schema_extra={"example": "11:25:00"},
    )
    location: Optional[str] = Field(
        None,
        description="Classroom or meeting location.",
        json_schema_extra={"example": "Hamilton 717"},
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="List of prerequisite course codes.",
        json_schema_extra={"example": ["COMS1004", "COMS3134"]},
    )
    active: bool = Field(
        default=True,
        description="Whether the course is currently active/offered.",
        json_schema_extra={"example": True},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440002",
                    "course_code": "COMS4111",
                    "title": "Introduction to Databases",
                    "description": "An introduction to database concepts and SQL.",
                    "instructor": "Dr. Jane Smith",
                    "credits": 3,
                    "semester": "Fall",
                    "year": 2024,
                    "max_enrollment": 150,
                    "current_enrollment": 87,
                    "meeting_days": ["Monday", "Wednesday"],
                    "start_time": "10:10:00",
                    "end_time": "11:25:00",
                    "location": "Hamilton 717",
                    "prerequisites": ["COMS1004", "COMS3134"],
                    "active": True,
                }
            ]
        }
    }


class CourseCreate(BaseModel):
    course_code: CourseCodeType = Field(
        ...,
        description="Course code (4-letter department + 4-digit number).",
    )
    title: str = Field(..., description="Course title.")
    description: Optional[str] = Field(None, description="Course description.")
    instructor: str = Field(..., description="Primary instructor name.")
    credits: int = Field(..., ge=1, le=6, description="Number of credit hours (1-6).")
    semester: Semester = Field(..., description="Semester when the course is offered.")
    year: int = Field(..., ge=2020, le=2030, description="Academic year.")
    max_enrollment: Optional[int] = Field(None, ge=1, description="Maximum number of students that can enroll.")
    current_enrollment: int = Field(default=0, ge=0, description="Current number of enrolled students.")
    meeting_days: List[DayOfWeek] = Field(default_factory=list, description="Days of the week when the course meets.")
    start_time: Optional[time] = Field(None, description="Course start time.")
    end_time: Optional[time] = Field(None, description="Course end time.")
    location: Optional[str] = Field(None, description="Classroom or meeting location.")
    prerequisites: List[str] = Field(default_factory=list, description="List of prerequisite course codes.")
    active: bool = Field(default=True, description="Whether the course is currently active/offered.")


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Course title.")
    description: Optional[str] = Field(None, description="Course description.")
    instructor: Optional[str] = Field(None, description="Primary instructor name.")
    credits: Optional[int] = Field(None, ge=1, le=6, description="Number of credit hours (1-6).")
    semester: Optional[Semester] = Field(None, description="Semester when the course is offered.")
    year: Optional[int] = Field(None, ge=2020, le=2030, description="Academic year.")
    max_enrollment: Optional[int] = Field(None, ge=1, description="Maximum number of students that can enroll.")
    current_enrollment: Optional[int] = Field(None, ge=0, description="Current number of enrolled students.")
    meeting_days: Optional[List[DayOfWeek]] = Field(None, description="Days of the week when the course meets.")
    start_time: Optional[time] = Field(None, description="Course start time.")
    end_time: Optional[time] = Field(None, description="Course end time.")
    location: Optional[str] = Field(None, description="Classroom or meeting location.")
    prerequisites: Optional[List[str]] = Field(None, description="List of prerequisite course codes.")
    active: Optional[bool] = Field(None, description="Whether the course is currently active/offered.")
