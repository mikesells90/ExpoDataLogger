from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExpoDeepEval, ExpoWalkScan
from app.schemas import HeatMapRow, StrategicRankingRow
from app.services import follow_up_queue, hall_heat_map, strategic_ranking, to_csv_bytes

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/strategic-ranking", response_model=list[StrategicRankingRow])
def get_strategic_ranking(db: Session = Depends(get_db)):
    return strategic_ranking(db)


@router.get("/hall-heat-map", response_model=list[HeatMapRow])
def get_heat_map(db: Session = Depends(get_db)):
    return hall_heat_map(db)


@router.get("/follow-up-queue", response_model=list[dict])
def get_follow_up_queue(db: Session = Depends(get_db)):
    rows = follow_up_queue(db)
    return [
        {
            "eval_id": r.eval_id,
            "company_name": r.company_name,
            "booth_number": r.booth_number,
            "contact_name": r.contact_name,
            "contact_email": r.contact_email,
            "sps_score": r.sps_score,
            "tier": r.tier,
            "action_plan": r.action_plan,
        }
        for r in rows
    ]


@router.get("/export/walk.csv")
def export_walk_csv(db: Session = Depends(get_db)):
    rows = db.query(ExpoWalkScan).all()
    data = [
        {
            "scan_id": r.scan_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "company_name": r.company_name,
            "booth_number": r.booth_number,
            "hall": r.hall,
            "prs_score": r.prs_score,
            "cti_score": r.cti_score,
            "pos_score": r.pos_score,
            "sps_score": r.sps_score,
            "tier": r.tier,
        }
        for r in rows
    ]
    return Response(content=to_csv_bytes(data), media_type="text/csv")


@router.get("/export/deep.csv")
def export_deep_csv(db: Session = Depends(get_db)):
    rows = db.query(ExpoDeepEval).all()
    data = [
        {
            "eval_id": r.eval_id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else "",
            "company_name": r.company_name,
            "booth_number": r.booth_number,
            "contact_name": r.contact_name,
            "contact_email": r.contact_email,
            "sps_score": r.sps_score,
            "tier": r.tier,
        }
        for r in rows
    ]
    return Response(content=to_csv_bytes(data), media_type="text/csv")

