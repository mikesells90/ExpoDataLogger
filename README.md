# Expo Intel Radar

Production-ready Streamlit app for fast trade show competitive intelligence capture and analysis.

## Stack
- Python
- Streamlit
- SQLite (SQLAlchemy)
- Plotly
- scikit-learn

## Local Run
```bash
cd expo_intel
pip install -r requirements.txt
streamlit run app.py --server.port 3000 --server.address 0.0.0.0
```

## Replit Run
This repo includes:
- `.replit`
- `replit.nix`

Open/import in Replit and press **Run**.

## File Layout
```text
expo_intel/
  app.py
  database.py
  models.py
  analytics.py
  intelligence.py
  ml.py
  utils.py
  requirements.txt
  data/expo.db
```

## Notes
- Clustering activates once there are at least 12 rows.
- Data is stored in `expo_intel/data/expo.db`.
- Schema is SQLAlchemy-based and structured for future Postgres migration.
