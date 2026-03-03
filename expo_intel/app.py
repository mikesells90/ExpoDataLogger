import json

import pandas as pd
import streamlit as st

from analytics_booth import render_booth_war_room
from analytics_walk import render_walk_war_room
from database import SessionLocal, init_db
from executive import render_exec_summary
from intelligence import classify_archetype, compute_scores
from ml import update_clusters
from models import BoothEntry
from utils import make_uuid, now_iso, to_json

st.set_page_config(page_title="Expo Intel Radar", page_icon="🎯", layout="wide")
init_db()


def get_entries_df(session) -> pd.DataFrame:
    rows = session.query(BoothEntry).order_by(BoothEntry.timestamp.desc()).all()
    records = []
    for r in rows:
        records.append(
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "mode": r.mode,
                "time_block": r.time_block,
                "brand_name": r.brand_name,
                "category": r.category,
                "format": r.format,
                "channel_target": r.channel_target,
                "flavor_mode": r.flavor_mode,
                "heat_index": r.heat_index,
                "sugar_signal": r.sugar_signal,
                "ingredient_signals": r.ingredient_signals,
                "primary_claim": r.primary_claim,
                "claim_density": r.claim_density,
                "claim_aggression": r.claim_aggression,
                "premium_signal": r.premium_signal,
                "chaos_signal": r.chaos_signal,
                "sampling_heavy": r.sampling_heavy,
                "influencer_visible": r.influencer_visible,
                "production_complexity": r.production_complexity,
                "co_pack_friendly": r.co_pack_friendly,
                "sku_spread": r.sku_spread,
                "margin_smell_test": r.margin_smell_test,
                "would_fund": r.would_fund,
                "saturation_nearby": r.saturation_nearby,
                "differentiation": r.differentiation,
                "forecast": r.forecast,
                "confidence": r.confidence,
                "blue_ocean_tag": r.blue_ocean_tag,
                "threat_flag": r.threat_flag,
                "traffic_behavior": r.traffic_behavior,
                "visitor_role": r.visitor_role,
                "first_question": r.first_question,
                "engagement_depth": r.engagement_depth,
                "follow_up": r.follow_up,
                "objections": r.objections,
                "positioning_angle": r.positioning_angle,
                "response_strength": r.response_strength,
                "forced_insight": r.forced_insight,
                "blue_ocean_score": r.blue_ocean_score,
                "threat_score": r.threat_score,
                "archetype": r.archetype,
                "cluster_id": r.cluster_id,
                "cluster_label": r.cluster_label,
            }
        )
    return pd.DataFrame(records)


@st.cache_data(show_spinner=False, ttl=10)
def load_all_entries() -> pd.DataFrame:
    session = SessionLocal()
    try:
        return get_entries_df(session)
    finally:
        session.close()


def get_default(key: str, fallback):
    if st.session_state.get("repeat_last_settings", False):
        return st.session_state.get(f"saved_{key}", fallback)
    return fallback


def save_setting(key: str, value):
    st.session_state[f"saved_{key}"] = value


def render_export_controls(df_all: pd.DataFrame, df_view: pd.DataFrame, key_prefix: str) -> None:
    st.markdown("### Export")
    all_csv = df_all.to_csv(index=False).encode("utf-8")
    view_csv = df_view.to_csv(index=False).encode("utf-8")
    all_json = json.dumps(df_all.to_dict(orient="records"), ensure_ascii=True, indent=2)
    view_json = json.dumps(df_view.to_dict(orient="records"), ensure_ascii=True, indent=2)

    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "Download All CSV",
            data=all_csv,
            file_name="expo_intel_all.csv",
            mime="text/csv",
            key=f"{key_prefix}_all_csv",
            use_container_width=True,
        )
        st.download_button(
            "Download Current View CSV",
            data=view_csv,
            file_name=f"expo_intel_{key_prefix}.csv",
            mime="text/csv",
            key=f"{key_prefix}_view_csv",
            use_container_width=True,
        )
    with e2:
        st.download_button(
            "Download All JSON",
            data=all_json,
            file_name="expo_intel_all.json",
            mime="application/json",
            key=f"{key_prefix}_all_json",
            use_container_width=True,
        )
        st.download_button(
            "Download Current View JSON",
            data=view_json,
            file_name=f"expo_intel_{key_prefix}.json",
            mime="application/json",
            key=f"{key_prefix}_view_json",
            use_container_width=True,
        )


