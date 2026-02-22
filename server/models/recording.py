from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

from geoalchemy2 import Geometry, WKBElement
from pydantic import model_validator
from shapely import wkb
from shapely.geometry import LineString
from sqlalchemy import Column, Text
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .line import Line


class RecordingStatus(str, Enum):
    """Status of a recording session."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ABANDONED = "abandoned"  # No activity for too long, auto-closed
    DISCARDED = "discarded"  # Ended without selecting a line


class RecordingSessionBase(SQLModel):
    """Base model for RecordingSession."""
    line_id: Optional[int] = Field(default=None, foreign_key="lines.id", index=True)
    direction: Optional[str] = Field(default=None, max_length=100)
    device_model: Optional[str] = Field(default=None, max_length=100)
    os_version: Optional[str] = Field(default=None, max_length=50)
    notes: Optional[str] = Field(default=None, sa_column=Column(Text))


class RecordingSession(RecordingSessionBase, table=True):
    """
    A recording session capturing a single trip on a transit line.
    """
    __tablename__ = "recording_sessions"

    id: Optional[int] = Field(default=None, primary_key=True)

    status: RecordingStatus = Field(default=RecordingStatus.IN_PROGRESS)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = Field(default=None)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)  # Updated on each batch upload
    
    # Computed path from all location points (updated when session ends)
    computed_path: Any = Field(
        default=None,
        sa_column=Column(
            Geometry(geometry_type="LINESTRING", srid=4326),
            nullable=True
        )
    )
    
    # Relationships
    line: Optional["Line"] = Relationship(back_populates="recordings")
    location_points: list["LocationPoint"] = Relationship(back_populates="session")
    sensor_readings: list["SensorReading"] = Relationship(back_populates="session")


class RecordingSessionCreate(SQLModel):
    """Schema for starting a new recording session (line is assigned later)."""
    direction: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    notes: Optional[str] = None


class EndRecordingRequest(SQLModel):
    """Schema for ending a recording session with an optional line assignment."""
    line_id: Optional[int] = None
    line_name: Optional[str] = None  # Create a new line with this name when line_id is null


class RecordingSessionRead(RecordingSessionBase):
    """Schema for reading a recording session."""
    id: int
    status: RecordingStatus
    started_at: datetime
    ended_at: Optional[datetime]
    last_activity_at: datetime
    computed_path: Optional[list[list[float]]] = None
    
    @model_validator(mode="before")
    @classmethod
    def convert_geometry(cls, data: Any) -> Any:
        """Convert PostGIS geometry to coordinate list."""
        if isinstance(data, RecordingSession):
            result = {
                "id": data.id,
                "line_id": data.line_id,
                "direction": data.direction,
                "device_model": data.device_model,
                "os_version": data.os_version,
                "notes": data.notes,
                "status": data.status,
                "started_at": data.started_at,
                "ended_at": data.ended_at,
                "last_activity_at": data.last_activity_at,
                "computed_path": None
            }
            if data.computed_path is not None:
                if isinstance(data.computed_path, WKBElement):
                    shape = wkb.loads(bytes(data.computed_path.data))
                    result["computed_path"] = list(shape.coords)
                elif isinstance(data.computed_path, LineString):
                    result["computed_path"] = list(data.computed_path.coords)
            return result
        return data


# ============================================================
# Location Points - GPS data
# ============================================================

class LocationPointBase(SQLModel):
    """Base model for a GPS location point."""
    timestamp: datetime  # When this reading was taken
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    altitude: Optional[float] = None  # Meters above sea level
    speed: Optional[float] = None  # Meters per second (from GPS)
    bearing: Optional[float] = Field(default=None, ge=0, lt=360)  # Degrees from north
    horizontal_accuracy: Optional[float] = None  # Meters
    vertical_accuracy: Optional[float] = None  # Meters


class LocationPoint(LocationPointBase, table=True):
    """A single GPS location point in a recording session."""
    __tablename__ = "location_points"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="recording_sessions.id", index=True)
    
    # PostGIS point for spatial queries
    point: Any = Field(
        sa_column=Column(
            Geometry(geometry_type="POINT", srid=4326),
            nullable=True
        )
    )
    
    session: Optional["RecordingSession"] = Relationship(back_populates="location_points")


class LocationPointCreate(LocationPointBase):
    """Schema for creating a location point."""
    pass


class LocationPointRead(LocationPointBase):
    """Schema for reading a location point."""
    id: int
    session_id: int


# ============================================================
# Sensor Readings - Accelerometer, Gyroscope, Barometer
# ============================================================

class SensorReadingBase(SQLModel):
    """Base model for sensor readings."""
    timestamp: datetime  # When this reading was taken
    
    # Accelerometer (m/s²)
    accel_x: Optional[float] = None
    accel_y: Optional[float] = None
    accel_z: Optional[float] = None
    
    # Gyroscope (rad/s)
    gyro_x: Optional[float] = None
    gyro_y: Optional[float] = None
    gyro_z: Optional[float] = None
    
    # Barometer
    pressure: Optional[float] = None  # hPa (hectopascals)
    
    # Magnetometer / Compass
    magnetic_heading: Optional[float] = Field(default=None, ge=0, lt=360)  # Degrees


class SensorReading(SensorReadingBase, table=True):
    """Sensor readings (accelerometer, gyroscope, etc.) from a recording session."""
    __tablename__ = "sensor_readings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="recording_sessions.id", index=True)
    
    session: Optional["RecordingSession"] = Relationship(back_populates="sensor_readings")


class SensorReadingCreate(SensorReadingBase):
    """Schema for creating a sensor reading."""
    pass


class SensorReadingRead(SensorReadingBase):
    """Schema for reading a sensor reading."""
    id: int
    session_id: int


# ============================================================
# Batch upload schemas (for efficiency)
# ============================================================

class LocationPointBatch(SQLModel):
    """Schema for uploading multiple location points at once."""
    points: list[LocationPointCreate]


class SensorReadingBatch(SQLModel):
    """Schema for uploading multiple sensor readings at once."""
    readings: list[SensorReadingCreate]
