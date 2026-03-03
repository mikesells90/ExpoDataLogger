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
                "meta_json": r.meta_json,
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
    meta_payload = {}

    def parse_csv_list(raw: str) -> list[str]:
        return [x.strip() for x in (raw or "").split(",") if x.strip()]

    top1, top2, top3, top4, top5 = st.columns([1.4, 1.2, 1.1, 1.4, 1.5])
    with top1:
        mode = st.selectbox("Capture Type", ["Walk", "Booth"], key="mode")
    with top2:
        time_block = st.radio("Time Block", ["AM", "Midday", "PM"], horizontal=True, key="time_block")
    with top3:
        st.toggle("Executive Mode", key="executive_mode")
    with top4:
        st.toggle("Repeat Last Settings", key="repeat_last_settings")
    with top5:
        st.toggle("Quick Add Mode", key="quick_add_mode")

    with st.form("capture_form", clear_on_submit=False):
        brand_name = st.text_input("Company Name *", value="", placeholder="Type company and submit fast")
        quick_add_mode = st.session_state.get("quick_add_mode", False)

        if quick_add_mode:
            st.caption("Quick Add is on: only brand, mode, and time block are required.")
            submitted = st.form_submit_button("Save Quick Entry", use_container_width=True, type="primary")
        else:
            if mode == "Walk":
                st.markdown("#### Walk Rapid Scan")
                c1, c2 = st.columns(2)
                with c1:
                    booth_number = st.text_input("Booth Number")
                    hall = st.text_input("Hall")
                    category_tags_raw = st.text_input("Category Tags (comma separated)")
                    protein_signal_score = st.slider("Protein Signal Score", 1, 5, 3)
                    competitive_threat_score = st.slider("Competitive Threat Score", 1, 5, 3)
                    follow_up_flag = st.selectbox("Follow Up Flag", ["revisit", "deep_dive", "skip"])
                with c2:
                    usda_flag = st.checkbox("USDA")
                    organic_flag = st.checkbox("Organic")
                    sqf_flag = st.checkbox("SQF")
                    regenerative_flag = st.checkbox("Regenerative")
                    emerging_brand_flag = st.checkbox("Emerging Brand")
                    quick_notes = st.text_area("Quick Notes", max_chars=500)
                    b1, b2 = st.columns(2)
                    quick_blue = b1.form_submit_button("Quick Blue Hint", use_container_width=True)
                    quick_danger = b2.form_submit_button("Quick Dangerous Early", use_container_width=True)

                category_tags = parse_csv_list(category_tags_raw)
                threat_band = "High" if competitive_threat_score >= 4 else ("Low" if competitive_threat_score <= 2 else "Medium")

                meta_payload = {
                    "schema": "expo_walk_scan",
                    "booth_number": booth_number,
                    "hall": hall,
                    "category_tags": category_tags,
                    "protein_signal_score": protein_signal_score,
                    "competitive_threat_score": competitive_threat_score,
                    "usda_flag": usda_flag,
                    "organic_flag": organic_flag,
                    "sqf_flag": sqf_flag,
                    "regenerative_flag": regenerative_flag,
                    "emerging_brand_flag": emerging_brand_flag,
                    "quick_notes": quick_notes,
                    "follow_up_flag": follow_up_flag,
                }

                form_data = {
                    "category": category_tags[0] if category_tags else "Other",
                    "format": "Other",
                    "channel_target": hall,
                    "flavor_mode": [],
                    "heat_index": 0,
                    "sugar_signal": "Unknown",
                    "ingredient_signals": [],
                    "primary_claim": category_tags[0] if category_tags else "Other",
                    "claim_density": "2-3",
                    "claim_aggression": competitive_threat_score,
                    "premium_signal": protein_signal_score,
                    "chaos_signal": competitive_threat_score,
                    "sampling_heavy": False,
                    "influencer_visible": False,
                    "production_complexity": 3,
                    "co_pack_friendly": "Maybe",
                    "sku_spread": "1-3",
                    "margin_smell_test": "Medium",
                    "would_fund": "With Changes",
                    "saturation_nearby": threat_band,
                    "differentiation": protein_signal_score,
                    "forecast": "Survive",
                    "confidence": "Medium",
                    "forced_insight": (quick_notes or "")[:120],
                    "blue_ocean_tag": hall,
                    "threat_flag": competitive_threat_score >= 4,
                    "traffic_behavior": category_tags,
                    "visitor_role": None,
                    "first_question": None,
                    "engagement_depth": None,
                    "follow_up": False,
                    "objections": [],
                    "positioning_angle": f"Booth {booth_number}" if booth_number else None,
                    "response_strength": None,
                }
            else:
                st.markdown("#### Booth Deep Evaluation")
                c1, c2 = st.columns(2)
                with c1:
                    booth_number = st.text_input("Booth Number")
                    contact_name = st.text_input("Contact Name")
                    contact_email = st.text_input("Contact Email")
                    contact_role = st.text_input("Contact Role")
                    website = st.text_input("Website")
                    core_skus = st.text_area("Core SKUs")
                    format_type = st.text_input("Format Type")
                    pack_size = st.text_input("Pack Size")
                    price_per_unit = st.number_input("Price per Unit", min_value=0.0, value=0.0, step=0.01)
                    claims_tags_raw = st.text_input("Claims Tags (comma separated)")
                    certifications_raw = st.text_input("Certifications (comma separated)")
                with c2:
                    manufacturing_type = st.selectbox("Manufacturing Type", ["self", "co_pack", "unknown"])
                    estimated_scale = st.selectbox("Estimated Scale", ["small", "mid", "national"])
                    channel_presence = st.multiselect("Channel Presence", ["retail", "club", "foodservice", "dtc", "amazon", "meal_kit"])
                    direct_competitor_flag = st.checkbox("Direct Competitor")
                    closest_charcut_sku = st.text_input("Closest Charcut SKU")
                    strategic_fit_score = st.slider("Strategic Fit Score", 1, 5, 3)
                    competitive_threat_score = st.slider("Competitive Threat Score", 1, 5, 3)
                    partnership_potential_score = st.slider("Partnership Potential Score", 1, 5, 3)
                    strength_notes = st.text_area("Strength Notes")
                    weakness_notes = st.text_area("Weakness Notes")
                    action_plan_raw = st.text_input("Action Plan (comma separated)")
                    post_show_priority = st.selectbox("Post Show Priority", ["tier1", "tier2", "tier3"])

                claims_tags = parse_csv_list(claims_tags_raw)
                certifications = parse_csv_list(certifications_raw)
                action_plan = parse_csv_list(action_plan_raw)
                complexity = 4 if manufacturing_type == "self" else (2 if manufacturing_type == "co_pack" else 3)
                margin_band = "High" if price_per_unit >= 6 else ("Medium" if price_per_unit >= 3 else "Low")
                scale_to_forecast = {"small": "Survive", "mid": "Scale", "national": "Acquire"}
                would_fund = "Yes" if post_show_priority == "tier1" else ("With Changes" if post_show_priority == "tier2" else "No")

                meta_payload = {
                    "schema": "expo_deep_eval",
                    "booth_number": booth_number,
                    "contact_name": contact_name,
                    "contact_email": contact_email,
                    "contact_role": contact_role,
                    "website": website,
                    "core_skus": core_skus,
                    "format_type": format_type,
                    "pack_size": pack_size,
                    "price_per_unit": price_per_unit,
                    "claims_tags": claims_tags,
                    "manufacturing_type": manufacturing_type,
                    "certifications": certifications,
                    "estimated_scale": estimated_scale,
                    "channel_presence": channel_presence,
                    "direct_competitor_flag": direct_competitor_flag,
                    "closest_charcut_sku": closest_charcut_sku,
                    "strategic_fit_score": strategic_fit_score,
                    "competitive_threat_score": competitive_threat_score,
                    "partnership_potential_score": partnership_potential_score,
                    "strength_notes": strength_notes,
                    "weakness_notes": weakness_notes,
                    "action_plan": action_plan,
                    "post_show_priority": post_show_priority,
                }

                form_data = {
                    "category": claims_tags[0] if claims_tags else "Other",
                    "format": format_type or "Other",
                    "channel_target": ", ".join(channel_presence),
                    "flavor_mode": [],
                    "heat_index": 0,
                    "sugar_signal": "Unknown",
                    "ingredient_signals": certifications,
                    "primary_claim": closest_charcut_sku or "Deep Eval",
                    "claim_density": "2-3",
                    "claim_aggression": competitive_threat_score,
                    "premium_signal": strategic_fit_score,
                    "chaos_signal": competitive_threat_score,
                    "sampling_heavy": False,
                    "influencer_visible": False,
                    "production_complexity": complexity,
                    "co_pack_friendly": "Yes" if manufacturing_type == "co_pack" else ("No" if manufacturing_type == "self" else "Maybe"),
                    "sku_spread": "4-8",
                    "margin_smell_test": margin_band,
                    "would_fund": would_fund,
                    "saturation_nearby": "High" if direct_competitor_flag else "Medium",
                    "differentiation": partnership_potential_score,
                    "forecast": scale_to_forecast.get(estimated_scale, "Survive"),
                    "confidence": "Medium",
                    "forced_insight": (strength_notes or "")[:120],
                    "blue_ocean_tag": None,
                    "threat_flag": direct_competitor_flag,
                    "traffic_behavior": [],
                    "visitor_role": contact_role,
                    "first_question": closest_charcut_sku,
                    "engagement_depth": strategic_fit_score,
                    "follow_up": post_show_priority in {"tier1", "tier2"},
                    "objections": parse_csv_list(weakness_notes),
                    "positioning_angle": core_skus,
                    "response_strength": partnership_potential_score,
                }

            submitted = st.form_submit_button("Submit Intel", use_container_width=True, type="primary")

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
            meta_json=to_json(meta_payload),
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

