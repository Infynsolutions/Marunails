"""
Argos API — Main entry point.
FastAPI application with CORS, versioned API routes, and startup logging.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.routes import router as api_router


# ── Logging ──

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("argos")


# ── Lifespan ──

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("🟢 Argos API starting — env=%s", settings.environment)
    logger.info("  Supabase: %s", settings.supabase_url[:30] + "..." if settings.supabase_url else "NOT SET")
    logger.info("  Claude API: %s", "configured" if settings.anthropic_api_key else "NOT SET")
    logger.info("  Google Sheets: %s", "configured" if settings.google_service_account_json else "NOT SET")
    yield
    logger.info("🔴 Argos API shutting down")


# ── App ──

app = FastAPI(
    title="Argos API",
    description="Dashboard inteligente para PyMEs — Backend API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "https://infy-napp.vercel.app",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://infy-napp-.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)


@app.get("/")
async def root():
    return {
        "service": "argos-api",
        "version": "0.1.0",
        "docs": "/docs",
    }
