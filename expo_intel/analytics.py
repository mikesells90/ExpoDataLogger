import json

import pandas as pd
import plotly.express as px
import streamlit as st

from intelligence import CLAIM_DENSITY_MAP, SATURATION_MAP
from utils import from_json


def _safe_mode(series: pd.Series, default="N/A"):
    if series.empty:
        return default
    mode = series.mode()
    if mode.empty:
        return default
    return mode.iloc[0]


def _explode_json_list(df: pd.DataFrame, column: str) -> pd.Series:
    if df.empty or column not in df.columns:
        return pd.Series(dtype=object)
    exploded = df[column].apply(from_json).explode().dropna()
    return exploded.astype(str)


def generate_digest(df: pd.DataFrame) -> list[str]:
    if df.empty:
        return ["No entries yet. Capture a few booths to generate the daily digest."]

    claim = _safe_mode(df["primary_claim"].dropna(), "No dominant claim yet")
    flavor = _safe_mode(_explode_json_list(df, "flavor_mode"), "No flavor trend yet")
    first_q = _safe_mode(df["first_question"].dropna(), "No buyer question trend yet")

    sat_numeric = df["saturation_nearby"].map(SATURATION_MAP).fillna(3)
    high_sat_share = float((sat_numeric >= 5).mean()) if len(df) else 0
    white_space_share = float(((sat_numeric <= 2) & (df["differentiation"].fillna(0) >= 4)).mean())

    warnings = []
    warnings.append(f"Dominant claim theme: {claim}.")
    warnings.append(f"Emerging flavor bias: {flavor}.")
    warnings.append(f"Buyer priority shift signal: most frequent first question is '{first_q}'.")
    if high_sat_share >= 0.4:
        warnings.append("Saturation cluster warning: high-saturation entries exceed 40% of captures.")
    if white_space_share >= 0.2:
        warnings.append("Whitespace pocket detected: at least 20% of entries combine low saturation and high differentiation.")

    return warnings[:5]