df_all = load_all_entries()
if "mode" in df_all.columns:
    walk_df = df_all[df_all["mode"] == "Walk"].copy()
    booth_df = df_all[df_all["mode"] == "Booth"].copy()
else:
    walk_df = pd.DataFrame()
    booth_df = pd.DataFrame()

capture_tab, walk_tab, booth_tab, exec_tab = st.tabs(
    ["Capture", "Walk War Room", "Booth War Room", "Executive Summary"]
)

with capture_tab:
    changed = render_capture_view()
    if changed:
        df_all = load_all_entries()
        if "mode" in df_all.columns:
            walk_df = df_all[df_all["mode"] == "Walk"].copy()
            booth_df = df_all[df_all["mode"] == "Booth"].copy()
    render_export_controls(df_all, df_all, "capture")

with walk_tab:
    st.caption(f"Showing Walk entries only: {len(walk_df)}")
    render_walk_war_room(walk_df)
    render_export_controls(df_all, walk_df, "walk")

with booth_tab:
    st.caption(f"Showing Booth entries only: {len(booth_df)}")
    render_booth_war_room(booth_df)
    render_export_controls(df_all, booth_df, "booth")

with exec_tab:
    render_exec_summary(df_all)
    render_export_controls(df_all, df_all, "executive")

st.caption("Replit run command: streamlit run app.py --server.port 3000 --server.address 0.0.0.0")
