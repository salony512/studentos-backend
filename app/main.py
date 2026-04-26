from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import init_db
from app.api import auth, academics, health, skills, mindfulness, insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create all tables."""
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for StudentOS — your AI-powered college life system",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list + ["*"],   # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(academics.router)
app.include_router(health.router)
app.include_router(skills.router)
app.include_router(mindfulness.router)
app.include_router(insights.router)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "message": "Rise above mediocrity. One API call at a time.",
    }


@app.get("/health")
async def health_check():
    return {"status": "ok"}
