from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import asyncio
import base64
from datetime import datetime
from pydantic import BaseModel

from database import engine, get_db, Base
from models import Tenant, User
from auth import get_current_tenant_id

# Import routers
from routers import dealers, outreach, stats, webrtc
from webrtc_streaming import stream_manager

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dealer Outreach System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=False,  # no cookies needed; allows wildcard origin in preflight
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dealers.router)
app.include_router(outreach.router)
app.include_router(stats.router)
app.include_router(webrtc.router)

class TenantCreate(BaseModel):
    name: str
    company: str
    email: str

@app.get("/")
def root():
    return {"message": "Dealer Outreach System API", "version": "1.0.0"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/tenants", response_model=dict)
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    db_tenant = Tenant(
        name=tenant.name,
        company=tenant.company,
        email=tenant.email
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return {"id": db_tenant.id, "name": db_tenant.name, "company": db_tenant.company}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup all WebRTC sessions on shutdown"""
    await stream_manager.close_all()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
