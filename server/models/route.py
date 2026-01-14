from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geometry, WKBElement
from pydantic import field_validator, model_validator
from shapely import wkb
from shapely.geometry import LineString
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .line import Line


class RouteBase(SQLModel):
    """Base model for Route with common fields."""
    direction: str = Field(max_length=100)  # e.g., "outbound", "inbound", "north", "clockwise"
    distinctive: Optional[str] = Field(default=None, max_length=255)  # e.g., "express", "via downtown"
    color: Optional[str] = Field(default=None, max_length=7)  # Hex color like #FF5733


class Route(RouteBase, table=True):
    """
    A transit route representing a specific path/direction within a line.
    
    The path is stored as a PostGIS LINESTRING geometry in WGS84 (SRID 4326).
    """
    __tablename__ = "routes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    line_id: int = Field(foreign_key="lines.id", index=True)
    
    # PostGIS geometry column for the route path
    # LINESTRING stores an ordered sequence of points (longitude, latitude)
    path: Any = Field(
        sa_column=Column(
            Geometry(geometry_type="LINESTRING", srid=4326),
            nullable=True
        )
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to line
    line: Optional["Line"] = Relationship(back_populates="routes")


class RouteCreate(RouteBase):
    """Schema for creating a new route."""
    line_id: int
    # Accept path as a list of [longitude, latitude] coordinate pairs
    path: Optional[list[list[float]]] = None
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[list[list[float]]]) -> Optional[list[list[float]]]:
        if v is None:
            return v
        if len(v) < 2:
            raise ValueError("Route path must have at least 2 points")
        for point in v:
            if len(point) != 2:
                raise ValueError("Each point must be [longitude, latitude]")
            lon, lat = point
            if not (-180 <= lon <= 180):
                raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        return v
    
    def to_linestring(self) -> Optional[str]:
        """Convert path to WKT LINESTRING format."""
        if self.path is None:
            return None
        coords = ", ".join(f"{lon} {lat}" for lon, lat in self.path)
        return f"SRID=4326;LINESTRING({coords})"


class RouteRead(RouteBase):
    """Schema for reading a route (API response)."""
    id: int
    line_id: int
    path: Optional[list[list[float]]] = None
    created_at: datetime
    updated_at: datetime
    
    @model_validator(mode="before")
    @classmethod
    def convert_geometry(cls, data: Any) -> Any:
        """Convert PostGIS geometry to coordinate list."""
        if isinstance(data, Route):
            result = {
                "id": data.id,
                "line_id": data.line_id,
                "direction": data.direction,
                "distinctive": data.distinctive,
                "color": data.color,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
                "path": None
            }
            if data.path is not None:
                if isinstance(data.path, WKBElement):
                    shape = wkb.loads(bytes(data.path.data))
                    result["path"] = list(shape.coords)
                elif isinstance(data.path, (LineString,)):
                    result["path"] = list(data.path.coords)
            return result
        return data


class RouteUpdate(SQLModel):
    """Schema for updating a route (all fields optional)."""
    direction: Optional[str] = Field(default=None, max_length=100)
    distinctive: Optional[str] = Field(default=None, max_length=255)
    color: Optional[str] = Field(default=None, max_length=7)
    path: Optional[list[list[float]]] = None
    
    @field_validator("path")
    @classmethod
    def validate_path(cls, v: Optional[list[list[float]]]) -> Optional[list[list[float]]]:
        if v is None:
            return v
        if len(v) < 2:
            raise ValueError("Route path must have at least 2 points")
        for point in v:
            if len(point) != 2:
                raise ValueError("Each point must be [longitude, latitude]")
            lon, lat = point
            if not (-180 <= lon <= 180):
                raise ValueError(f"Longitude must be between -180 and 180, got {lon}")
            if not (-90 <= lat <= 90):
                raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        return v
    
    def to_linestring(self) -> Optional[str]:
        """Convert path to WKT LINESTRING format if path is set."""
        if self.path is None:
            return None
        coords = ", ".join(f"{lon} {lat}" for lon, lat in self.path)
        return f"SRID=4326;LINESTRING({coords})"
