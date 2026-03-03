import pandas as pd
import streamlit as st

from analytics_shared import as_list, ensure_scores, explode_list_column, safe_mode


def _contains_any(text: str, tokens: list[str]) -> bool:
    t = (text or "").lower()
    return any(tok in t for tok in tokens)


def render_exec_summary(df_all: pd.DataFrame) -> None:
    st.subheader("Executive Summary: Noise vs Signal Delta")
    if df_all.empty:
        st.info("No data yet.")
        return

    base = ensure_scores(df_all)
    walk_df = base[base["mode"] == "Walk"].copy()
    booth_df = base[base["mode"] == "Booth"].copy()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Walk (Noise)")
        walk_claim = safe_mode(walk_df.get("primary_claim", pd.Series(dtype=object)).astype(str), "N/A")
        walk_flavor = safe_mode(explode_list_column(walk_df, "flavor_mode"), "N/A")
        walk_4p_share = float((walk_df["claim_density"] == "4+").mean() * 100) if "claim_density" in walk_df.columns and len(walk_df) else 0.0
        st.metric("Most Common Claim", walk_claim)
        st.metric("Most Common Flavor", walk_flavor)
        st.metric("Claim Density 4+ Share", f"{walk_4p_share:.0f}%")

    with c2:
        st.markdown("### Booth (Signal)")
        booth_q = safe_mode(booth_df.get("first_question", pd.Series(dtype=object)).astype(str), "N/A")
        booth_obj = safe_mode(explode_list_column(booth_df, "objections"), "N/A")
        avg_engagement = float(pd.to_numeric(booth_df.get("engagement_depth", 0), errors="coerce").fillna(0).mean()) if len(booth_df) else 0.0
        follow_up_pct = float((pd.to_numeric(booth_df.get("follow_up", 0), errors="coerce").fillna(0) == 1).mean() * 100) if len(booth_df) else 0.0
        st.metric("Most Common First Question", booth_q)
        st.metric("Most Common Objection", booth_obj)
        st.metric("Avg Engagement Depth", f"{avg_engagement:.2f}")
        st.metric("% Follow Up", f"{follow_up_pct:.0f}%")

    st.markdown("### Delta Callouts")
    callouts = []
    if _contains_any(walk_claim, ["functional", "macro", "protein", "gut", "health"]) and _contains_any(
        booth_q, ["margin", "velocity", "sell", "retail", "turn", "price"]
    ):
        callouts.append("Mismatch: floor noise != buyer signal. Walk claims skew functional, booth questions skew margin/velocity.")

    top_walk_flavor = walk_flavor
    if top_walk_flavor != "N/A":
        booth_flavors = explode_list_column(booth_df, "flavor_mode")
        booth_has_flavor = booth_flavors.str.lower().eq(top_walk_flavor.lower()).any() if not booth_flavors.empty else False
        if not booth_has_flavor and avg_engagement < 3.5:
            callouts.append(f"Flavor disconnect: '{top_walk_flavor}' is rising in Walk but not translating to strong booth engagement.")

    if not callouts:
        callouts.append("No major mismatch detected in current sample window.")

    for c in callouts:
        st.write(f"- {c}")

    st.markdown("### Top 5 Opportunity Candidates")
    if walk_df.empty or booth_df.empty:
        st.info("Need both Walk and Booth data to compute opportunity candidates.")
        return

    walk_candidates = walk_df[(walk_df["saturation_numeric"] <= 1) & (walk_df["differentiation"] >= 4)].copy()
    if walk_candidates.empty:
        st.info("No low-saturation + high-differentiation Walk candidates yet.")
        return

    booth_df = booth_df.copy()
    booth_df["engagement_depth"] = pd.to_numeric(booth_df.get("engagement_depth", 0), errors="coerce").fillna(0)
    booth_df["follow_up"] = pd.to_numeric(booth_df.get("follow_up", 0), errors="coerce").fillna(0)
    booth_df["primary_claim"] = booth_df.get("primary_claim", pd.Series(dtype=object)).fillna("").astype(str)
    walk_candidates["primary_claim"] = walk_candidates.get("primary_claim", pd.Series(dtype=object)).fillna("").astype(str)

    candidate_rows = []
    for _, w in walk_candidates.iterrows():
        w_flavors = set(as_list(w.get("flavor_mode")))
        matches = booth_df[booth_df["primary_claim"].str.lower() == str(w["primary_claim"]).lower()].copy()

        if "flavor_mode" in booth_df.columns and w_flavors:
            matches["flavor_overlap"] = matches["flavor_mode"].apply(lambda v: int(bool(w_flavors.intersection(set(as_list(v))))))
            matches = matches[(matches["flavor_overlap"] == 1) | (matches["engagement_depth"] >= 4)]
        else:
            matches = matches[matches["engagement_depth"] >= 4]

        if matches.empty:
            continue

        best = matches.sort_values(["engagement_depth", "follow_up"], ascending=False).iloc[0]
        candidate_rows.append(
            {
                "walk_brand": w.get("brand_name", "Unknown"),
                "claim_theme": w.get("primary_claim", "Unknown"),
                "walk_differentiation": w.get("differentiation", 0),
                "walk_saturation": w.get("saturation_nearby", "Unknown"),
                "booth_brand_match": best.get("brand_name", "Unknown"),
                "booth_engagement": float(best.get("engagement_depth", 0)),
                "booth_follow_up": int(best.get("follow_up", 0)),
            }
        )

    if not candidate_rows:
        st.info("No claim/flavor overlaps with strong booth engagement yet.")
        return

    out = pd.DataFrame(candidate_rows).sort_values(["booth_engagement", "booth_follow_up"], ascending=False).head(5)
    st.dataframe(out, hide_index=True, use_container_width=True)

