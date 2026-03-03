from typing import Any


CATEGORY_WEIGHTS = {
    "meat": 10,
    "sausage": 10,
    "jerky": 10,
    "protein snack": 7,
    "collagen": 5,
    "functional": 5,
    "plant protein": 3,
    "ingredient supplier": 4,
    "equipment": 2,
}

FORMAT_WEIGHTS = {
    "stick": 5,
    "snack": 5,
    "sausage link": 5,
    "patty": 4,
    "chub": 4,
    "frozen entree": 2,
}

CLAIMS_WEIGHTS = {
    "organic": 3,
    "roc": 5,
    "grass-fed": 4,
    "regenerative": 6,
    "nitrate-free": 2,
    "high protein": 3,
}

SCALE_WEIGHTS = {"small": 5, "mid": 10, "national": 20}

CHANNEL_WEIGHTS = {
    "club": 15,
    "costco": 15,
    "whole foods": 10,
    "national retail": 12,
    "dtc": 5,
}

CERTIFICATION_WEIGHTS = {"usda": 5, "organic": 5, "sqf 9": 5, "sqf": 5}


def _as_lower_list(items: list[str] | None) -> list[str]:
    if not items:
        return []
    return [str(x).strip().lower() for x in items if str(x).strip()]


def keyword_scan(*texts: str | None) -> dict[str, list[str]]:
    combined = " ".join([t or "" for t in texts]).lower()
    detected_claims = [k for k in CLAIMS_WEIGHTS.keys() if k in combined]
    detected_categories = [k for k in CATEGORY_WEIGHTS.keys() if k in combined]
    return {"claims": detected_claims, "categories": detected_categories}


def _category_weight(category_tags: list[str]) -> int:
    tags = _as_lower_list(category_tags)
    return max([CATEGORY_WEIGHTS.get(tag, 0) for tag in tags] + [0])


def _format_weight(format_type: str | None) -> int:
    if not format_type:
        return 0
    fmt = format_type.strip().lower()
    for key, weight in FORMAT_WEIGHTS.items():
        if key in fmt:
            return weight
    return 0


def _claims_weight(claims_tags: list[str]) -> int:
    tags = _as_lower_list(claims_tags)
    return sum(CLAIMS_WEIGHTS.get(tag, 0) for tag in tags)


def compute_prs(
    protein_signal_score: int | None,
    category_tags: list[str] | None,
    claims_tags: list[str] | None,
    format_type: str | None,
) -> float | None:
    if protein_signal_score is None or not category_tags:
        return None
    raw = (protein_signal_score * 3) + _category_weight(category_tags) + _format_weight(format_type) + _claims_weight(claims_tags or [])
    return float(min(100, raw))


def _channel_weight(channels: list[str]) -> int:
    total = 0
    for c in _as_lower_list(channels):
        if c in CHANNEL_WEIGHTS:
            total += CHANNEL_WEIGHTS[c]
        if "whole foods" in c:
            total += CHANNEL_WEIGHTS["whole foods"]
        if "national retail" in c:
            total += CHANNEL_WEIGHTS["national retail"]
    return total


def compute_cti(
    competitive_threat_score: int | None,
    direct_competitor_flag: bool | None,
    estimated_scale: str | None,
    channel_presence: list[str] | None,
) -> float | None:
    if competitive_threat_score is None or not estimated_scale:
        return None
    scale_weight = SCALE_WEIGHTS.get(estimated_scale.strip().lower(), 0)
    raw = (competitive_threat_score * 5) + (20 if direct_competitor_flag else 0) + scale_weight + _channel_weight(channel_presence or [])
    return float(min(100, raw))


def compute_pos(
    partnership_potential_score: int | None,
    manufacturing_type: str | None,
    certifications: list[str] | None,
    ingredient_supplier_flag: bool | None,
) -> float | None:
    if partnership_potential_score is None or not manufacturing_type:
        return None
    cert_weight = sum(CERTIFICATION_WEIGHTS.get(c, 0) for c in _as_lower_list(certifications or []))
    is_co_pack = manufacturing_type.strip().lower() == "co_pack"
    raw = (partnership_potential_score * 5) + (15 if is_co_pack else 0) + (20 if ingredient_supplier_flag else 0) + cert_weight
    return float(min(100, raw))


def compute_sps(prs: float | None, cti: float | None, pos: float | None) -> float | None:
    if prs is None or cti is None or pos is None:
        return None
    return float((prs * 0.4) + (cti * 0.35) + (pos * 0.25))


def tier_from_sps(sps: float | None) -> str | None:
    if sps is None:
        return None
    if sps >= 75:
        return "tier1"
    if sps >= 50:
        return "tier2"
    return "tier3"


def derive_scores(payload: dict[str, Any]) -> dict[str, float | str | None]:
    category_tags = payload.get("category_tags") or []
    claims_tags = payload.get("claims_tags") or []
    text_scan = keyword_scan(payload.get("quick_notes"), payload.get("core_skus"), payload.get("strength_notes"), payload.get("weakness_notes"))
    merged_claims = list({*map(str.lower, claims_tags), *text_scan["claims"]})
    merged_categories = list({*map(str.lower, category_tags), *text_scan["categories"]})

    prs = compute_prs(
        protein_signal_score=payload.get("protein_signal_score") or payload.get("strategic_fit_score"),
        category_tags=merged_categories,
        claims_tags=merged_claims,
        format_type=payload.get("format_type"),
    )
    cti = compute_cti(
        competitive_threat_score=payload.get("competitive_threat_score"),
        direct_competitor_flag=payload.get("direct_competitor_flag"),
        estimated_scale=payload.get("estimated_scale"),
        channel_presence=payload.get("channel_presence") or [],
    )
    pos = compute_pos(
        partnership_potential_score=payload.get("partnership_potential_score"),
        manufacturing_type=payload.get("manufacturing_type"),
        certifications=payload.get("certifications") or [],
        ingredient_supplier_flag="ingredient supplier" in merged_categories,
    )
    sps = compute_sps(prs, cti, pos)
    return {
        "prs_score": prs,
        "cti_score": cti,
        "pos_score": pos,
        "sps_score": sps,
        "tier": tier_from_sps(sps),
    }

