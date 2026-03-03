from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import DeepEvalCreate, DeepEvalOut
from app.services import create_deep_eval, query_deep_evals

router = APIRouter(prefix="/deep-evals", tags=["deep"])


@router.post("", response_model=DeepEvalOut)
def create_deep(payload: DeepEvalCreate, db: Session = Depends(get_db)):
    row = create_deep_eval(db, payload.model_dump())
    return row


@router.get("", response_model=list[DeepEvalOut])
def list_deep(
    direct_competitors_only: bool = Query(False),
    high_partnership_only: bool = Query(False),
    event_slug: str | None = Query(None),
    db: Session = Depends(get_db),
):
    return query_deep_evals(
        db,
        direct_competitors_only=direct_competitors_only,
        high_partnership_only=high_partnership_only,
        event_slug=event_slug,
    )
