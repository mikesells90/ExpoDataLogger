import csv
import io
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ExpoDeepEval, ExpoWalkScan
from app.scoring import derive_scores


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_walk_scan(db: Session, payload: dict) -> ExpoWalkScan:
    scores = derive_scores(payload)
    row = ExpoWalkScan(
        scan_id=payload.get("scan_id") or str(uuid4()),
        timestamp=payload.get("timestamp") or _now(),
        company_name=payload["company_name"],
        booth_number=payload.get("booth_number"),
        hall=payload.get("hall"),
        category_tags=payload.get("category_tags", []),
        protein_signal_score=payload.get("protein_signal_score"),
        competitive_threat_score=payload.get("competitive_threat_score"),
        usda_flag=payload.get("usda_flag"),
        organic_flag=payload.get("organic_flag"),
        sqf_flag=payload.get("sqf_flag"),
        regenerative_flag=payload.get("regenerative_flag"),
        emerging_brand_flag=payload.get("emerging_brand_flag"),
        quick_notes=payload.get("quick_notes"),
        follow_up_flag=payload.get("follow_up_flag"),
        **scores,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_deep_eval(db: Session, payload: dict) -> ExpoDeepEval:
    scores = derive_scores(payload)
    tier = scores["tier"] or payload.get("post_show_priority")
    row = ExpoDeepEval(
        eval_id=payload.get("eval_id") or str(uuid4()),
        timestamp=payload.get("timestamp") or _now(),
        company_name=payload["company_name"],
        booth_number=payload.get("booth_number"),
        contact_name=payload.get("contact_name"),
        contact_email=payload.get("contact_email"),
        contact_role=payload.get("contact_role"),
        website=payload.get("website"),
        core_skus=payload.get("core_skus"),
        format_type=payload.get("format_type"),
        pack_size=payload.get("pack_size"),
        price_per_unit=payload.get("price_per_unit"),
        claims_tags=payload.get("claims_tags", []),
        manufacturing_type=payload.get("manufacturing_type"),
        certifications=payload.get("certifications", []),
        estimated_scale=payload.get("estimated_scale"),
        channel_presence=payload.get("channel_presence", []),
        direct_competitor_flag=payload.get("direct_competitor_flag"),
        closest_charcut_sku=payload.get("closest_charcut_sku"),
        strategic_fit_score=payload.get("strategic_fit_score"),
        competitive_threat_score=payload.get("competitive_threat_score"),
        partnership_potential_score=payload.get("partnership_potential_score"),
        strength_notes=payload.get("strength_notes"),
        weakness_notes=payload.get("weakness_notes"),
        action_plan=payload.get("action_plan", []),
        post_show_priority=tier,
        tier=tier,
        prs_score=scores["prs_score"],
        cti_score=scores["cti_score"],
        pos_score=scores["pos_score"],
        sps_score=scores["sps_score"],
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def query_walk_scans(
    db: Session,
    meat_forward_only: bool = False,
    organic_only: bool = False,
):
    stmt = select(ExpoWalkScan).order_by(desc(ExpoWalkScan.timestamp))
    if meat_forward_only:
        stmt = stmt.where(ExpoWalkScan.protein_signal_score >= 4)
    if organic_only:
        stmt = stmt.where(ExpoWalkScan.organic_flag.is_(True))
    return db.execute(stmt).scalars().all()


def query_deep_evals(
    db: Session,
    direct_competitors_only: bool = False,
    high_partnership_only: bool = False,
):
    stmt = select(ExpoDeepEval).order_by(desc(ExpoDeepEval.timestamp))
    if direct_competitors_only:
        stmt = stmt.where(ExpoDeepEval.direct_competitor_flag.is_(True))
    if high_partnership_only:
        stmt = stmt.where(ExpoDeepEval.partnership_potential_score >= 4)
    return db.execute(stmt).scalars().all()


def strategic_ranking(db: Session):
    walk = db.execute(select(ExpoWalkScan)).scalars().all()
    deep = db.execute(select(ExpoDeepEval)).scalars().all()
    rows = []
    for w in walk:
        rows.append(
            {
                "source": "walk",
                "record_id": w.scan_id,
                "company_name": w.company_name,
                "booth_number": w.booth_number,
                "sps_score": w.sps_score,
                "tier": w.tier,
            }
        )
    for d in deep:
        rows.append(
            {
                "source": "deep_eval",
                "record_id": d.eval_id,
                "company_name": d.company_name,
                "booth_number": d.booth_number,
                "sps_score": d.sps_score,
                "tier": d.tier,
            }
        )
    return sorted(rows, key=lambda x: (x["sps_score"] or -1), reverse=True)


def hall_heat_map(db: Session):
    walk = db.execute(select(ExpoWalkScan)).scalars().all()
    buckets = {}
    for row in walk:
        hall = row.hall or "Unknown"
        if hall not in buckets:
            buckets[hall] = {"hall": hall, "booth_count": 0, "sps_sum": 0.0}
        buckets[hall]["booth_count"] += 1
        buckets[hall]["sps_sum"] += float(row.sps_score or 0)

    out = []
    for hall, v in buckets.items():
        avg_sps = round(v["sps_sum"] / max(v["booth_count"], 1), 2)
        if avg_sps >= 80:
            color = "Red"
        elif avg_sps >= 60:
            color = "Orange"
        elif avg_sps >= 40:
            color = "Yellow"
        elif avg_sps >= 20:
            color = "Light Green"
        else:
            color = "Gray"
        out.append(
            {
                "hall": hall,
                "booth_count": v["booth_count"],
                "avg_sps": avg_sps,
                "heat_color": color,
            }
        )
    return sorted(out, key=lambda x: x["avg_sps"], reverse=True)


def follow_up_queue(db: Session):
    rows = db.execute(
        select(ExpoDeepEval).where(ExpoDeepEval.tier == "tier1").order_by(desc(ExpoDeepEval.sps_score))
    ).scalars().all()
    return rows


def to_csv_bytes(items: list[dict]) -> bytes:
    if not items:
        return b""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(items[0].keys()))
    writer.writeheader()
    writer.writerows(items)
    return stream.getvalue().encode("utf-8")

