from typing import Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from database import get_db
from models.line import Line, LineCreate, LineRead, LineReadWithRoutes, LineStatus, LineUpdate
from models.recording import RecordingSession

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
    status: Optional[LineStatus] = Query(
        default=LineStatus.APPROVED,
        description="Filter by status. Use 'pending' to see lines awaiting approval."
    ),
    include_all: bool = Query(
        default=False,
        description="If true, return all lines regardless of status (admin use)."
    ),
    db: Session = Depends(get_db)
) -> Sequence[LineRead]:
    """List transit lines. By default, only returns approved lines."""
    query = select(Line)
    
    if not include_all:
        query = query.where(Line.status == status)
    
    lines = db.execute(query.offset(skip).limit(limit)).scalars().all()
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


@router.post("/{line_id}/merge/{target_line_id}", response_model=LineRead)
def merge_line(
    line_id: int,
    target_line_id: int,
    db: Session = Depends(get_db)
) -> LineRead:
    """
    Merge a line into another line (admin operation).
    
    All recordings from line_id will be moved to target_line_id.
    The source line will be marked as MERGED with a reference to the target.
    """
    if line_id == target_line_id:
        raise HTTPException(status_code=400, detail="Cannot merge a line into itself")
    
    source = db.get(Line, line_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source line {line_id} not found")
    
    target = db.get(Line, target_line_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Target line {target_line_id} not found")
    
    if source.status == LineStatus.MERGED:
        raise HTTPException(
            status_code=400,
            detail=f"Source line {line_id} is already merged into line {source.merged_into_id}"
        )
    
    if target.status == LineStatus.MERGED:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot merge into line {target_line_id} as it is already merged into another line"
        )
    
    # Move all recordings from source to target
    db.execute(
        update(RecordingSession)
        .where(RecordingSession.line_id == line_id)
        .values(line_id=target_line_id)
    )
    
    # Mark source as merged
    source.status = LineStatus.MERGED
    source.merged_into_id = target_line_id
    
    db.commit()
    db.refresh(target)
    
    return LineRead.model_validate(target)


@router.post("/{line_id}/approve", response_model=LineRead)
def approve_line(line_id: int, db: Session = Depends(get_db)) -> LineRead:
    """Approve a pending line (admin operation)."""
    line = db.get(Line, line_id)
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    
    if line.status != LineStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Line is not pending (current status: {line.status})"
        )
    
    line.status = LineStatus.APPROVED
    db.commit()
    db.refresh(line)
    
    return LineRead.model_validate(line)
