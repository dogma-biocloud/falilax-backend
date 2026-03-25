from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.services.simulation_runtime import should_run_simulation, simulation_loop

# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FalilaX API",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router, prefix="/api/v1")


# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    log.info("Starting FalilaX API")

    if ENV_PATH.exists():
        log.info(f"Loaded environment variables from {ENV_PATH}")
    else:
        log.warning(f".env file not found at {ENV_PATH}")

    if should_run_simulation():
        log.info("FalilaX demo mode enabled: starting simulation loop")
        asyncio.create_task(simulation_loop())
    else:
        log.info("Simulation loop not started")