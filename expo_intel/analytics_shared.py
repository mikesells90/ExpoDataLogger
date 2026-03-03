import json
from typing import Any

import pandas as pd

SATURATION_MAP = {"Low": 1, "Medium": 3, "High": 5}
CLAIM_DENSITY_MAP = {"1": 1, "2-3": 3, "4+": 5}
MARGIN_MAP = {"Low": 1, "Medium": 3, "High": 5}


def ensure_column(df: pd.DataFrame, col: str, default: Any) -> pd.DataFrame:
    if col not in df.columns:
        df[col] = default
    return df


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return []
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return [str(v) for v in parsed if str(v).strip()]
        except json.JSONDecodeError:
            pass
        return [value]
    return []


def explode_list_column(df: pd.DataFrame, col: str) -> pd.Series:
    if df.empty or col not in df.columns:
        return pd.Series(dtype=object)
    return df[col].apply(as_list).explode().dropna().astype(str)


def safe_mode(series: pd.Series, default: str = "N/A") -> str:
    s = series.dropna()
    if s.empty:
        return default
    m = s.mode()
    if m.empty:
        return default
    return str(m.iloc[0])


def add_common_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = ensure_column(out, "saturation_nearby", "Medium")
    out = ensure_column(out, "claim_density", "2-3")
    out = ensure_column(out, "margin_smell_test", "Medium")
    out = ensure_column(out, "differentiation", 3)
    out = ensure_column(out, "premium_signal", 3)
    out = ensure_column(out, "chaos_signal", 3)
    out = ensure_column(out, "production_complexity", 3)
    out = ensure_column(out, "engagement_depth", 0)
    out = ensure_column(out, "mode", "Walk")
    out = ensure_column(out, "blue_ocean_tag", "")
    out = ensure_column(out, "claim_aggression", 3)

    out["saturation_numeric"] = out["saturation_nearby"].map(SATURATION_MAP).fillna(3).astype(float)
    out["claim_density_numeric"] = out["claim_density"].map(CLAIM_DENSITY_MAP).fillna(3).astype(float)
    out["margin_numeric"] = out["margin_smell_test"].map(MARGIN_MAP).fillna(3).astype(float)

    for c, d in [
        ("differentiation", 3),
        ("premium_signal", 3),
        ("chaos_signal", 3),
        ("production_complexity", 3),
        ("engagement_depth", 0),
        ("claim_aggression", 3),
    ]:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(d)

    return out


def _clamp_series(series: pd.Series, lo: float, hi: float) -> pd.Series:
    return series.clip(lower=lo, upper=hi)


def compute_blue_ocean_score(df: pd.DataFrame) -> pd.Series:
    base = add_common_numeric_columns(df)
    blue_ocean_bonus = (base["blue_ocean_tag"].fillna("").astype(str).str.strip() != "").astype(int) * 2
    engagement_bonus = base["engagement_depth"].where(base["mode"] == "Booth", 0)
    score = (
        (6 - base["saturation_numeric"])
        + base["differentiation"]
        + (base["premium_signal"] - base["chaos_signal"])
        + engagement_bonus
        + blue_ocean_bonus
    )
    return _clamp_series(score, 0, 25).astype(float)


def compute_threat_score(df: pd.DataFrame) -> pd.Series:
    base = add_common_numeric_columns(df)
    engagement_bonus = (base["engagement_depth"] >= 4).astype(int) * 2
    score = (
        base["differentiation"]
        + base["premium_signal"]
        + (6 - base["saturation_numeric"])
        + (6 - base["production_complexity"])
        + engagement_bonus
    )
    return _clamp_series(score, 0, 25).astype(float)


def ensure_scores(df: pd.DataFrame) -> pd.DataFrame:
    out = add_common_numeric_columns(df)
    if "blue_ocean_score" not in out.columns:
        out["blue_ocean_score"] = compute_blue_ocean_score(out)
    else:
        out["blue_ocean_score"] = pd.to_numeric(out["blue_ocean_score"], errors="coerce")
        mask = out["blue_ocean_score"].isna()
        if mask.any():
            out.loc[mask, "blue_ocean_score"] = compute_blue_ocean_score(out.loc[mask])
    if "threat_score" not in out.columns:
        out["threat_score"] = compute_threat_score(out)
    else:
        out["threat_score"] = pd.to_numeric(out["threat_score"], errors="coerce")
        mask = out["threat_score"].isna()
        if mask.any():
            out.loc[mask, "threat_score"] = compute_threat_score(out.loc[mask])
    return out

