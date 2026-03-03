from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WalkScanBase(BaseModel):
    timestamp: Optional[datetime] = None
    company_name: str
    booth_number: Optional[str] = None
    hall: Optional[str] = None

    category_tags: list[str] = Field(default_factory=list)
    protein_signal_score: Optional[int] = None
    competitive_threat_score: Optional[int] = None

    usda_flag: Optional[bool] = None
    organic_flag: Optional[bool] = None
    sqf_flag: Optional[bool] = None
    regenerative_flag: Optional[bool] = None
    emerging_brand_flag: Optional[bool] = None

    quick_notes: Optional[str] = None
    follow_up_flag: Optional[str] = None


class WalkScanCreate(WalkScanBase):
    scan_id: Optional[str] = None


class WalkScanOut(WalkScanBase):
    scan_id: str
    prs_score: Optional[float] = None
    cti_score: Optional[float] = None
    pos_score: Optional[float] = None
    sps_score: Optional[float] = None
    tier: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DeepEvalBase(BaseModel):
    timestamp: Optional[datetime] = None
    company_name: str
    booth_number: Optional[str] = None

    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_role: Optional[str] = None
    website: Optional[str] = None

    core_skus: Optional[str] = None
    format_type: Optional[str] = None
    pack_size: Optional[str] = None
    price_per_unit: Optional[float] = None

    claims_tags: list[str] = Field(default_factory=list)
    manufacturing_type: Optional[str] = None
    certifications: list[str] = Field(default_factory=list)
    estimated_scale: Optional[str] = None

    channel_presence: list[str] = Field(default_factory=list)

    direct_competitor_flag: Optional[bool] = None
    closest_charcut_sku: Optional[str] = None

    strategic_fit_score: Optional[int] = None
    competitive_threat_score: Optional[int] = None
    partnership_potential_score: Optional[int] = None

    strength_notes: Optional[str] = None
    weakness_notes: Optional[str] = None
    action_plan: list[str] = Field(default_factory=list)

    post_show_priority: Optional[str] = None


class DeepEvalCreate(DeepEvalBase):
    eval_id: Optional[str] = None


class DeepEvalOut(DeepEvalBase):
    eval_id: str
    prs_score: Optional[float] = None
    cti_score: Optional[float] = None
    pos_score: Optional[float] = None
    sps_score: Optional[float] = None
    tier: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExhibitorCursorIngest(BaseModel):
    cursor: Optional[str] = None
    exhibitors: list[dict] = Field(default_factory=list)


class HeatMapRow(BaseModel):
    hall: str
    booth_count: int
    avg_sps: float
    heat_color: str


class StrategicRankingRow(BaseModel):
    source: str
    record_id: str
    company_name: str
    booth_number: Optional[str] = None
    sps_score: Optional[float] = None
    tier: Optional[str] = None

