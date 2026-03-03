from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ExhibitorCursorIngest
from app.services import create_walk_scan

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/cursor")
def ingest_cursor(payload: ExhibitorCursorIngest, db: Session = Depends(get_db)):
    created = 0
    for exhibitor in payload.exhibitors:
        scan_payload = {
            "company_name": exhibitor.get("company_name") or exhibitor.get("name") or "Unknown",
            "booth_number": exhibitor.get("booth_number"),
            "hall": exhibitor.get("hall"),
            "category_tags": exhibitor.get("category_tags") or [],
            "protein_signal_score": exhibitor.get("protein_signal_score"),
            "competitive_threat_score": exhibitor.get("competitive_threat_score"),
            "quick_notes": exhibitor.get("description"),
            "follow_up_flag": exhibitor.get("follow_up_flag"),
            "organic_flag": exhibitor.get("organic_flag"),
            "usda_flag": exhibitor.get("usda_flag"),
            "sqf_flag": exhibitor.get("sqf_flag"),
            "regenerative_flag": exhibitor.get("regenerative_flag"),
            "emerging_brand_flag": exhibitor.get("emerging_brand_flag"),
        }
        create_walk_scan(db, scan_payload)
        created += 1

    next_cursor = f"cursor_{created}" if created else payload.cursor
    return {"created": created, "next_cursor": next_cursor}

