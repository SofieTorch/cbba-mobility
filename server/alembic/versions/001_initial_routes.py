"""Initial lines and routes tables with PostGIS

Revision ID: 001
Revises: 
Create Date: 2026-01-14

"""
from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    
    # Create lines table
    op.create_table(
        "lines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_lines_name"), "lines", ["name"], unique=False)
    
    # Create routes table
    op.create_table(
        "routes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("line_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=100), nullable=False),
        sa.Column("distinctive", sa.String(length=255), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column(
            "path",
            geoalchemy2.types.Geometry(
                geometry_type="LINESTRING",
                srid=4326,
                from_text="ST_GeomFromEWKT",
                name="geometry"
            ),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["line_id"], ["lines.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_routes_line_id"), "routes", ["line_id"], unique=False)
    
    # Create spatial index for efficient geo queries
    op.execute("CREATE INDEX ix_routes_path_gist ON routes USING GIST (path)")


def downgrade() -> None:
    op.drop_index("ix_routes_path_gist", table_name="routes")
    op.drop_index(op.f("ix_routes_line_id"), table_name="routes")
    op.drop_table("routes")
    op.drop_index(op.f("ix_lines_name"), table_name="lines")
    op.drop_table("lines")
