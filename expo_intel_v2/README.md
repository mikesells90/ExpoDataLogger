# Expo Intelligence System (Expo West 2026)

Stack:
- Backend: FastAPI
- DB: Postgres
- Frontend: React (Vite)
- Charts: Plotly
- Export: CSV + JSON

## Backend setup
```bash
cd expo_intel_v2/backend
pip install -r requirements.txt
```

Set env vars:
- `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/expo_intel`
- Optional MVP auth: `APP_PASSWORD=your-password` (client must send `x-app-password` header)

Run API:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run tests:
```bash
pytest -q
```

## DB migration
SQL migration file:
- `expo_intel_v2/backend/migrations/001_init.sql`

Apply with psql:
```bash
psql "$DATABASE_URL" -f expo_intel_v2/backend/migrations/001_init.sql
```

## Frontend setup
```bash
cd expo_intel_v2/frontend
npm install
```

Set API base:
- `VITE_API_BASE=http://localhost:8000`

Run:
```bash
npm run dev
```

## Production deploy (Render)
This repo includes:
- `expo_intel_v2/backend/Dockerfile`
- `expo_intel_v2/frontend/Dockerfile`
- `expo_intel_v2/render.yaml`

Steps:
1. Create a new Render Blueprint from `expo_intel_v2/render.yaml`
2. Provision the Postgres database
3. Deploy API (`expo-intel-api`) and UI (`expo-intel-ui`)
4. Optionally set `APP_PASSWORD` on API service

Notes:
- API listens on port `8000`
- UI serves static React bundle via nginx
- If you use a custom frontend URL, set backend `FRONTEND_ORIGIN` accordingly

## Implemented pages
1. Walking Dashboard
2. Deep Evaluation Dashboard
3. Strategic Ranking Board
4. Hall Heat Map
5. Follow-up Queue (Tier1)

## Key backend endpoints
- `POST /walk-scans`
- `GET /walk-scans`
- `POST /deep-evals`
- `GET /deep-evals`
- `GET /analytics/strategic-ranking`
- `GET /analytics/hall-heat-map`
- `GET /analytics/hall/{hall}/exhibitors`
- `GET /analytics/follow-up-queue`
- `GET /analytics/export/walk.csv`
- `GET /analytics/export/deep.csv`
- `GET /analytics/export/combined_rankings.csv`
- `GET /analytics/export/all.json`
- `POST /ingest/graphql` (fail-loud on auth/rate wall)

## Ingestion behavior
- Uses persisted GraphQL query against the provided endpoint
- Polite delay between pages (`>= 0.4s`)
- Stops and returns explicit error on non-200 or GraphQL errors
