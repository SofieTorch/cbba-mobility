import json
from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.functions import ST_AsGeoJSON
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models.line import Line
from models.route import Route, RouteCreate, RouteRead, RouteUpdate

router = APIRouter(prefix="/routes", tags=["routes"])


@router.post("/", response_model=RouteRead, status_code=201)
def create_route(route_data: RouteCreate, db: Session = Depends(get_db)) -> RouteRead:
    """Create a new route for a line."""
    # Verify line exists
    line = db.get(Line, route_data.line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    
    route = Route(
        line_id=route_data.line_id,
        direction=route_data.direction,
        distinctive=route_data.distinctive,
        color=route_data.color,
        path=route_data.to_linestring()
    )
    db.add(route)
    db.commit()
    db.refresh(route)
    return RouteRead.model_validate(route)


@router.get("/", response_model=list[RouteRead])
def list_routes(
    line_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Sequence[RouteRead]:
    """List all routes, optionally filtered by line."""
    query = select(Route)
    if line_id is not None:
        query = query.where(Route.line_id == line_id)
    routes = db.execute(query.offset(skip).limit(limit)).scalars().all()
    return [RouteRead.model_validate(r) for r in routes]


@router.get("/{route_id}", response_model=RouteRead)
def get_route(route_id: int, db: Session = Depends(get_db)) -> RouteRead:
    """Get a specific route by ID."""
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return RouteRead.model_validate(route)


@router.patch("/{route_id}", response_model=RouteRead)
def update_route(
    route_id: int,
    route_data: RouteUpdate,
    db: Session = Depends(get_db)
) -> RouteRead:
    """Update an existing route."""
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    update_data = route_data.model_dump(exclude_unset=True)
    
    # Handle path separately as it needs conversion
    if "path" in update_data and update_data["path"] is not None:
        route.path = route_data.to_linestring()
        del update_data["path"]
    
    for key, value in update_data.items():
        setattr(route, key, value)
    
    db.add(route)
    db.commit()
    db.refresh(route)
    return RouteRead.model_validate(route)


@router.delete("/{route_id}", status_code=204)
def delete_route(route_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a route."""
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    db.delete(route)
    db.commit()


@router.get("/{route_id}/geojson")
def get_route_geojson(route_id: int, db: Session = Depends(get_db)) -> dict:
    """Get route path as GeoJSON Feature."""
    route = db.get(Route, route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    
    if route.path is None:
        raise HTTPException(status_code=404, detail="Route has no path defined")
    
    # Use PostGIS to convert to GeoJSON
    result = db.execute(
        select(ST_AsGeoJSON(Route.path)).where(Route.id == route_id)
    ).scalar()
    
    return {
        "type": "Feature",
        "properties": {
            "id": route.id,
            "line_id": route.line_id,
            "direction": route.direction,
            "distinctive": route.distinctive
        },
        "geometry": json.loads(result)
    }


@router.get("/nearby/", response_model=list[RouteRead])
def find_routes_nearby(
    longitude: float,
    latitude: float,
    radius_meters: float = 1000,
    db: Session = Depends(get_db)
) -> Sequence[RouteRead]:
    """Find routes within a given radius of a point."""
    # Create a point from the coordinates and find routes within radius
    point = f"SRID=4326;POINT({longitude} {latitude})"
    
    query = select(Route).where(
        func.ST_DWithin(
            func.ST_Transform(Route.path, 3857),  # Transform to meters
            func.ST_Transform(func.ST_GeomFromEWKT(point), 3857),
            radius_meters
        )
    )
    
    routes = db.execute(query).scalars().all()
    return [RouteRead.model_validate(r) for r in routes]
