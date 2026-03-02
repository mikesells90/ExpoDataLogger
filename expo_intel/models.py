from sqlalchemy import Column, Float, Integer, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class BoothEntry(Base):
    __tablename__ = "booth_entries"

    id = Column(Text, primary_key=True, index=True)
    timestamp = Column(Text, nullable=False, index=True)
    mode = Column(Text, nullable=False, index=True)
    time_block = Column(Text, nullable=False)
    brand_name = Column(Text, nullable=False, index=True)

    category = Column(Text)
    format = Column(Text)
    channel_target = Column(Text)

    flavor_mode = Column(Text)
    heat_index = Column(Integer)
    sugar_signal = Column(Text)
    ingredient_signals = Column(Text)

    primary_claim = Column(Text)
    claim_density = Column(Text)
    claim_aggression = Column(Integer)

    premium_signal = Column(Integer)
    chaos_signal = Column(Integer)
    sampling_heavy = Column(Integer)
    influencer_visible = Column(Integer)

    production_complexity = Column(Integer)
    co_pack_friendly = Column(Text)
    sku_spread = Column(Text)
    margin_smell_test = Column(Text)
    would_fund = Column(Text)

    saturation_nearby = Column(Text)
    differentiation = Column(Integer)
    forecast = Column(Text)
    confidence = Column(Text)

    blue_ocean_tag = Column(Text)
    threat_flag = Column(Integer)
    traffic_behavior = Column(Text)

    visitor_role = Column(Text)
    first_question = Column(Text)
    engagement_depth = Column(Integer)
    follow_up = Column(Integer)
    objections = Column(Text)
    positioning_angle = Column(Text)
    response_strength = Column(Integer)

    forced_insight = Column(Text)

    blue_ocean_score = Column(Float)
    threat_score = Column(Float)
    archetype = Column(Text)
    cluster_id = Column(Integer)
    cluster_label = Column(Text)