def render_capture_view() -> bool:
    st.subheader("Capture")
    submitted = False
    quick_blue = False
    quick_danger = False
    form_data = {}

    top1, top2, top3, top4, top5 = st.columns([1.4, 1.2, 1.1, 1.4, 1.5])
    with top1:
        mode = st.radio("Mode", ["Walk", "Booth"], horizontal=True, key="mode")
    with top2:
        time_block = st.radio("Time Block", ["AM", "Midday", "PM"], horizontal=True, key="time_block")
    with top3:
        st.toggle("Executive Mode", key="executive_mode")
    with top4:
        st.toggle("Repeat Last Settings", key="repeat_last_settings")
    with top5:
        st.toggle("Quick Add Mode", key="quick_add_mode")

    with st.form("capture_form", clear_on_submit=False):
        brand_name = st.text_input("Brand Name *", value="", placeholder="Type brand and submit fast")
        quick_add_mode = st.session_state.get("quick_add_mode", False)

        if quick_add_mode:
            st.caption("Quick Add is on: only brand, mode, and time block are required.")
            submitted = st.form_submit_button("Save Quick Entry", use_container_width=True, type="primary")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                category = st.selectbox(
                    "Category",
                    ["Energy", "Hydration", "Protein", "Functional", "Snack", "Other"],
                    index=["Energy", "Hydration", "Protein", "Functional", "Snack", "Other"].index(get_default("category", "Functional")),
                )
                format_type = st.selectbox(
                    "Format",
                    ["Can", "Bottle", "Powder", "Shot", "Bar", "Other"],
                    index=["Can", "Bottle", "Powder", "Shot", "Bar", "Other"].index(get_default("format_type", "Can")),
                )
                channel_target = st.selectbox(
                    "Channel Target",
                    ["Mass", "Specialty", "Gym", "DTC", "Foodservice"],
                    index=["Mass", "Specialty", "Gym", "DTC", "Foodservice"].index(get_default("channel_target", "Mass")),
                )
                flavor_mode = st.multiselect(
                    "Flavor Mode (max 2)",
                    ["Fruity", "Citrus", "Creamy", "Dessert", "Savory", "Botanical", "Classic"],
                    default=get_default("flavor_mode", []),
                )
                heat_index = st.slider("Heat Index", 0, 3, int(get_default("heat_index", 1)))
                sugar_signal = st.selectbox(
                    "Sugar Signal",
                    ["Low", "Medium", "High", "Unknown"],
                    index=["Low", "Medium", "High", "Unknown"].index(get_default("sugar_signal", "Unknown")),
                )
                ingredient_signals = st.multiselect(
                    "Ingredient Signals",
                    ["Adaptogens", "Nootropics", "Electrolytes", "Collagen", "Creatine", "Vitamins", "Caffeine"],
                    default=get_default("ingredient_signals", []),
                )

            with c2:
                primary_claim = st.selectbox(
                    "Primary Claim Type",
                    ["Energy", "Recovery", "Hydration", "Focus", "Macro/Protein", "Gut Health", "Mood", "Other"],
                    index=["Energy", "Recovery", "Hydration", "Focus", "Macro/Protein", "Gut Health", "Mood", "Other"].index(get_default("primary_claim", "Energy")),
                )
                claim_density = st.selectbox(
                    "Claim Density",
                    ["1", "2-3", "4+"],
                    index=["1", "2-3", "4+"].index(get_default("claim_density", "2-3")),
                )
                claim_aggression = st.slider("Claim Aggression", 1, 5, int(get_default("claim_aggression", 3)))
                premium_signal = st.slider("Premium Signal", 1, 5, int(get_default("premium_signal", 3)))
                chaos_signal = st.slider("Chaos Signal", 1, 5, int(get_default("chaos_signal", 3)))
                sampling_heavy = st.checkbox("Sampling Heavy", value=bool(get_default("sampling_heavy", False)))
                influencer_visible = st.checkbox("Influencer Visible", value=bool(get_default("influencer_visible", False)))
                production_complexity = st.slider("Production Complexity", 1, 5, int(get_default("production_complexity", 3)))
                co_pack_friendly = st.selectbox(
                    "Co-Pack Friendly",
                    ["Yes", "No", "Maybe"],
                    index=["Yes", "No", "Maybe"].index(get_default("co_pack_friendly", "Maybe")),
                )
                sku_spread = st.selectbox(
                    "SKU Spread",
                    ["1-3", "4-8", "9+"],
                    index=["1-3", "4-8", "9+"].index(get_default("sku_spread", "4-8")),
                )
                margin_smell_test = st.selectbox(
                    "Margin Smell Test",
                    ["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(get_default("margin_smell_test", "Medium")),
                )
                would_fund = st.selectbox(
                    "Would I Fund This",
                    ["Yes", "No", "With Changes"],
                    index=["Yes", "No", "With Changes"].index(get_default("would_fund", "With Changes")),
                )

            with c3:
                saturation_nearby = st.selectbox(
                    "Saturation Nearby",
                    ["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(get_default("saturation_nearby", "Medium")),
                )
                differentiation = st.slider("Differentiation", 1, 5, int(get_default("differentiation", 3)))
                forecast = st.selectbox(
                    "Forecast",
                    ["Fail", "Survive", "Scale", "Acquire"],
                    index=["Fail", "Survive", "Scale", "Acquire"].index(get_default("forecast", "Survive")),
                )
                confidence = st.selectbox(
                    "Confidence",
                    ["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(get_default("confidence", "Medium")),
                )
                forced_insight = st.text_input(
                    "Forced Insight",
                    value=get_default("forced_insight", ""),
                    max_chars=120,
                    placeholder="Max 120 chars",
                )

                if mode == "Walk":
                    blue_ocean_tag = st.text_input("Blue Ocean Tag", value=get_default("blue_ocean_tag", ""))
                    threat_flag = st.checkbox("Threat Flag", value=bool(get_default("threat_flag", False)))
                    traffic_behavior = st.multiselect(
                        "Traffic Behavior",
                        ["Dense", "Fast Pass", "Sticky", "Line Forming", "Photo Heavy", "Sampling Queue"],
                        default=get_default("traffic_behavior", []),
                    )
                    b1, b2 = st.columns(2)
                    quick_blue = b1.form_submit_button("Quick Blue Hint", use_container_width=True)
                    quick_danger = b2.form_submit_button("Quick Dangerous Early", use_container_width=True)
                else:
                    blue_ocean_tag = None
                    threat_flag = False
                    traffic_behavior = []
                    visitor_role = st.selectbox(
                        "Visitor Role",
                        ["Buyer", "Founder", "Operator", "Investor", "Other"],
                        index=["Buyer", "Founder", "Operator", "Investor", "Other"].index(get_default("visitor_role", "Buyer")),
                    )
                    first_question = st.text_input("First Question Asked", value=get_default("first_question", ""))
                    engagement_depth = st.slider("Engagement Depth", 1, 5, int(get_default("engagement_depth", 3)))
                    follow_up = st.checkbox("Follow Up", value=bool(get_default("follow_up", False)))
                    objections = st.multiselect(
                        "Objections",
                        ["Price", "Taste", "Shelf Life", "Velocity", "Complex Ops", "No Clear Need"],
                        default=get_default("objections", []),
                    )
                    positioning_angle = st.text_input("Positioning Angle Used", value=get_default("positioning_angle", ""))
                    response_strength = st.slider("Response Strength", 1, 5, int(get_default("response_strength", 3)))

            submitted = st.form_submit_button("Submit Intel", use_container_width=True, type="primary")
            form_data = {
                "category": category,
                "format": format_type,
                "channel_target": channel_target,
                "flavor_mode": flavor_mode,
                "heat_index": heat_index,
                "sugar_signal": sugar_signal,
                "ingredient_signals": ingredient_signals,
                "primary_claim": primary_claim,
                "claim_density": claim_density,
                "claim_aggression": claim_aggression,
                "premium_signal": premium_signal,
                "chaos_signal": chaos_signal,
                "sampling_heavy": sampling_heavy,
                "influencer_visible": influencer_visible,
                "production_complexity": production_complexity,
                "co_pack_friendly": co_pack_friendly,
                "sku_spread": sku_spread,
                "margin_smell_test": margin_smell_test,
                "would_fund": would_fund,
                "saturation_nearby": saturation_nearby,
                "differentiation": differentiation,
                "forecast": forecast,
                "confidence": confidence,
                "forced_insight": forced_insight,
                "blue_ocean_tag": blue_ocean_tag,
                "threat_flag": threat_flag,
                "traffic_behavior": traffic_behavior,
                "visitor_role": visitor_role if mode == "Booth" else None,
                "first_question": first_question if mode == "Booth" else None,
                "engagement_depth": engagement_depth if mode == "Booth" else None,
                "follow_up": follow_up if mode == "Booth" else False,
                "objections": objections if mode == "Booth" else [],
                "positioning_angle": positioning_angle if mode == "Booth" else None,
                "response_strength": response_strength if mode == "Booth" else None,
            }

    if not submitted:
        if quick_blue or quick_danger:
            submitted = True
    if not submitted:
        return False

    if not brand_name.strip():
        st.error("Brand name is required.")
        return False

    if not st.session_state.get("quick_add_mode", False) and len(form_data.get("flavor_mode", [])) > 2:
        st.error("Flavor Mode allows up to 2 selections.")
        return False

    payload = {
        "id": make_uuid(),
        "timestamp": now_iso(),
        "mode": mode,
        "time_block": time_block,
        "brand_name": brand_name.strip(),
    }
    if not st.session_state.get("quick_add_mode", False):
        payload.update(form_data)

    if quick_blue:
        payload["blue_ocean_tag"] = payload.get("blue_ocean_tag") or "Quick Blue Hint"
    if quick_danger:
        payload["threat_flag"] = True
        payload["blue_ocean_tag"] = payload.get("blue_ocean_tag") or "Quick Dangerous Early"

    derived = compute_scores(payload)
    archetype = classify_archetype(payload)

    session = SessionLocal()
    try:
        entry = BoothEntry(
            id=payload["id"],
            timestamp=payload["timestamp"],
            mode=payload["mode"],
            time_block=payload["time_block"],
            brand_name=payload["brand_name"],
            category=payload.get("category"),
            format=payload.get("format"),
            channel_target=payload.get("channel_target"),
            flavor_mode=to_json(payload.get("flavor_mode")),
            heat_index=payload.get("heat_index"),
            sugar_signal=payload.get("sugar_signal"),
            ingredient_signals=to_json(payload.get("ingredient_signals")),
            primary_claim=payload.get("primary_claim"),
            claim_density=payload.get("claim_density"),
            claim_aggression=payload.get("claim_aggression"),
            premium_signal=payload.get("premium_signal"),
            chaos_signal=payload.get("chaos_signal"),
            sampling_heavy=int(bool(payload.get("sampling_heavy"))) if payload.get("sampling_heavy") is not None else None,
            influencer_visible=int(bool(payload.get("influencer_visible"))) if payload.get("influencer_visible") is not None else None,
            production_complexity=payload.get("production_complexity"),
            co_pack_friendly=payload.get("co_pack_friendly"),
            sku_spread=payload.get("sku_spread"),
            margin_smell_test=payload.get("margin_smell_test"),
            would_fund=payload.get("would_fund"),
            saturation_nearby=payload.get("saturation_nearby"),
            differentiation=payload.get("differentiation"),
            forecast=payload.get("forecast"),
            confidence=payload.get("confidence"),
            blue_ocean_tag=payload.get("blue_ocean_tag"),
            threat_flag=int(bool(payload.get("threat_flag"))) if payload.get("threat_flag") is not None else None,
            traffic_behavior=to_json(payload.get("traffic_behavior")),
            visitor_role=payload.get("visitor_role"),
            first_question=payload.get("first_question"),
            engagement_depth=payload.get("engagement_depth"),
            follow_up=int(bool(payload.get("follow_up"))) if payload.get("follow_up") is not None else None,
            objections=to_json(payload.get("objections")),
            positioning_angle=payload.get("positioning_angle"),
            response_strength=payload.get("response_strength"),
            forced_insight=payload.get("forced_insight"),
            blue_ocean_score=derived["blue_ocean_score"],
            threat_score=derived["threat_score"],
            archetype=archetype,
            cluster_id=None,
            cluster_label=None,
        )
        session.add(entry)
        session.commit()

        update_clusters(session)
        saved = session.query(BoothEntry).filter(BoothEntry.id == entry.id).first()
    finally:
        session.close()

    st.success("Intel captured.")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Archetype", saved.archetype or "Unclassified")
    s2.metric("Blue Ocean Score", f"{saved.blue_ocean_score:.1f}")
    s3.metric("Threat Score", f"{saved.threat_score:.1f}")
    s4.metric("Cluster Label", saved.cluster_label or "Pending")
    if saved.would_fund == "Yes":
        st.info("Would You Build This? If yes, define the first distribution wedge now.")

    if st.session_state.get("repeat_last_settings", False) and not st.session_state.get("quick_add_mode", False):
        for key, value in form_data.items():
            save_setting(key, value)
    else:
        keys_to_clear = [k for k in st.session_state.keys() if k.startswith("saved_")]
        for key in keys_to_clear:
            st.session_state.pop(key, None)

    st.cache_data.clear()
    return True


st.markdown(
    """
    <style>
    .main .block-container {padding-top: 1rem; padding-bottom: 1rem;}
    div[data-testid="stMetricValue"] {font-size: 1.2rem;}
    .stButton button {height: 2.7rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Expo Intel Radar")
st.caption("Fast capture with split intelligence war rooms: Walk vs Booth.")

nav = st.sidebar.radio(
    "Navigate",
    ["Capture", "Walk War Room", "Booth War Room", "Executive Summary"],
    index=0,
)

df_all = load_all_entries()
if "mode" in df_all.columns:
    walk_df = df_all[df_all["mode"] == "Walk"].copy()
    booth_df = df_all[df_all["mode"] == "Booth"].copy()
else:
    walk_df = pd.DataFrame()
    booth_df = pd.DataFrame()

if nav == "Capture":
    changed = render_capture_view()
    if changed:
        df_all = load_all_entries()
    render_export_controls(df_all, df_all, "capture")
elif nav == "Walk War Room":
    render_walk_war_room(walk_df)
    render_export_controls(df_all, walk_df, "walk")
elif nav == "Booth War Room":
    render_booth_war_room(booth_df)
    render_export_controls(df_all, booth_df, "booth")
else:
    render_exec_summary(df_all)
    render_export_controls(df_all, df_all, "executive")

st.caption("Replit run command: streamlit run app.py --server.port 3000 --server.address 0.0.0.0")
