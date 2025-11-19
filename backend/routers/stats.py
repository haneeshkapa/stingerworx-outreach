from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import os
from pydantic import BaseModel
from datetime import datetime

from database import get_db
from models import Dealer, OutreachAttempt, ActivityLog, DealerStatus, OutreachStatus
from auth import get_current_tenant_id

router = APIRouter(
    tags=["stats"]
)

class StatsResponse(BaseModel):
    total_dealers: int
    contacted_dealers: int
    interested_leads: int
    pending_approvals: int
    class3_verified: int
    discovered_count: int
    enriched_count: int
    state_breakdown: dict

@router.get("/api/activity")
def get_activity_logs(
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """Get recent activity logs for real-time progress tracking"""
    logs = db.query(ActivityLog).filter(
        ActivityLog.tenant_id == tenant_id
    ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    return [{
        "id": log.id,
        "activity_type": log.activity_type,
        "dealer_name": log.dealer_name,
        "message": log.message,
        "details": log.details,
        "created_at": log.created_at
    } for log in logs]

@router.get("/api/stats", response_model=StatsResponse)
def get_stats(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    total_dealers = db.query(Dealer).filter(Dealer.tenant_id == tenant_id).count()
    contacted = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id,
        Dealer.status.in_([DealerStatus.CONTACTED, DealerStatus.RESPONDED, DealerStatus.INTERESTED])
    ).count()
    interested = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id,
        Dealer.status == DealerStatus.INTERESTED
    ).count()
    pending = db.query(OutreachAttempt).filter(
        OutreachAttempt.tenant_id == tenant_id,
        OutreachAttempt.status == OutreachStatus.PENDING
    ).count()
    
    # Count Class 3 SOT dealers
    class3_verified = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id,
        Dealer.sot_class == "Class 3 SOT"
    ).count()
    
    # Count discovered and enriched dealers
    discovered_count = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id,
        Dealer.status == DealerStatus.DISCOVERED
    ).count()
    
    enriched_count = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id,
        Dealer.status == DealerStatus.ENRICHED
    ).count()
    
    # Get state breakdown
    state_counts = db.query(
        Dealer.state,
        func.count(Dealer.id).label('count')
    ).filter(
        Dealer.tenant_id == tenant_id
    ).group_by(Dealer.state).all()
    
    state_breakdown = {state: count for state, count in state_counts}
    
    return {
        "total_dealers": total_dealers,
        "contacted_dealers": contacted,
        "interested_leads": interested,
        "pending_approvals": pending,
        "class3_verified": class3_verified,
        "discovered_count": discovered_count,
        "enriched_count": enriched_count,
        "state_breakdown": state_breakdown
    }

@router.get("/api/logs")
def get_workflow_logs(lines: int = 500):
    """
    Get the latest backend workflow logs for real-time monitoring
    """
    import glob
    
    # Find the latest backend log file
    log_files = glob.glob('/tmp/logs/backend_*.log')
    if not log_files:
        return {"logs": "No logs available yet"}
    
    # Get the most recent log file
    latest_log = max(log_files, key=os.path.getmtime)
    
    try:
        with open(latest_log, 'r') as f:
            # Read all lines and get the last N lines
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
            log_content = ''.join(recent_lines)
        
        return {
            "logs": log_content,
            "file": latest_log,
            "total_lines": len(all_lines),
            "showing_lines": len(recent_lines)
        }
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}
