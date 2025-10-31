from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from utils.db import init_database
from routers import endpoints, policies, rules, assignments, detector_configs, audit_logs, export, auth
from routers import alerts
from routers import metrics
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

@app.get("/health")
def health():
    return {"status": "ok"}
