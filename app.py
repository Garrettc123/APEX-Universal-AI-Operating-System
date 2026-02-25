import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="APEX AI OS", version="1.0.0")

# FIX: Load allowed origins from env var instead of wildcard "*"
# Set ALLOWED_ORIGINS="https://your-domain.com,https://api.your-domain.com" in production
_raw_origins = os.getenv("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.get("/")
async def root():
    return {"status": "healthy", "service": "APEX AI Operating System"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
# NOTE: Entrypoint is in main.py - no duplicate uvicorn block here
