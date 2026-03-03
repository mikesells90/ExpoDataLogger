from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import WalkScanCreate, WalkScanOut
from app.services import create_walk_scan, query_walk_scans

router = APIRouter(prefix="/walk-scans", tags=["walk"])


@router.post("", response_model=WalkScanOut)
def create_walk(payload: WalkScanCreate, db: Session = Depends(get_db)):
    row = create_walk_scan(db, payload.model_dump())
    return row


@router.get("", response_model=list[WalkScanOut])
def list_walk(
    meat_forward_only: bool = Query(False),
    organic_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    return query_walk_scans(db, meat_forward_only=meat_forward_only, organic_only=organic_only)

