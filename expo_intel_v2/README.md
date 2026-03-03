# Expo Intelligence System v2

This is a parallel production architecture added to `main`:
- Backend: FastAPI
- Frontend: React (Vite)
- Database: Postgres
- Charts: Plotly

## Features
- Two data models:
  - `expo_walk_scan` (rapid floor scans)
  - `expo_deep_eval` (in-booth deep evaluations)
- Modular scoring engine:
  - PRS, CTI, POS, SPS
  - Tier auto-assignment
- Cursor-based exhibitor ingestion (`/ingest/cursor`)
- Keyword scanning from free text fields
- Real-time scoring on save
- Hall heat map aggregation
- Strategic ranking board
- Tier1 follow-up queue
- Filters:
  - Meat-forward only
  - Organic only
  - Direct competitors only
  - High partnership potential only

## Run backend
```bash
cd expo_intel_v2/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Run frontend
```bash
cd expo_intel_v2/frontend
npm install
npm run dev
```

## Postgres local (optional)
```bash
cd expo_intel_v2
docker compose up -d
```

Set `DATABASE_URL` before starting backend:
`postgresql+psycopg2://postgres:postgres@localhost:5432/expo_intel`
