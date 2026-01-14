from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .recording import RecordingSession
    from .route import Route


class LineBase(SQLModel):
    """Base model for Line with common fields."""
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)


class Line(LineBase, table=True):
    """
    A transit line (e.g., "Line 42", "Red Line").
    
    A line can have multiple routes (e.g., outbound/inbound directions).
    """
    __tablename__ = "lines"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    routes: list["Route"] = Relationship(back_populates="line")
    recordings: list["RecordingSession"] = Relationship(back_populates="line")


class LineCreate(LineBase):
    """Schema for creating a new line."""
    pass


class LineRead(LineBase):
    """Schema for reading a line (API response)."""
    id: int
    created_at: datetime
    updated_at: datetime


class LineReadWithRoutes(LineRead):
    """Schema for reading a line with its routes."""
    routes: list["RouteRead"] = []


class LineUpdate(SQLModel):
    """Schema for updating a line (all fields optional)."""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)


# Import here to avoid circular imports
from .route import RouteRead  # noqa: E402
LineReadWithRoutes.model_rebuild()
