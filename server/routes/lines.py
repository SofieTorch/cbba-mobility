from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models.line import Line, LineCreate, LineRead, LineReadWithRoutes, LineUpdate

router = APIRouter(prefix="/lines", tags=["lines"])


@router.post("/", response_model=LineRead, status_code=201)
def create_line(line_data: LineCreate, db: Session = Depends(get_db)) -> LineRead:
    """Create a new transit line."""
    line = Line(
        name=line_data.name,
        description=line_data.description,
    )
    db.add(line)
    db.commit()
    db.refresh(line)
    return LineRead.model_validate(line)


@router.get("/", response_model=list[LineRead])
def list_lines(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> Sequence[LineRead]:
    """List all transit lines."""
    lines = db.execute(select(Line).offset(skip).limit(limit)).scalars().all()
    return [LineRead.model_validate(ln) for ln in lines]


@router.get("/{line_id}", response_model=LineReadWithRoutes)
def get_line(line_id: int, db: Session = Depends(get_db)) -> LineReadWithRoutes:
    """Get a specific line by ID with its routes."""
    line = db.execute(
        select(Line).where(Line.id == line_id).options(selectinload(Line.routes))
    ).scalar_one_or_none()
    
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    return LineReadWithRoutes.model_validate(line)


@router.patch("/{line_id}", response_model=LineRead)
def update_line(
    line_id: int,
    line_data: LineUpdate,
    db: Session = Depends(get_db)
) -> LineRead:
    """Update an existing line."""
    line = db.get(Line, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    
    update_data = line_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(line, key, value)
    
    db.add(line)
    db.commit()
    db.refresh(line)
    return LineRead.model_validate(line)


@router.delete("/{line_id}", status_code=204)
def delete_line(line_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a line and all its routes."""
    line = db.get(Line, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    db.delete(line)
    db.commit()
