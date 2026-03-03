import csv
import io
import time
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import ExpoDeepEval, ExpoExhibitorsRaw, ExpoWalkScan
from app.scoring import derive_scores

GRAPHQL_URL = "https://attend.expowest.com/api/graphql"
PERSISTED_HASH = "b3cb76208b6de3d96c5ba1a8f02e6be6135d5ff1db0a2eecd64b7d15e7e6b5e2"
VIEW_ID = "RXZlbnRWaWV3XzEyMjU1ODQ="
EVENT_ID = "RXZlbnRfMzAxMDc4Nw=="


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _to_dict_score(score_result):
    return {
        "prs_score": score_result.prs_score,
        "cti_score": score_result.cti_score,
        "pos_score": score_result.pos_score,
        "sps_score": score_result.sps_score,
        "score_confidence": score_result.score_confidence,
    }


def create_walk_scan(db: Session, payload: dict) -> ExpoWalkScan:
    score_result = derive_scores(payload)
    row = ExpoWalkScan(
        scan_id=payload.get("scan_id") or str(uuid4()),
        created_at=_now(),
        updated_at=_now(),
        event_slug=payload.get("event_slug") or "natural-products-expo-west-2026",
        company_name=payload["company_name"],
        booth_number=payload.get("booth_number"),
        hall=payload.get("hall"),
        category_tags=payload.get("category_tags", []),
        protein_signal_score=int(payload["protein_signal_score"]),
        competitive_threat_score=int(payload["competitive_threat_score"]),
        follow_up_flag=payload["follow_up_flag"],
        usda_flag=bool(payload.get("usda_flag", False)),
        organic_flag=bool(payload.get("organic_flag", False)),
        sqf_flag=bool(payload.get("sqf_flag", False)),
        regenerative_flag=bool(payload.get("regenerative_flag", False)),
        emerging_brand_flag=bool(payload.get("emerging_brand_flag", False)),
        quick_notes=payload.get("quick_notes"),
        tier=score_result.tier,
        **_to_dict_score(score_result),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def create_deep_eval(db: Session, payload: dict) -> ExpoDeepEval:
    score_result = derive_scores(payload)
    row = ExpoDeepEval(
        eval_id=payload.get("eval_id") or str(uuid4()),
        created_at=_now(),
        updated_at=_now(),
        event_slug=payload.get("event_slug") or "natural-products-expo-west-2026",
        company_name=payload["company_name"],
        booth_number=payload.get("booth_number"),
        hall=payload.get("hall"),
        contact_name=payload.get("contact_name"),
        contact_email=payload.get("contact_email"),
        contact_role=payload.get("contact_role"),
        website=payload.get("website"),
        core_skus=payload.get("core_skus"),
        format_type=payload.get("format_type"),
        pack_size=payload.get("pack_size"),
        price_per_unit=payload.get("price_per_unit"),
        claims_tags=payload.get("claims_tags", []),
        manufacturing_type=payload["manufacturing_type"],
        certifications=payload.get("certifications", []),
        estimated_scale=payload["estimated_scale"],
        kill_step_type=payload.get("kill_step_type"),
        channel_presence=payload.get("channel_presence", []),
        direct_competitor_flag=bool(payload.get("direct_competitor_flag", False)),
        closest_charcut_sku=payload.get("closest_charcut_sku"),
        differentiator_notes=payload.get("differentiator_notes"),
        weakness_notes=payload.get("weakness_notes"),
        what_they_do_better=payload.get("what_they_do_better"),
        what_we_do_better=payload.get("what_we_do_better"),
        strategic_fit_score=int(payload["strategic_fit_score"]),
        competitive_threat_score=int(payload["competitive_threat_score"]),
        partnership_potential_score=int(payload["partnership_potential_score"]),
        action_plan=payload.get("action_plan", []),
        post_show_priority=payload["post_show_priority"],
        full_notes=payload.get("full_notes"),
        tier_suggested=score_result.tier,
        **_to_dict_score(score_result),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def query_walk_scans(db: Session, meat_forward_only: bool = False, organic_only: bool = False, event_slug: str | None = None):
    stmt = select(ExpoWalkScan).order_by(desc(ExpoWalkScan.created_at))
    if event_slug:
        stmt = stmt.where(ExpoWalkScan.event_slug == event_slug)
    if meat_forward_only:
        stmt = stmt.where(ExpoWalkScan.protein_signal_score >= 4)
    if organic_only:
        stmt = stmt.where(ExpoWalkScan.organic_flag.is_(True))
    return db.execute(stmt).scalars().all()


def query_deep_evals(db: Session, direct_competitors_only: bool = False, high_partnership_only: bool = False, event_slug: str | None = None):
    stmt = select(ExpoDeepEval).order_by(desc(ExpoDeepEval.created_at))
    if event_slug:
        stmt = stmt.where(ExpoDeepEval.event_slug == event_slug)
    if direct_competitors_only:
        stmt = stmt.where(ExpoDeepEval.direct_competitor_flag.is_(True))
    if high_partnership_only:
        stmt = stmt.where(ExpoDeepEval.partnership_potential_score >= 4)
    return db.execute(stmt).scalars().all()


def strategic_ranking(db: Session, tier1_only: bool = False, hall: str | None = None, competitor_only: bool = False):
    walk = db.execute(select(ExpoWalkScan)).scalars().all()
    deep = db.execute(select(ExpoDeepEval)).scalars().all()
    bucket = {}

    def key_for(company_name: str, booth_number: str | None):
        return (company_name or "").strip().lower(), (booth_number or "").strip().lower()

    for w in walk:
        key = key_for(w.company_name, w.booth_number)
        current = bucket.get(key)
        candidate = {
            "source": "walk",
            "record_id": w.scan_id,
            "company_name": w.company_name,
            "booth_number": w.booth_number,
            "hall": w.hall,
            "sps_score": w.sps_score,
            "tier": w.tier,
            "score_confidence": w.score_confidence,
            "competitor_flag": False,
        }
        if current is None or (candidate["sps_score"] or 0) > (current["sps_score"] or 0):
            bucket[key] = candidate

    for d in deep:
        key = key_for(d.company_name, d.booth_number)
        current = bucket.get(key)
        candidate = {
            "source": "deep_eval",
            "record_id": d.eval_id,
            "company_name": d.company_name,
            "booth_number": d.booth_number,
            "hall": d.hall,
            "sps_score": d.sps_score,
            "tier": d.tier_suggested,
            "score_confidence": d.score_confidence,
            "competitor_flag": bool(d.direct_competitor_flag),
        }
        if current is None or (candidate["sps_score"] or 0) > (current["sps_score"] or 0):
            bucket[key] = candidate

    rows = list(bucket.values())
    if tier1_only:
        rows = [r for r in rows if r["tier"] == "tier1"]
    if hall:
        rows = [r for r in rows if (r.get("hall") or "").lower() == hall.lower()]
    if competitor_only:
        rows = [r for r in rows if r.get("competitor_flag")]

    return sorted(rows, key=lambda x: (x["sps_score"] or -1), reverse=True)


def _heat_color(avg_sps: float) -> str:
    if avg_sps >= 80:
        return "red"
    if avg_sps >= 60:
        return "orange"
    if avg_sps >= 40:
        return "yellow"
    if avg_sps >= 20:
        return "light_green"
    return "gray"


def hall_heat_map(db: Session, tier1_only: bool = False, meat_only: bool = False, organic_only: bool = False):
    walk_rows = db.execute(select(ExpoWalkScan)).scalars().all()
    if tier1_only:
        walk_rows = [r for r in walk_rows if r.tier == "tier1"]
    if meat_only:
        walk_rows = [r for r in walk_rows if any("meat/jerky/sausage" in str(t).lower() for t in (r.category_tags or []))]
    if organic_only:
        walk_rows = [r for r in walk_rows if r.organic_flag]

    buckets: dict[str, dict] = {}
    for row in walk_rows:
        hall = row.hall or "Unknown"
        if hall not in buckets:
            buckets[hall] = {"hall": hall, "booth_count": 0, "sps_sum": 0.0}
        buckets[hall]["booth_count"] += 1
        buckets[hall]["sps_sum"] += float(row.sps_score or 0)

    out = []
    for hall, data in buckets.items():
        avg_sps = round(data["sps_sum"] / max(data["booth_count"], 1), 2)
        density = round(avg_sps, 2)
        out.append(
            {
                "hall": hall,
                "booth_count": data["booth_count"],
                "total_sps": round(data["sps_sum"], 2),
                "avg_sps": avg_sps,
                "density_score": density,
                "heat_color": _heat_color(avg_sps),
            }
        )
    return sorted(out, key=lambda x: x["avg_sps"], reverse=True)


def exhibitors_for_hall(db: Session, hall: str):
    rows = db.execute(select(ExpoWalkScan).where(ExpoWalkScan.hall == hall).order_by(desc(ExpoWalkScan.sps_score))).scalars().all()
    return [
        {
            "scan_id": r.scan_id,
            "company_name": r.company_name,
            "booth_number": r.booth_number,
            "hall": r.hall,
            "sps_score": r.sps_score,
            "tier": r.tier,
            "follow_up_flag": r.follow_up_flag,
        }
        for r in rows
    ]


def follow_up_queue(db: Session):
    rows = db.execute(
        select(ExpoDeepEval).where(ExpoDeepEval.tier_suggested == "tier1").order_by(desc(ExpoDeepEval.sps_score))
    ).scalars().all()
    return rows


def ingest_graphql_exhibitors(db: Session, max_pages: int = 50, delay_seconds: float = 0.4):
    cursor = None
    total = 0
    pages = 0
    with httpx.Client(timeout=20.0) as client:
        while pages < max_pages:
            payload = {
                "operationName": "EventExhibitorListViewConnectionQuery",
                "variables": {
                    "withEvent": True,
                    "viewId": VIEW_ID,
                    "eventId": EVENT_ID,
                    "after": cursor,
                },
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": PERSISTED_HASH,
                    }
                },
            }
            response = client.post(GRAPHQL_URL, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Ingestion blocked: HTTP {response.status_code} :: {response.text[:800]}")
            body = response.json()
            if "errors" in body and body["errors"]:
                raise RuntimeError(f"Ingestion blocked: GraphQL errors :: {body['errors']}")

            data = (((body.get("data") or {}).get("event") or {}).get("exhibitors") or {})
            edges = data.get("edges") or []
            for edge in edges:
                node = edge.get("node") or {}
                row = ExpoExhibitorsRaw(
                    exhibitor_id=str(node.get("id") or ""),
                    name=node.get("name"),
                    exhibitor_type=node.get("type"),
                    booth=node.get("booth"),
                    description_html=node.get("descriptionHtml"),
                    logo_url=node.get("logoUrl"),
                    raw_json=node,
                )
                db.add(row)
                total += 1
            db.commit()

            page_info = data.get("pageInfo") or {}
            cursor = page_info.get("endCursor")
            pages += 1
            if not page_info.get("hasNextPage"):
                break
            time.sleep(max(delay_seconds, 0.4))

    return {"pages": pages, "records_saved": total, "end_cursor": cursor}


def to_csv_bytes(items: list[dict]) -> bytes:
    if not items:
        return b""
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(items[0].keys()))
    writer.writeheader()
    writer.writerows(items)
    return stream.getvalue().encode("utf-8")

