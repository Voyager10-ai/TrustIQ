"""
ABIE FastAPI Application
Main application setup with all routes and middleware.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.config import settings
from backend.database import database
from backend.routes import calibration, monitoring, risk, websocket

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    # Startup
    logger.info("Starting ABIE - AI Behavioral Integrity Engine")
    await database.connect()
    logger.info("All systems initialized.")
    yield
    # Shutdown
    logger.info("Shutting down ABIE...")
    await database.disconnect()


app = FastAPI(
    title="ABIE - AI Behavioral Integrity Engine",
    description=(
        "Multi-modal AI system for detecting behavioral deviations during online exams. "
        "Combines Vision, Behavioral Biometrics, Acoustic Intelligence, Stylometric Analysis, "
        "and Multi-Modal Fusion for comprehensive anomaly detection."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React frontend (localhost dev + Vercel production)
import os
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(calibration.router, prefix="/api")
app.include_router(monitoring.router, prefix="/api")
app.include_router(risk.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "ABIE - AI Behavioral Integrity Engine",
        "version": "1.0.0",
        "status": "running",
        "modules": [
            "Vision Intelligence",
            "Behavioral Biometrics",
            "Acoustic Intelligence",
            "Stylometric Analysis",
            "Multi-Modal Fusion Engine"
        ]
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected" if database.is_connected else "disconnected (in-memory mode)",
        "modules_loaded": True
    }
