from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GraphQLIngestRequest
from app.services import ingest_graphql_exhibitors

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/graphql")
def ingest_graphql(payload: GraphQLIngestRequest, db: Session = Depends(get_db)):
    try:
        return ingest_graphql_exhibitors(
            db,
            max_pages=payload.max_pages,
            delay_seconds=payload.delay_seconds,
        )
    except Exception as exc:  # Fail loudly by design.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

