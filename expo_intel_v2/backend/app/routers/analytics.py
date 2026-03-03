from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ExpoDeepEval, ExpoWalkScan
from app.schemas import HeatMapRow, StrategicRankingRow
from app.services import (
    exhibitors_for_hall,
    follow_up_queue,
    hall_heat_map,
    strategic_ranking,
    to_csv_bytes,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/strategic-ranking", response_model=list[StrategicRankingRow])
def get_strategic_ranking(
    tier1_only: bool = Query(False),
    hall: str | None = Query(None),
    competitor_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    return strategic_ranking(db, tier1_only=tier1_only, hall=hall, competitor_only=competitor_only)


@router.get("/hall-heat-map", response_model=list[HeatMapRow])
def get_heat_map(
    tier1_only: bool = Query(False),
    meat_only: bool = Query(False),
    organic_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    return hall_heat_map(db, tier1_only=tier1_only, meat_only=meat_only, organic_only=organic_only)


@router.get("/hall/{hall}/exhibitors")
def get_hall_exhibitors(hall: str, db: Session = Depends(get_db)):
    return exhibitors_for_hall(db, hall)


@router.get("/follow-up-queue")
def get_follow_up_queue(db: Session = Depends(get_db)):
    rows = follow_up_queue(db)
    return [
        {
            "eval_id": r.eval_id,
            "company_name": r.company_name,
            "booth_number": r.booth_number,
            "contact_name": r.contact_name,
            "contact_email": r.contact_email,
            "contact_role": r.contact_role,
            "action_plan": r.action_plan,
            "post_show_priority": r.post_show_priority,
            "sps_score": r.sps_score,
            "tier_suggested": r.tier_suggested,
        }
        for r in rows
    ]


@router.get("/export/walk.csv")
def export_walk_csv(db: Session = Depends(get_db)):
    rows = db.query(ExpoWalkScan).all()
    data = [
        {
            "scan_id": r.scan_id,
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "event_slug": r.event_slug,
            "company_name": r.company_name,
            "booth_number": r.booth_number,
            "hall": r.hall,
            "follow_up_flag": r.follow_up_flag,
            "prs_score": r.prs_score,
            "cti_score": r.cti_score,
            "pos_score": r.pos_score,
            "sps_score": r.sps_score,
            "tier": r.tier,
            "score_confidence": r.score_confidence,
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
            "created_at": r.created_at.isoformat() if r.created_at else "",
            "event_slug": r.event_slug,
            "company_name": r.company_name,
            "booth_number": r.booth_number,
            "hall": r.hall,
            "contact_name": r.contact_name,
            "contact_email": r.contact_email,
            "sps_score": r.sps_score,
            "tier_suggested": r.tier_suggested,
            "score_confidence": r.score_confidence,
        }
        for r in rows
    ]
    return Response(content=to_csv_bytes(data), media_type="text/csv")


@router.get("/export/combined_rankings.csv")
def export_combined_csv(db: Session = Depends(get_db)):
    ranked = strategic_ranking(db)
    return Response(content=to_csv_bytes(ranked), media_type="text/csv")


@router.get("/export/all.json")
def export_all_json(db: Session = Depends(get_db)):
    walk = db.query(ExpoWalkScan).all()
    deep = db.query(ExpoDeepEval).all()
    payload = {
        "walk": [
            {
                "scan_id": r.scan_id,
                "company_name": r.company_name,
                "booth_number": r.booth_number,
                "hall": r.hall,
                "prs_score": r.prs_score,
                "cti_score": r.cti_score,
                "pos_score": r.pos_score,
                "sps_score": r.sps_score,
                "tier": r.tier,
            }
            for r in walk
        ],
        "deep": [
            {
                "eval_id": r.eval_id,
                "company_name": r.company_name,
                "booth_number": r.booth_number,
                "hall": r.hall,
                "contact_name": r.contact_name,
                "sps_score": r.sps_score,
                "tier_suggested": r.tier_suggested,
            }
            for r in deep
        ],
        "combined_rankings": strategic_ranking(db),
    }
    return JSONResponse(content=payload)

