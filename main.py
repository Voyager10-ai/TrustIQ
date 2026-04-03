"""
Exam-Cheater: AI Behavioral Integrity Engine (ABIE)
====================================================
Multi-modal AI system for detecting behavioral deviations during online exams.

Modules:
    - Vision Intelligence
    - Behavioral Biometrics
    - Acoustic Intelligence
    - Stylometric Analysis
    - Multi-Modal Fusion Engine

Usage:
    python main.py
"""

import uvicorn
import os
from backend.config import settings


def main():
    """Start the ABIE FastAPI server."""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   ABIE - AI Behavioral Integrity Engine          ║
    ║   Exam-Cheater Detection System v1.0             ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    # Railway (and other cloud hosts) inject PORT via environment variable
    # Fall back to settings.PORT (8000) for local development
    port = int(os.environ.get("PORT", settings.PORT))
    reload = settings.DEBUG and port == settings.PORT  # No reload in production

    uvicorn.run(
        "backend.app:app",
        host="0.0.0.0",
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
