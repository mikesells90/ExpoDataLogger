import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
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

APP_PASSWORD = os.getenv("APP_PASSWORD")


@app.middleware("http")
async def optional_password_guard(request, call_next):
    if not APP_PASSWORD:
        return await call_next(request)
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)
    provided = request.headers.get("x-app-password")
    if provided != APP_PASSWORD:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized: invalid app password"})
    return await call_next(request)


@app.get("/health")
def health():
    return {"status": "ok"}