def render_war_room(df: pd.DataFrame) -> None:
    st.subheader("War Room Dashboard")
    if df.empty:
        st.info("No entries yet. Add your first capture from the left panel.")
        return

    df = df.copy()
    df["claim_density_numeric"] = df["claim_density"].map(CLAIM_DENSITY_MAP).fillna(3)
    df["saturation_numeric"] = df["saturation_nearby"].map(SATURATION_MAP).fillna(3)

    total_entries = len(df)
    walk_pct = float((df["mode"] == "Walk").mean() * 100)
    booth_pct = float((df["mode"] == "Booth").mean() * 100)
    avg_diff = float(df["differentiation"].fillna(0).mean())
    avg_claim_density = float(df["claim_density_numeric"].mean())
    avg_complexity = float(df["production_complexity"].fillna(0).mean())
    flavor_mode = _safe_mode(_explode_json_list(df, "flavor_mode"))
    claim_mode = _safe_mode(df["primary_claim"].dropna())
    first_q_mode = _safe_mode(df["first_question"].dropna())
    objection_mode = _safe_mode(_explode_json_list(df, "objections"))
    blue_ocean_remaining = int(df["blue_ocean_tag"].fillna("").eq("").sum())

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Entries", total_entries)
    m2.metric("Walk %", f"{walk_pct:.0f}%")
    m3.metric("Booth %", f"{booth_pct:.0f}%")
    m4.metric("Avg Differentiation", f"{avg_diff:.2f}")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Avg Claim Density", f"{avg_claim_density:.2f}")
    m6.metric("Avg Production Complexity", f"{avg_complexity:.2f}")
    m7.metric("Most Frequent Flavor", flavor_mode)
    m8.metric("Most Frequent Claim", claim_mode)

    m9, m10, m11 = st.columns(3)
    m9.metric("Most Frequent First Question", first_q_mode)
    m10.metric("Top Objection", objection_mode)
    m11.metric("Blue Ocean Tags Remaining", blue_ocean_remaining)

    recent = df.sort_values("timestamp", ascending=False).head(5)
    stimulation = float((recent["premium_signal"].fillna(0) + recent["chaos_signal"].fillna(0)).mean())
    if stimulation > 7:
        st.warning("Stimulation Warning: average premium+chaos in last 5 entries is above 7.")

    st.markdown("### Daily Intelligence Digest")
    for insight in generate_digest(df):
        st.write(f"- {insight}")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        flavor_counts = _explode_json_list(df, "flavor_mode").value_counts().reset_index()
        flavor_counts.columns = ["flavor_mode", "count"]
        if not flavor_counts.empty:
            st.plotly_chart(px.bar(flavor_counts, x="flavor_mode", y="count", title="Flavor Mode Bar"), use_container_width=True)

        st.plotly_chart(
            px.scatter(
                df,
                x="premium_signal",
                y="chaos_signal",
                color="mode",
                hover_data=["brand_name", "archetype"],
                title="Premium vs Chaos Scatter",
            ),
            use_container_width=True,
        )

        if df["cluster_id"].notna().any():
            cluster_df = df[df["cluster_id"].notna()].copy()
            st.plotly_chart(
                px.scatter(
                    cluster_df,
                    x="differentiation",
                    y="claim_density_numeric",
                    color="cluster_label",
                    hover_data=["brand_name", "cluster_id"],
                    title="Cluster Scatter",
                ),
                use_container_width=True,
            )

    with chart_col2:
        claim_counts = df["primary_claim"].fillna("Unknown").value_counts().reset_index()
        claim_counts.columns = ["primary_claim", "count"]
        st.plotly_chart(px.bar(claim_counts, x="primary_claim", y="count", title="Claim Frequency Bar"), use_container_width=True)

        st.plotly_chart(
            px.scatter(
                df,
                x="differentiation",
                y="saturation_numeric",
                color="forecast",
                hover_data=["brand_name", "archetype"],
                title="Differentiation vs Saturation Scatter",
            ),
            use_container_width=True,
        )

        heatmap = df.groupby(["saturation_numeric", "differentiation"]).size().reset_index(name="count")
        st.plotly_chart(
            px.density_heatmap(
                heatmap,
                x="saturation_numeric",
                y="differentiation",
                z="count",
                title="Heatmap: Saturation vs Differentiation",
            ),
            use_container_width=True,
        )

    st.markdown("### Top Lists")
    t1, t2 = st.columns(2)
    with t1:
        st.write("Top 10 Blue Ocean Score")
        st.dataframe(df.sort_values("blue_ocean_score", ascending=False)[["brand_name", "blue_ocean_score", "archetype"]].head(10), hide_index=True)

        st.write("Top 10 Overclaimed")
        overclaimed = df.assign(overclaim_score=df["claim_density_numeric"] + df["chaos_signal"].fillna(0))
        st.dataframe(overclaimed.sort_values("overclaim_score", ascending=False)[["brand_name", "overclaim_score", "primary_claim"]].head(10), hide_index=True)

    with t2:
        st.write("Top 10 Threat Score")
        st.dataframe(df.sort_values("threat_score", ascending=False)[["brand_name", "threat_score", "archetype"]].head(10), hide_index=True)

        st.write("Top 10 Operational Mirage")
        mirage = df[
            (df["production_complexity"].fillna(0) >= 4)
            & (df["margin_smell_test"].fillna("").eq("Low"))
        ]
        st.dataframe(mirage[["brand_name", "production_complexity", "margin_smell_test"]].head(10), hide_index=True)

    st.markdown("### Export")
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", data=csv_data, file_name="expo_intel_entries.csv", mime="text/csv")
    st.download_button(
        "Download JSON",
        data=json.dumps(df.to_dict(orient="records"), ensure_ascii=True, indent=2),
        file_name="expo_intel_entries.json",
        mime="application/json",
    )

