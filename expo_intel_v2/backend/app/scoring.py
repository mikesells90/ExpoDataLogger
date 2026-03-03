from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CATEGORY_WEIGHTS = {
    "meat/jerky/sausage": 10,
    "protein snack": 7,
    "collagen/functional protein": 5,
    "plant protein": 3,
    "ingredient supplier": 4,
    "equipment/tech": 2,
}

FORMAT_WEIGHTS = {
    "stick": 5,
    "snack": 5,
    "sausage link": 5,
    "patty": 4,
    "chub": 4,
    "crumble": 3,
    "frozen entree": 2,
    "frozen entrée": 2,
}

CLAIMS_WEIGHTS = {
    "organic": 3,
    "roc": 5,
    "grass-fed": 4,
    "regenerative": 6,
    "nitrate-free": 2,
    "high protein": 3,
    "no sugar": 2,
}

SCALE_WEIGHTS = {"small": 5, "mid": 10, "national": 20, "unknown": 10}
CHANNEL_WEIGHTS = {
    "club": 15,
    "retail": 12,
    "distribution": 12,
    "amazon": 8,
    "dtc": 5,
    "foodservice": 6,
    "meal kit": 6,
}
CERTIFICATION_WEIGHTS = {"usda": 5, "organic": 5, "sqf": 5}


def _normalize_list(values: list[str] | None) -> list[str]:
    if not values:
        return []
    return [str(v).strip().lower() for v in values if str(v).strip()]


def _cap(value: int | float, lo: int = 0, hi: int = 100) -> int:
    return int(max(lo, min(hi, round(value))))


def _match_weight(raw_items: list[str], mapping: dict[str, int], cap: int | None = None) -> int:
    total = 0
    for item in raw_items:
        for key, weight in mapping.items():
            if key in item:
                total += weight
    if cap is not None:
        total = min(total, cap)
    return total


def compute_prs(payload: dict[str, Any]) -> int:
    protein_signal = payload.get("protein_signal_score")
    if protein_signal is None:
        fit = payload.get("strategic_fit_score")
        threat = payload.get("competitive_threat_score")
        if fit is not None and threat is not None:
            protein_signal = _cap((fit + threat) / 2, 1, 5)
        elif fit is not None:
            protein_signal = int(fit)
        else:
            protein_signal = 3

    categories = _normalize_list(payload.get("category_tags"))
    claims = _normalize_list(payload.get("claims_tags"))
    certifications = _normalize_list(payload.get("certifications"))
    combined_claims = claims + certifications
    format_type = str(payload.get("format_type") or "").lower()

    category_weight = _match_weight(categories, CATEGORY_WEIGHTS, cap=15)
    format_weight = _match_weight([format_type], FORMAT_WEIGHTS, cap=6)
    claims_weight = _match_weight(combined_claims, CLAIMS_WEIGHTS, cap=10)

    prs_raw = (int(protein_signal) * 3) + category_weight + format_weight + claims_weight
    return _cap(prs_raw * 4)


def compute_cti(payload: dict[str, Any]) -> int:
    threat_score = int(payload.get("competitive_threat_score") or 3)
    direct_competitor = bool(payload.get("direct_competitor_flag"))
    scale = str(payload.get("estimated_scale") or "unknown").lower()
    channels = _normalize_list(payload.get("channel_presence"))

    channel_weight = _match_weight(channels, CHANNEL_WEIGHTS, cap=25)
    scale_weight = SCALE_WEIGHTS.get(scale, 10)
    cti_raw = (threat_score * 5) + (20 if direct_competitor else 0) + scale_weight + channel_weight
    return _cap(cti_raw)


def compute_pos(payload: dict[str, Any]) -> int:
    partnership_score = payload.get("partnership_potential_score")
    if partnership_score is None:
        partnership_score = payload.get("follow_up_flag")
        if partnership_score == "deep_dive":
            partnership_score = 4
        elif partnership_score == "revisit":
            partnership_score = 3
        else:
            partnership_score = 2

    manufacturing_type = str(payload.get("manufacturing_type") or "unknown").lower()
    categories = _normalize_list(payload.get("category_tags"))
    certifications = _normalize_list(payload.get("certifications"))

    cert_weight = _match_weight(certifications, CERTIFICATION_WEIGHTS, cap=15)
    ingredient_supplier_flag = any("ingredient supplier" in c for c in categories)

    pos_raw = (
        (int(partnership_score) * 5)
        + (15 if manufacturing_type == "co_pack" else 0)
        + (20 if ingredient_supplier_flag else 0)
        + cert_weight
    )
    return _cap(pos_raw)


def compute_sps(prs: int, cti: int, pos: int) -> int:
    return _cap(round((prs * 0.40) + (cti * 0.35) + (pos * 0.25)))


def compute_tier(sps: int) -> str:
    if sps >= 75:
        return "tier1"
    if sps >= 50:
        return "tier2"
    return "tier3"


def compute_score_confidence(payload: dict[str, Any]) -> str:
    is_booth = payload.get("strategic_fit_score") is not None or payload.get("partnership_potential_score") is not None
    if is_booth:
        required = ["strategic_fit_score", "competitive_threat_score", "partnership_potential_score", "manufacturing_type", "estimated_scale"]
        return "high" if all(payload.get(k) is not None for k in required) else "medium"
    required_walk = ["protein_signal_score", "competitive_threat_score", "follow_up_flag"]
    if all(payload.get(k) is not None for k in required_walk):
        return "medium"
    return "low"


@dataclass
class ScoreResult:
    prs_score: int
    cti_score: int
    pos_score: int
    sps_score: int
    tier: str
    score_confidence: str


def derive_scores(payload: dict[str, Any]) -> ScoreResult:
    prs = compute_prs(payload)
    cti = compute_cti(payload)
    pos = compute_pos(payload)
    sps = compute_sps(prs, cti, pos)
    return ScoreResult(
        prs_score=prs,
        cti_score=cti,
        pos_score=pos,
        sps_score=sps,
        tier=compute_tier(sps),
        score_confidence=compute_score_confidence(payload),
    )

