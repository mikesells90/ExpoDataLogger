from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.types import JSON

from app.database import Base


def json_type():
    return JSON().with_variant(JSONB, "postgresql")


class ExpoWalkScan(Base):
    __tablename__ = "expo_walk_scan"

    scan_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)
    booth_number = Column(String, nullable=True)
    hall = Column(String, nullable=True, index=True)

    category_tags = Column(json_type(), nullable=True)
    protein_signal_score = Column(Integer, nullable=True)
    competitive_threat_score = Column(Integer, nullable=True)

    usda_flag = Column(Boolean, nullable=True)
    organic_flag = Column(Boolean, nullable=True)
    sqf_flag = Column(Boolean, nullable=True)
    regenerative_flag = Column(Boolean, nullable=True)
    emerging_brand_flag = Column(Boolean, nullable=True)

    quick_notes = Column(Text, nullable=True)
    follow_up_flag = Column(String, nullable=True)

    prs_score = Column(Float, nullable=True)
    cti_score = Column(Float, nullable=True)
    pos_score = Column(Float, nullable=True)
    sps_score = Column(Float, nullable=True, index=True)
    tier = Column(String, nullable=True, index=True)


class ExpoDeepEval(Base):
    __tablename__ = "expo_deep_eval"

    eval_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    company_name = Column(String, nullable=False, index=True)
    booth_number = Column(String, nullable=True)

    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_role = Column(String, nullable=True)
    website = Column(String, nullable=True)

    core_skus = Column(Text, nullable=True)
    format_type = Column(String, nullable=True)
    pack_size = Column(String, nullable=True)
    price_per_unit = Column(Float, nullable=True)

    claims_tags = Column(json_type(), nullable=True)
    manufacturing_type = Column(String, nullable=True)
    certifications = Column(json_type(), nullable=True)
    estimated_scale = Column(String, nullable=True)

    channel_presence = Column(json_type(), nullable=True)

    direct_competitor_flag = Column(Boolean, nullable=True)
    closest_charcut_sku = Column(String, nullable=True)

    strategic_fit_score = Column(Integer, nullable=True)
    competitive_threat_score = Column(Integer, nullable=True)
    partnership_potential_score = Column(Integer, nullable=True)

    strength_notes = Column(Text, nullable=True)
    weakness_notes = Column(Text, nullable=True)
    action_plan = Column(json_type(), nullable=True)

    post_show_priority = Column(String, nullable=True)

    prs_score = Column(Float, nullable=True)
    cti_score = Column(Float, nullable=True)
    pos_score = Column(Float, nullable=True)
    sps_score = Column(Float, nullable=True, index=True)
    tier = Column(String, nullable=True, index=True)
