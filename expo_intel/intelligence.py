from utils import clamp

SATURATION_MAP = {"Low": 1, "Medium": 3, "High": 5}
CLAIM_DENSITY_MAP = {"1": 1, "2-3": 3, "4+": 5}
MARGIN_MAP = {"Low": 1, "Medium": 3, "High": 5}
CONFIDENCE_MAP = {"Low": 1, "Medium": 3, "High": 5}


def _as_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def compute_scores(payload: dict) -> dict:
    # These numeric transforms keep rule logic and ML features consistent.
    saturation_numeric = SATURATION_MAP.get(payload.get("saturation_nearby"), 3)
    claim_density_numeric = CLAIM_DENSITY_MAP.get(payload.get("claim_density"), 3)
    margin_numeric = MARGIN_MAP.get(payload.get("margin_smell_test"), 3)
    confidence_numeric = CONFIDENCE_MAP.get(payload.get("confidence"), 3)

    differentiation = _as_int(payload.get("differentiation"), 3)
    premium_signal = _as_int(payload.get("premium_signal"), 3)
    chaos_signal = _as_int(payload.get("chaos_signal"), 3)
    production_complexity = _as_int(payload.get("production_complexity"), 3)
    engagement_depth = _as_int(payload.get("engagement_depth"), 0)
    mode = payload.get("mode", "Walk")

    blue_ocean_bonus = 2 if payload.get("blue_ocean_tag") else 0
    threat_engagement_bonus = 2 if engagement_depth >= 4 else 0

    blue_ocean_score = (
        (6 - saturation_numeric)
        + differentiation
        + (premium_signal - chaos_signal)
        + (engagement_depth if mode == "Booth" else 0)
        + blue_ocean_bonus
    )
    threat_score = (
        differentiation
        + premium_signal
        + (6 - saturation_numeric)
        + (6 - production_complexity)
        + threat_engagement_bonus
    )

    return {
        "saturation_numeric": saturation_numeric,
        "claim_density_numeric": claim_density_numeric,
        "margin_numeric": margin_numeric,
        "confidence_numeric": confidence_numeric,
        "blue_ocean_score": float(clamp(blue_ocean_score, 0, 25)),
        "threat_score": float(clamp(threat_score, 0, 25)),
    }


def classify_archetype(payload: dict) -> str:
    # Deterministic archetype rules in priority order.
    influencer_visible = bool(payload.get("influencer_visible"))
    chaos_signal = _as_int(payload.get("chaos_signal"), 0)
    claim_density_numeric = CLAIM_DENSITY_MAP.get(payload.get("claim_density"), 3)
    premium_signal = _as_int(payload.get("premium_signal"), 0)
    production_complexity = _as_int(payload.get("production_complexity"), 0)
    margin_numeric = MARGIN_MAP.get(payload.get("margin_smell_test"), 3)
    saturation_numeric = SATURATION_MAP.get(payload.get("saturation_nearby"), 3)
    differentiation = _as_int(payload.get("differentiation"), 0)
    primary_claim = (payload.get("primary_claim") or "").lower()
    is_macro_heavy = any(token in primary_claim for token in ["protein", "macro", "functional", "keto", "fiber"])

    if influencer_visible and chaos_signal >= 4:
        return "Influencer Chaos Brand"
    if claim_density_numeric >= 5 and chaos_signal >= 4:
        return "Functional Hype Brand"
    if premium_signal >= 4 and chaos_signal <= 2:
        return "Premium Minimalist"
    if production_complexity >= 4 and margin_numeric <= 1:
        return "Operational Mirage"
    if saturation_numeric <= 1 and differentiation >= 4 and production_complexity <= 2:
        return "White Space Signal"
    if is_macro_heavy and differentiation <= 2:
        return "Commodity Macro Player"
    return "Unclassified"
