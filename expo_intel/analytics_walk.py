import pandas as pd
import plotly.express as px
import streamlit as st

from analytics_shared import ensure_scores, explode_list_column, safe_mode


def render_walk_war_room(walk_df: pd.DataFrame) -> None:
    st.subheader("Walk War Room")
    if walk_df.empty:
        st.info("No Walk entries yet.")
        return

    df = ensure_scores(walk_df)
    df["brand_name"] = df.get("brand_name", pd.Series(dtype=object)).fillna("Unknown")
    df["archetype"] = df.get("archetype", pd.Series(dtype=object)).fillna("Unclassified")
    df["claim_density"] = df.get("claim_density", pd.Series(dtype=object)).fillna("2-3")
    df["primary_claim"] = df.get("primary_claim", pd.Series(dtype=object)).fillna("Unknown")

    total_entries = len(df)
    avg_diff = float(df["differentiation"].mean())
    avg_claim_density = float(df["claim_density_numeric"].mean())
    avg_premium = float(df["premium_signal"].mean())
    avg_chaos = float(df["chaos_signal"].mean())
    blue_tag_count = int((df.get("blue_ocean_tag", "").fillna("").astype(str).str.strip() != "").sum())

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total Walk Entries", total_entries)
    k2.metric("Avg Differentiation", f"{avg_diff:.2f}")
    k3.metric("Avg Claim Density", f"{avg_claim_density:.2f}")
    k4.metric("Avg Premium", f"{avg_premium:.2f}")
    k5.metric("Avg Chaos", f"{avg_chaos:.2f}")
    k6.metric("Blue Ocean Tags", blue_tag_count)

    c1, c2 = st.columns(2)
    with c1:
        heat = df.groupby(["saturation_numeric", "differentiation"]).size().reset_index(name="count")
        st.plotly_chart(
            px.density_heatmap(
                heat,
                x="saturation_numeric",
                y="differentiation",
                z="count",
                title="Saturation vs Differentiation Heatmap",
            ),
            use_container_width=True,
        )

        flavor_counts = explode_list_column(df, "flavor_mode").value_counts().reset_index()
        flavor_counts.columns = ["flavor_mode", "count"]
        if not flavor_counts.empty:
            st.plotly_chart(
                px.bar(flavor_counts, x="flavor_mode", y="count", title="Flavor Mode Frequency"),
                use_container_width=True,
            )

        st.plotly_chart(
            px.histogram(
                df,
                x="claim_density",
                title="Claim Density Distribution",
                category_orders={"claim_density": ["1", "2-3", "4+"]},
            ),
            use_container_width=True,
        )

    with c2:
        color_col = "cluster_label" if ("cluster_label" in df.columns and df["cluster_label"].notna().any()) else "archetype"
        st.plotly_chart(
            px.scatter(
                df,
                x="premium_signal",
                y="chaos_signal",
                color=color_col,
                hover_data=["brand_name", "primary_claim"],
                title="Premium vs Chaos",
            ),
            use_container_width=True,
        )

        claim_counts = df["primary_claim"].fillna("Unknown").value_counts().reset_index()
        claim_counts.columns = ["primary_claim", "count"]
        st.plotly_chart(
            px.bar(claim_counts, x="primary_claim", y="count", title="Primary Claim Frequency"),
            use_container_width=True,
        )

    st.markdown("### Top Lists")
    t1, t2 = st.columns(2)
    with t1:
        st.write("Top 10 Blue Ocean Score")
        st.dataframe(
            df.sort_values("blue_ocean_score", ascending=False)[["brand_name", "blue_ocean_score", "archetype"]].head(10),
            hide_index=True,
            use_container_width=True,
        )

        st.write("Top 10 Overclaimed")
        overclaimed = df.assign(
            overclaimed_score=df["claim_density_numeric"] + df["claim_aggression"] + (6 - df["differentiation"])
        )
        st.dataframe(
            overclaimed.sort_values("overclaimed_score", ascending=False)[
                ["brand_name", "overclaimed_score", "claim_density", "claim_aggression", "differentiation"]
            ].head(10),
            hide_index=True,
            use_container_width=True,
        )

    with t2:
        st.write("Top 10 Threat Score")
        st.dataframe(
            df.sort_values("threat_score", ascending=False)[["brand_name", "threat_score", "archetype"]].head(10),
            hide_index=True,
            use_container_width=True,
        )

        st.write("Top 10 Operational Mirage")
        mirage = df[(df["production_complexity"] >= 4) & (df["margin_numeric"] <= 1)]
        st.dataframe(
            mirage.sort_values("production_complexity", ascending=False)[
                ["brand_name", "production_complexity", "margin_smell_test", "primary_claim"]
            ].head(10),
            hide_index=True,
            use_container_width=True,
        )

    top_tag = safe_mode(df.get("blue_ocean_tag", pd.Series(dtype=object)).astype(str).replace("", pd.NA).dropna(), "N/A")
    st.caption(f"Most frequent Blue Ocean tag: {top_tag}")

