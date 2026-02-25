"""Sole entrypoint for APEX AI OS.

Run with: python main.py
Or via Docker CMD: python -m uvicorn app:app --host 0.0.0.0 --port 8000
"""
import os
import uvicorn
from app import app  # noqa: F401 - import ensures app is configured

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        workers=workers,
        log_level=log_level,
        reload=False,
    )
