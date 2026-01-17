from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .line import Line
    from .recording import RecordingSession


class UserBase(SQLModel):
    """Base model for User."""
    username: str = Field(max_length=100, unique=True, index=True)
    email: Optional[str] = Field(default=None, max_length=255, unique=True)


class User(UserBase, table=True):
    """A user who records transit routes."""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    # In production, store hashed password, not plain text
    password_hash: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    recordings: list["RecordingSession"] = Relationship(back_populates="user")
    submitted_lines: list["Line"] = Relationship(back_populates="submitted_by")


class UserCreate(SQLModel):
    """Schema for creating a user."""
    username: str = Field(max_length=100)
    email: Optional[str] = Field(default=None, max_length=255)
    password: str = Field(min_length=8)


class UserRead(UserBase):
    """Schema for reading a user (API response)."""
    id: int
    is_active: bool
    created_at: datetime
