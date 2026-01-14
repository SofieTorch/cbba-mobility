"""Add users and recording sessions tables

Revision ID: 002
Revises: 001
Create Date: 2026-01-14

"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    
    # Create recording_sessions table
    op.create_table(
        "recording_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("line_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=100), nullable=True),
        sa.Column("device_model", sa.String(length=100), nullable=True),
        sa.Column("os_version", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, default="in_progress"),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column(
            "computed_path",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry"
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["line_id"], ["lines.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recording_sessions_user_id"), "recording_sessions", ["user_id"], unique=False)
    op.create_index(op.f("ix_recording_sessions_line_id"), "recording_sessions", ["line_id"], unique=False)
    
    # Create location_points table
    op.create_table(
        "location_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("bearing", sa.Float(), nullable=True),
        sa.Column("horizontal_accuracy", sa.Float(), nullable=True),
        sa.Column("vertical_accuracy", sa.Float(), nullable=True),
        sa.Column(
            "point",
            geoalchemy2.types.Geometry(
                geometry_type="POINT",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry"
            ),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["session_id"], ["recording_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_location_points_session_id"), "location_points", ["session_id"], unique=False)
    op.create_index("ix_location_points_timestamp", "location_points", ["session_id", "timestamp"], unique=False)
    
    # Spatial index for location points
    op.execute("CREATE INDEX ix_location_points_point_gist ON location_points USING GIST (point)")
    
    # Create sensor_readings table
    op.create_table(
        "sensor_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("accel_x", sa.Float(), nullable=True),
        sa.Column("accel_y", sa.Float(), nullable=True),
        sa.Column("accel_z", sa.Float(), nullable=True),
        sa.Column("gyro_x", sa.Float(), nullable=True),
        sa.Column("gyro_y", sa.Float(), nullable=True),
        sa.Column("gyro_z", sa.Float(), nullable=True),
        sa.Column("pressure", sa.Float(), nullable=True),
        sa.Column("magnetic_heading", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["recording_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sensor_readings_session_id"), "sensor_readings", ["session_id"], unique=False)
    op.create_index("ix_sensor_readings_timestamp", "sensor_readings", ["session_id", "timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sensor_readings_timestamp", table_name="sensor_readings")
    op.drop_index(op.f("ix_sensor_readings_session_id"), table_name="sensor_readings")
    op.drop_table("sensor_readings")
    
    op.drop_index("ix_location_points_point_gist", table_name="location_points")
    op.drop_index("ix_location_points_timestamp", table_name="location_points")
    op.drop_index(op.f("ix_location_points_session_id"), table_name="location_points")
    op.drop_table("location_points")
    
    op.drop_index(op.f("ix_recording_sessions_line_id"), table_name="recording_sessions")
    op.drop_index(op.f("ix_recording_sessions_user_id"), table_name="recording_sessions")
    op.drop_table("recording_sessions")
    
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
