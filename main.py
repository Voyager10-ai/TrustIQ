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
from backend.config import settings


def main():
    """Start the ABIE FastAPI server."""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║   ABIE - AI Behavioral Integrity Engine          ║
    ║   Exam-Cheater Detection System v1.0             ║
    ╚══════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
