from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import analytics, deep, ingest, walk

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expo Intelligence API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(walk.router)
app.include_router(deep.router)
app.include_router(ingest.router)
app.include_router(analytics.router)


@app.get("/health")
def health():
    return {"status": "ok"}

