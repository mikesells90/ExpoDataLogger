import pandas as pd
import plotly.express as px
import streamlit as st

from analytics_shared import as_list, ensure_scores, explode_list_column, safe_mode


def render_booth_war_room(booth_df: pd.DataFrame) -> None:
    st.subheader("Booth War Room")
    if booth_df.empty:
        st.info("No Booth entries yet.")
        return

    df = ensure_scores(booth_df)
    for col, default in [
        ("brand_name", "Unknown"),
        ("visitor_role", "Unknown"),
        ("first_question", "Unknown"),
        ("time_block", "Unknown"),
        ("positioning_angle", "Unknown"),
        ("response_strength", 0),
        ("follow_up", 0),
    ]:
        if col not in df.columns:
            df[col] = default

    df["response_strength"] = pd.to_numeric(df["response_strength"], errors="coerce").fillna(0)
    df["engagement_depth"] = pd.to_numeric(df["engagement_depth"], errors="coerce").fillna(0)
    df["follow_up_bool"] = df["follow_up"].fillna(0).astype(int) == 1
    df["objections_count"] = df.get("objections", pd.Series([[]] * len(df))).apply(lambda x: len(as_list(x)))

    total = len(df)
    avg_engagement = float(df["engagement_depth"].mean())
    followup_pct = float(df["follow_up_bool"].mean() * 100)
    top_role = safe_mode(df["visitor_role"].astype(str), "N/A")
    top_q = safe_mode(df["first_question"].astype(str), "N/A")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Booth Interactions", total)
    k2.metric("Avg Engagement Depth", f"{avg_engagement:.2f}")
    k3.metric("% Follow Up", f"{followup_pct:.0f}%")
    k4.metric("Top Visitor Role", top_role)
    k5.metric("Top First Question", top_q)

    c1, c2 = st.columns(2)
    with c1:
        first_q = df["first_question"].fillna("Unknown").value_counts().reset_index()
        first_q.columns = ["first_question", "count"]
        st.plotly_chart(px.bar(first_q, x="first_question", y="count", title="First Question Frequency"), use_container_width=True)

        st.plotly_chart(
            px.histogram(df, x="engagement_depth", nbins=5, title="Engagement Depth Distribution"),
            use_container_width=True,
        )

        objections = explode_list_column(df, "objections")
        objections = objections[~objections.str.lower().isin(["none", "na", "n/a", ""])]
        if not objections.empty:
            objection_counts = objections.value_counts().reset_index()
            objection_counts.columns = ["objection", "count"]
            st.plotly_chart(
                px.bar(objection_counts, x="objection", y="count", title="Objection Frequency"),
                use_container_width=True,
            )

    with c2:
        visitor = df["visitor_role"].fillna("Unknown").value_counts().reset_index()
        visitor.columns = ["visitor_role", "count"]
        st.plotly_chart(px.bar(visitor, x="visitor_role", y="count", title="Visitor Role Frequency"), use_container_width=True)

        pos = (
            df.groupby("positioning_angle", dropna=False)["response_strength"]
            .mean()
            .reset_index()
            .sort_values("response_strength", ascending=False)
        )
        pos["positioning_angle"] = pos["positioning_angle"].fillna("Unknown")
        st.plotly_chart(
            px.bar(
                pos,
                x="positioning_angle",
                y="response_strength",
                title="Positioning Angle vs Avg Response Strength",
            ),
            use_container_width=True,
        )

        by_time = (
            df.groupby("time_block", dropna=False)["engagement_depth"]
            .mean()
            .reset_index()
        )
        by_time["time_block"] = by_time["time_block"].fillna("Unknown")
        st.plotly_chart(
            px.bar(by_time, x="time_block", y="engagement_depth", title="Avg Engagement by Time Block"),
            use_container_width=True,
        )

    st.markdown("### Top Lists")
    t1, t2 = st.columns(2)
    with t1:
        highest_value = df.assign(value_score=df["engagement_depth"] + df["response_strength"] + (df["follow_up_bool"].astype(int) * 2))
        st.write("Top 10 Highest Value")
        st.dataframe(
            highest_value.sort_values("value_score", ascending=False)[
                ["brand_name", "value_score", "engagement_depth", "follow_up", "response_strength"]
            ].head(10),
            hide_index=True,
            use_container_width=True,
        )

        st.write("Top 10 Most Objection Heavy")
        st.dataframe(
            df.sort_values("objections_count", ascending=False)[
                ["brand_name", "objections_count", "first_question", "visitor_role"]
            ].head(10),
            hide_index=True,
            use_container_width=True,
        )

    with t2:
        st.write("Top 10 Best Positioning Outcomes")
        st.dataframe(
            df.sort_values(["response_strength", "engagement_depth"], ascending=False)[
                ["brand_name", "positioning_angle", "response_strength", "engagement_depth"]
            ].head(10),
            hide_index=True,
            use_container_width=True,
        )

