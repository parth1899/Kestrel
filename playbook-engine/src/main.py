from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.playbooks import router as playbooks_router
from .api.executions import router as executions_router
from .utils.config import load_config
from .utils.logger import logger
from .messaging.consumer import start_consumer, ingest_file_once

# Fix asyncio subprocess on Windows
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# FastAPI app with background consumer startup.

app = FastAPI(title="Playbook Engine", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(playbooks_router, prefix="/api")
app.include_router(executions_router, prefix="/api")


@app.on_event("startup")
async def on_startup():
    cfg = load_config()
    # Start RabbitMQ consumer in background if enabled
    if cfg["messaging"].get("enabled", True):
        asyncio.create_task(start_consumer())
    # If a file_input path is provided, ingest it once in background
    file_input = (cfg["messaging"].get("file_input") or "").strip()
    if file_input:
        asyncio.create_task(ingest_file_once(file_input))
    logger.info("Playbook Engine started")


@app.get("/health")
async def health():
    return {"status": "ok"}
