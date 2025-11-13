from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.db import init_database
from utils.decision_engine import run_once
import os
import asyncio
import logging

logger = logging.getLogger("app")
from routers import endpoints, policies, rules, assignments, detector_configs, audit_logs, export, auth
from routers import alerts
from routers import metrics
from routers import decisions
from routers import users

app = FastAPI(title="Kestrel Management Plane", version="0.1.0")

# CORS (allow local dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup hook to ensure DB is initialized
@app.on_event("startup")
async def startup_event():
    init_database()
    # Run decision engine once at startup; for continuous operation, consider a scheduler
    try:
        run_once()
    except Exception:
        # avoid failing startup; errors can be logged if logger present
        pass
    # Schedule periodic decision engine if interval provided
    interval = int(os.getenv("DECISION_ENGINE_INTERVAL", "0") or 0)
    if interval > 0:
        async def _periodic():
            while True:
                try:
                    created = run_once()
                    if created:
                        logger.info(f"Periodic decision engine created {created} decisions")
                except Exception as e:
                    logger.warning(f"Decision engine error: {e}")
                await asyncio.sleep(interval)
        asyncio.create_task(_periodic())

# Routers
app.include_router(endpoints.router, prefix="/api/endpoints", tags=["endpoints"])
app.include_router(policies.router, prefix="/api/policies", tags=["policies"])
app.include_router(rules.router, prefix="/api/rules", tags=["rules"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(detector_configs.router, prefix="/api/detectors", tags=["detectors"])  
app.include_router(audit_logs.router, prefix="/api/audit", tags=["audit"])  
app.include_router(export.router, prefix="/api/export", tags=["export"])  
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])  
app.include_router(users.router, prefix="/api/users", tags=["users"])  
app.include_router(alerts.router)  
app.include_router(metrics.router)
app.include_router(decisions.router)

@app.get("/health")
def health():
    return {"status": "ok"}
