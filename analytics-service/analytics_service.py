# analytics-service/analytics_service.py
#!/usr/bin/env python3
import asyncio
import uvicorn
from fastapi import FastAPI

from core.consumer import start_consumer
from features import get_extractor
from utils.config import load_config
from utils.logger import log

app = FastAPI(title="Real-time Analytics Service")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    cfg = load_config()
    log.info("Starting analytics consumer in FastAPI event loop...")
    asyncio.create_task(start_consumer(cfg, get_extractor=get_extractor))

if __name__ == "__main__":
    cfg = load_config()
    # NO THREAD — let FastAPI manage the loop
    uvicorn.run(app, host="0.0.0.0", port=8000)