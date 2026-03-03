from app.scoring import compute_cti, compute_pos, compute_prs, compute_sps, compute_tier, derive_scores


def test_direct_meat_competitor_costco_national_is_tier1():
    payload = {
        "protein_signal_score": 5,
        "category_tags": ["Meat/Jerky/Sausage"],
        "claims_tags": ["High Protein", "Organic"],
        "format_type": "stick",
        "competitive_threat_score": 5,
        "direct_competitor_flag": True,
        "estimated_scale": "national",
        "channel_presence": ["Club", "Retail"],
        "partnership_potential_score": 2,
        "manufacturing_type": "self",
        "certifications": ["USDA"],
    }
    prs = compute_prs(payload)
    cti = compute_cti(payload)
    pos = compute_pos(payload)
    sps = compute_sps(prs, cti, pos)
    assert cti >= 80
    assert sps >= 75
    assert compute_tier(sps) == "tier1"


def test_ingredient_supplier_with_usda_organic_has_high_pos():
    payload = {
        "protein_signal_score": 3,
        "category_tags": ["Ingredient Supplier"],
        "claims_tags": ["Organic"],
        "format_type": "powder",
        "competitive_threat_score": 2,
        "direct_competitor_flag": False,
        "estimated_scale": "mid",
        "channel_presence": ["Distribution"],
        "partnership_potential_score": 5,
        "manufacturing_type": "co_pack",
        "certifications": ["USDA", "Organic", "SQF"],
    }
    pos = compute_pos(payload)
    assert pos >= 60
    scores = derive_scores(payload)
    assert scores.sps_score >= 50


def test_plant_protein_dtc_only_is_lower_tier():
    payload = {
        "protein_signal_score": 3,
        "category_tags": ["Plant Protein"],
        "claims_tags": ["No Sugar"],
        "format_type": "frozen entree",
        "competitive_threat_score": 2,
        "direct_competitor_flag": False,
        "estimated_scale": "small",
        "channel_presence": ["DTC"],
        "partnership_potential_score": 2,
        "manufacturing_type": "unknown",
        "certifications": [],
    }
    scores = derive_scores(payload)
    assert scores.prs_score < 70
    assert scores.cti_score < 40
    assert scores.tier in {"tier2", "tier3"}

