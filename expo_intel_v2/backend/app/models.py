from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.database import Base


def json_type():
    return JSON().with_variant(JSONB, "postgresql")


class ExpoWalkScan(Base):
    __tablename__ = "expo_walk_scan"
    __table_args__ = (
        CheckConstraint("protein_signal_score BETWEEN 1 AND 5", name="ck_walk_protein_signal"),
        CheckConstraint("competitive_threat_score BETWEEN 1 AND 5", name="ck_walk_threat_signal"),
        CheckConstraint("prs_score BETWEEN 0 AND 100", name="ck_walk_prs"),
        CheckConstraint("cti_score BETWEEN 0 AND 100", name="ck_walk_cti"),
        CheckConstraint("pos_score BETWEEN 0 AND 100", name="ck_walk_pos"),
        CheckConstraint("sps_score BETWEEN 0 AND 100", name="ck_walk_sps"),
        CheckConstraint("follow_up_flag IN ('revisit','deep_dive','skip')", name="ck_walk_follow_up"),
        CheckConstraint("tier IN ('tier1','tier2','tier3')", name="ck_walk_tier"),
        CheckConstraint("score_confidence IN ('low','medium','high')", name="ck_walk_score_confidence"),
        Index("idx_walk_company_booth", "company_name", "booth_number"),
        Index("idx_walk_sps", "sps_score"),
        Index("idx_walk_category_tags_gin", "category_tags", postgresql_using="gin"),
    )

    scan_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    event_slug = Column(Text, nullable=False, server_default="natural-products-expo-west-2026", index=True)

    company_name = Column(Text, nullable=False, index=True)
    booth_number = Column(Text, nullable=True)
    hall = Column(Text, nullable=True)

    category_tags = Column(json_type(), nullable=False, default=list, server_default="[]")
    protein_signal_score = Column(Integer, nullable=False)
    competitive_threat_score = Column(Integer, nullable=False)
    follow_up_flag = Column(Text, nullable=False)

    usda_flag = Column(Boolean, nullable=False, default=False, server_default="false")
    organic_flag = Column(Boolean, nullable=False, default=False, server_default="false")
    sqf_flag = Column(Boolean, nullable=False, default=False, server_default="false")
    regenerative_flag = Column(Boolean, nullable=False, default=False, server_default="false")
    emerging_brand_flag = Column(Boolean, nullable=False, default=False, server_default="false")

    quick_notes = Column(Text, nullable=True)

    prs_score = Column(Integer, nullable=False, default=0, server_default="0")
    cti_score = Column(Integer, nullable=False, default=0, server_default="0")
    pos_score = Column(Integer, nullable=False, default=0, server_default="0")
    sps_score = Column(Integer, nullable=False, default=0, server_default="0")
    tier = Column(Text, nullable=False, default="tier3", server_default="tier3")
    score_confidence = Column(Text, nullable=False, default="medium", server_default="medium")


class ExpoDeepEval(Base):
    __tablename__ = "expo_deep_eval"
    __table_args__ = (
        CheckConstraint("strategic_fit_score BETWEEN 1 AND 5", name="ck_eval_fit"),
        CheckConstraint("competitive_threat_score BETWEEN 1 AND 5", name="ck_eval_threat"),
        CheckConstraint("partnership_potential_score BETWEEN 1 AND 5", name="ck_eval_partnership"),
        CheckConstraint("manufacturing_type IN ('self','co_pack','unknown')", name="ck_eval_mfg"),
        CheckConstraint("estimated_scale IN ('small','mid','national')", name="ck_eval_scale"),
        CheckConstraint("post_show_priority IN ('tier1','tier2','tier3')", name="ck_eval_priority"),
        CheckConstraint("tier_suggested IN ('tier1','tier2','tier3')", name="ck_eval_tier_suggested"),
        CheckConstraint("score_confidence IN ('low','medium','high')", name="ck_eval_score_confidence"),
        CheckConstraint("prs_score BETWEEN 0 AND 100", name="ck_eval_prs"),
        CheckConstraint("cti_score BETWEEN 0 AND 100", name="ck_eval_cti"),
        CheckConstraint("pos_score BETWEEN 0 AND 100", name="ck_eval_pos"),
        CheckConstraint("sps_score BETWEEN 0 AND 100", name="ck_eval_sps"),
        Index("idx_eval_company_booth", "company_name", "booth_number"),
        Index("idx_eval_sps", "sps_score"),
    )

    eval_id = Column(String, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    event_slug = Column(Text, nullable=False, server_default="natural-products-expo-west-2026", index=True)

    company_name = Column(Text, nullable=False, index=True)
    booth_number = Column(Text, nullable=True)
    hall = Column(Text, nullable=True)

    contact_name = Column(Text, nullable=True)
    contact_email = Column(Text, nullable=True)
    contact_role = Column(Text, nullable=True)
    website = Column(Text, nullable=True)

    core_skus = Column(Text, nullable=True)
    format_type = Column(Text, nullable=True)
    pack_size = Column(Text, nullable=True)
    price_per_unit = Column(Numeric(10, 2), nullable=True)

    claims_tags = Column(json_type(), nullable=False, default=list, server_default="[]")
    manufacturing_type = Column(Text, nullable=False, default="unknown", server_default="unknown")
    certifications = Column(json_type(), nullable=False, default=list, server_default="[]")
    estimated_scale = Column(Text, nullable=False, default="small", server_default="small")
    kill_step_type = Column(Text, nullable=True)

    channel_presence = Column(json_type(), nullable=False, default=list, server_default="[]")

    direct_competitor_flag = Column(Boolean, nullable=False, default=False, server_default="false")
    closest_charcut_sku = Column(Text, nullable=True)
    differentiator_notes = Column(Text, nullable=True)
    weakness_notes = Column(Text, nullable=True)
    what_they_do_better = Column(Text, nullable=True)
    what_we_do_better = Column(Text, nullable=True)

    strategic_fit_score = Column(Integer, nullable=False)
    competitive_threat_score = Column(Integer, nullable=False)
    partnership_potential_score = Column(Integer, nullable=False)

    action_plan = Column(json_type(), nullable=False, default=list, server_default="[]")
    post_show_priority = Column(Text, nullable=False, default="tier3", server_default="tier3")
    full_notes = Column(Text, nullable=True)

    prs_score = Column(Integer, nullable=False, default=0, server_default="0")
    cti_score = Column(Integer, nullable=False, default=0, server_default="0")
    pos_score = Column(Integer, nullable=False, default=0, server_default="0")
    sps_score = Column(Integer, nullable=False, default=0, server_default="0")
    tier_suggested = Column(Text, nullable=False, default="tier3", server_default="tier3")
    score_confidence = Column(Text, nullable=False, default="high", server_default="high")


class ExpoExhibitorsRaw(Base):
    __tablename__ = "expo_exhibitors_raw"
    __table_args__ = (Index("idx_exhibitor_id", "exhibitor_id"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    exhibitor_id = Column(Text, nullable=True)
    name = Column(Text, nullable=True)
    exhibitor_type = Column(Text, nullable=True)
    booth = Column(Text, nullable=True)
    description_html = Column(Text, nullable=True)
    logo_url = Column(Text, nullable=True)
    raw_json = Column(json_type(), nullable=False, default=dict, server_default="{}")

