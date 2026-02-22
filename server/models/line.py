from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geometry, WKBElement
from pydantic import field_validator, model_validator
from shapely import wkb
from shapely.geometry import LineString
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .recording import RecordingSession


class LineStatus(str, Enum):
    """Status of a transit line."""
    PENDING = "pending"
    APPROVED = "approved"
    MERGED = "merged"


class LineBase(SQLModel):
    """Base model for Line with common fields."""
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None, max_length=1000)


class Line(LineBase, table=True):
    """
    A transit line (e.g., "Line 42", "Red Line").

    The path is stored as a PostGIS LINESTRING geometry in WGS84 (SRID 4326).
    """
    __tablename__ = "lines"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # PostGIS geometry column for the line path
    path: Any = Field(
        sa_column=Column(
            Geometry(geometry_type="LINESTRING", srid=4326),
            nullable=True
        )
    )

    # Approval workflow
    status: LineStatus = Field(default=LineStatus.PENDING)
    merged_into_id: Optional[int] = Field(default=None, foreign_key="lines.id")

    # Relationships
    recordings: list["RecordingSession"] = Relationship(back_populates="line")


def _validate_path(v: Optional[list[list[float]]]) -> Optional[list[list[float]]]:
    """Validate path as list of [lon, lat] with at least 2 points."""
    if v is None:
        return v
    if len(v) < 2:
        raise ValueError("Path must have at least 2 points")
    for point in v:
        if len(point) != 2:
            raise ValueError("Each point must be [longitude, latitude]")
        lon, lat = point
        if not (-180 <= lon <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    return v


def _path_to_linestring(path: Optional[list[list[float]]]) -> Optional[str]:
    """Convert path to WKT LINESTRING format."""
    if path is None or len(path) < 2:
        return None
    coords = ", ".join(f"{lon} {lat}" for lon, lat in path)
    return f"SRID=4326;LINESTRING({coords})"


class LineCreate(LineBase):
    """Schema for creating a new line."""
    path: Optional[list[list[float]]] = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[list[list[float]]]) -> Optional[list[list[float]]]:
        return _validate_path(v)


class LineRead(LineBase):
    """Schema for reading a line (API response)."""
    id: int
    status: LineStatus
    merged_into_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    path: Optional[list[list[float]]] = None

    @model_validator(mode="before")
    @classmethod
    def convert_geometry(cls, data: Any) -> Any:
        """Convert PostGIS geometry to coordinate list."""
        if isinstance(data, Line):
            result = {
                "id": data.id,
                "name": data.name,
                "description": data.description,
                "status": data.status,
                "merged_into_id": data.merged_into_id,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "path": None
            }
            if data.path is not None:
                if isinstance(data.path, WKBElement):
                    shape = wkb.loads(bytes(data.path.data))
                    result["path"] = list(shape.coords)
                elif isinstance(data.path, LineString):
                    result["path"] = list(data.path.coords)
            return result
        return data


class LineUpdate(SQLModel):
    """Schema for updating a line (all fields optional)."""
    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    status: Optional[LineStatus] = None
    path: Optional[list[list[float]]] = None

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[list[list[float]]]) -> Optional[list[list[float]]]:
        return _validate_path(v)
