import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from intelligence import CLAIM_DENSITY_MAP, SATURATION_MAP
from models import BoothEntry

FEATURE_COLUMNS = [
    "saturation_numeric",
    "differentiation",
    "claim_density_numeric",
    "claim_aggression",
    "premium_signal",
    "chaos_signal",
    "production_complexity",
    "mode_encoded",
    "engagement_depth",
]


def _coerce_numeric(value, default=0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _cluster_label(centroid: dict) -> str:
    if centroid["chaos_signal"] >= 4 and centroid["claim_density_numeric"] >= 4:
        return "Loud Overclaimers"
    if centroid["premium_signal"] >= 4 and centroid["differentiation"] >= 4:
        return "Premium Differentiators"
    if centroid["saturation_numeric"] <= 2 and centroid["differentiation"] >= 4:
        return "Whitespace Pocket"
    if centroid["chaos_signal"] >= 4 and centroid["mode_encoded"] >= 0.5:
        return "Chaotic Influencers"
    if centroid["production_complexity"] >= 4 and centroid["differentiation"] <= 2:
        return "Fragile Complexity"
    return "Me Too Zone"


def update_clusters(session) -> None:
    entries = session.query(BoothEntry).all()
    if len(entries) < 12:
        # Keep clusters empty until enough signal exists.
        for row in entries:
            row.cluster_id = None
            row.cluster_label = None
        session.commit()
        return

    rows = []
    for row in entries:
        rows.append(
            {
                "id": row.id,
                "saturation_numeric": SATURATION_MAP.get(row.saturation_nearby, 3),
                "differentiation": _coerce_numeric(row.differentiation, 3),
                "claim_density_numeric": CLAIM_DENSITY_MAP.get(row.claim_density, 3),
                "claim_aggression": _coerce_numeric(row.claim_aggression, 3),
                "premium_signal": _coerce_numeric(row.premium_signal, 3),
                "chaos_signal": _coerce_numeric(row.chaos_signal, 3),
                "production_complexity": _coerce_numeric(row.production_complexity, 3),
                "mode_encoded": 1.0 if row.mode == "Booth" else 0.0,
                "engagement_depth": _coerce_numeric(row.engagement_depth, 0),
            }
        )

    df = pd.DataFrame(rows)
    X = df[FEATURE_COLUMNS].fillna(0.0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    best_k = 3
    best_score = -1.0
    max_k = min(6, len(df) - 1)
    # Lightweight auto-k search tuned for small field datasets.
    for k in range(3, max_k + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X_scaled)
        score = silhouette_score(X_scaled, labels)
        if score > best_score:
            best_score = score
            best_k = k

    final_model = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    final_labels = final_model.fit_predict(X_scaled)
    centroids_scaled = final_model.cluster_centers_
    centroids = scaler.inverse_transform(centroids_scaled)

    cluster_label_map = {}
    for idx, centroid_values in enumerate(centroids):
        centroid = {name: centroid_values[i] for i, name in enumerate(FEATURE_COLUMNS)}
        cluster_label_map[idx] = _cluster_label(centroid)

    label_by_id = dict(zip(df["id"], final_labels.tolist()))
    for row in entries:
        cid = int(label_by_id[row.id])
        row.cluster_id = cid
        row.cluster_label = cluster_label_map.get(cid, "Me Too Zone")

    session.commit()
