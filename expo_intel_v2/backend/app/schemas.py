from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

FOLLOW_UP_FLAGS = ["revisit", "deep_dive", "skip"]
PRIORITIES = ["tier1", "tier2", "tier3"]
MFG_TYPES = ["self", "co_pack", "unknown"]
SCALE_TYPES = ["small", "mid", "national"]
CONFIDENCE_TYPES = ["low", "medium", "high"]


def _list_or_empty(value):
    return value if isinstance(value, list) else []


class WalkScanBase(BaseModel):
    event_slug: str = "natural-products-expo-west-2026"
    company_name: str
    booth_number: Optional[str] = None
    hall: Optional[str] = None
    category_tags: list[str] = Field(default_factory=list)
    protein_signal_score: int
    competitive_threat_score: int
    follow_up_flag: Literal["revisit", "deep_dive", "skip"]
    usda_flag: bool = False
    organic_flag: bool = False
    sqf_flag: bool = False
    regenerative_flag: bool = False
    emerging_brand_flag: bool = False
    quick_notes: Optional[str] = Field(default=None, max_length=500)

    @field_validator("protein_signal_score", "competitive_threat_score")
    @classmethod
    def _validate_1_5(cls, value: int):
        if value < 1 or value > 5:
            raise ValueError("must be between 1 and 5")
        return value


class WalkScanCreate(WalkScanBase):
    scan_id: Optional[str] = None


class WalkScanOut(WalkScanBase):
    scan_id: str
    created_at: datetime
    updated_at: datetime
    prs_score: int
    cti_score: int
    pos_score: int
    sps_score: int
    tier: Literal["tier1", "tier2", "tier3"]
    score_confidence: Literal["low", "medium", "high"]

    model_config = ConfigDict(from_attributes=True)


class DeepEvalBase(BaseModel):
    event_slug: str = "natural-products-expo-west-2026"
    company_name: str
    booth_number: Optional[str] = None
    hall: Optional[str] = None

    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_role: Optional[str] = None
    website: Optional[str] = None

    core_skus: Optional[str] = None
    format_type: Optional[str] = None
    pack_size: Optional[str] = None
    price_per_unit: Optional[float] = None

    claims_tags: list[str] = Field(default_factory=list)
    manufacturing_type: Literal["self", "co_pack", "unknown"]
    certifications: list[str] = Field(default_factory=list)
    estimated_scale: Literal["small", "mid", "national"]
    kill_step_type: Optional[str] = None

    channel_presence: list[str] = Field(default_factory=list)

    direct_competitor_flag: bool = False
    closest_charcut_sku: Optional[str] = None
    differentiator_notes: Optional[str] = None
    weakness_notes: Optional[str] = None
    what_they_do_better: Optional[str] = None
    what_we_do_better: Optional[str] = None

    strategic_fit_score: int
    competitive_threat_score: int
    partnership_potential_score: int

    action_plan: list[str] = Field(default_factory=list)
    post_show_priority: Literal["tier1", "tier2", "tier3"]
    full_notes: Optional[str] = None

    @field_validator("strategic_fit_score", "competitive_threat_score", "partnership_potential_score")
    @classmethod
    def _validate_1_5(cls, value: int):
        if value < 1 or value > 5:
            raise ValueError("must be between 1 and 5")
        return value


class DeepEvalCreate(DeepEvalBase):
    eval_id: Optional[str] = None


class DeepEvalOut(DeepEvalBase):
    eval_id: str
    created_at: datetime
    updated_at: datetime
    prs_score: int
    cti_score: int
    pos_score: int
    sps_score: int
    tier_suggested: Literal["tier1", "tier2", "tier3"]
    score_confidence: Literal["low", "medium", "high"]

    model_config = ConfigDict(from_attributes=True)


class ExhibitorCursorIngest(BaseModel):
    cursor: Optional[str] = None
    exhibitors: list[dict] = Field(default_factory=list)

    @field_validator("exhibitors", mode="before")
    @classmethod
    def _normalize_exhibitors(cls, value):
        return _list_or_empty(value)


class GraphQLIngestRequest(BaseModel):
    max_pages: int = 50
    delay_seconds: float = 0.4


class HeatMapRow(BaseModel):
    hall: str
    booth_count: int
    total_sps: float
    avg_sps: float
    density_score: float
    heat_color: str


class StrategicRankingRow(BaseModel):
    source: Literal["walk", "deep_eval", "combined"]
    record_id: str
    company_name: str
    booth_number: Optional[str] = None
    hall: Optional[str] = None
    sps_score: Optional[int] = None
    tier: Optional[str] = None
    score_confidence: Optional[str] = None

