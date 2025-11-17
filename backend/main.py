from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database import engine, get_db, Base
from models import Tenant, User, Dealer, MessageTemplate, OutreachAttempt, DealerStatus, OutreachStatus, ActivityLog, ActivityType
from auth import get_current_tenant_id
from pydantic import BaseModel
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dealer Outreach System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TenantCreate(BaseModel):
    name: str
    company: str
    email: str

class DealerResponse(BaseModel):
    id: int
    business_name: str
    state: str
    city: str
    phone: str | None
    website: str | None
    email: str | None
    contact_form_url: str | None
    sot_class: str | None
    status: str
    extra_data: dict | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class OutreachResponse(BaseModel):
    id: int
    dealer_id: int
    method: str
    subject: str | None
    status: str
    sent_at: datetime | None
    
    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_dealers: int
    contacted_dealers: int
    interested_leads: int
    pending_approvals: int
    class3_verified: int
    discovered_count: int
    enriched_count: int
    state_breakdown: dict

class DealerCreate(BaseModel):
    business_name: str
    ffl_number: Optional[str] = None
    sot_class: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: str
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    source: str = "Manual"

class OutreachCreate(BaseModel):
    dealer_id: int
    template_id: Optional[int] = None
    method: str = "contact_form"
    
class MessageTemplateResponse(BaseModel):
    id: int
    name: str
    subject_template: Optional[str]
    body_template: str
    is_active: bool
    
    class Config:
        from_attributes = True

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

@app.get("/api/dealers", response_model=List[DealerResponse])
def get_dealers(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    dealers = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id
    ).offset(skip).limit(limit).all()
    return dealers

@app.post("/api/dealers", response_model=DealerResponse)
def create_dealer(
    dealer: DealerCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    db_dealer = Dealer(
        tenant_id=tenant_id,
        **dealer.model_dump()
    )
    db.add(db_dealer)
    db.commit()
    db.refresh(db_dealer)
    return db_dealer

@app.post("/api/dealers/import/{state}")
def import_dealers_from_state(
    state: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """Import dealers from ATF list for a specific state"""
    from scrapers.atf_importer import ATFImporter
    from scrapers.contact_enricher import ContactEnricher
    
    def import_task():
        from scrapers.activity_logger import ActivityLogger
        importer = ATFImporter(db, tenant_id)
        enricher = ContactEnricher(db, tenant_id)
        activity = ActivityLogger(db, tenant_id)
        
        # Import dealers from ATF list
        num_imported = importer.import_dealers_from_state(state)
        
        if num_imported == 0:
            activity.log('info', f'No dealers to enrich in {state}')
            return
        
        # Get the newly imported dealers that need enrichment
        new_dealers = db.query(Dealer).filter(
            Dealer.tenant_id == tenant_id,
            Dealer.state == state,
            Dealer.status == DealerStatus.DISCOVERED
        ).limit(min(num_imported, 5)).all()  # Limit to 5 for testing
        
        activity.log('info', f'Enriching {len(new_dealers)} dealers from {state}')
        
        # Enrich each dealer with AI (website, contact info, Class 3 verification)
        for dealer in new_dealers:
            activity.log('dealer_search', f'Enriching {dealer.business_name}', dealer_name=dealer.business_name)
            
            dealer_dict = {
                'business_name': dealer.business_name,
                'city': dealer.city,
                'state': dealer.state
            }
            
            # Enrich with AI (includes Class 3 verification)
            enriched = enricher.enrich_dealer(dealer_dict, verify_class3=True)
            
            # Update dealer with enriched data
            if enriched.get('website'):
                dealer.website = enriched['website']
                dealer.status = DealerStatus.ENRICHED
            
            if enriched.get('email'):
                dealer.email = enriched['email']
            
            if enriched.get('phone'):
                dealer.phone = enriched['phone']
            
            if enriched.get('contact_form_url'):
                dealer.contact_form_url = enriched['contact_form_url']
            
            # Store Class 3 verification results
            if enriched.get('class3_verified') is not None:
                dealer.sot_class = 'Class 3 SOT' if enriched['class3_verified'] else 'No Class 3'
                # SQLAlchemy doesn't detect in-place JSON mutations, so reassign the whole dict
                dealer.extra_data = {
                    **(dealer.extra_data or {}),
                    'class3_confidence': enriched.get('class3_confidence', 0.0),
                    'class3_evidence': enriched.get('class3_evidence', ''),
                    'class3_verified_at': datetime.now().isoformat()
                }
        
        db.commit()
        activity.log('info', f"Import and enrichment complete for {state}")
    
    background_tasks.add_task(import_task)
    
    return {"message": f"Import started for {state}", "state": state}

@app.post("/api/dealers/re-enrich")
def re_enrich_all_dealers(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """Re-enrich all dealers with updated AI (fixes Wikipedia bug, etc.)"""
    from scrapers.contact_enricher import ContactEnricher
    
    def re_enrich_task():
        from scrapers.activity_logger import ActivityLogger
        enricher = ContactEnricher(db, tenant_id)
        activity = ActivityLogger(db, tenant_id)
        
        # Get all dealers that have been enriched
        dealers = db.query(Dealer).filter(
            Dealer.tenant_id == tenant_id,
            Dealer.status.in_([DealerStatus.ENRICHED, DealerStatus.DISCOVERED])
        ).all()
        
        activity.log('info', f'Re-enriching {len(dealers)} dealers with fixed AI')
        
        # Re-enrich each dealer
        for dealer in dealers:
            activity.log('dealer_search', f'Re-enriching {dealer.business_name}', dealer_name=dealer.business_name)
            
            dealer_dict = {
                'business_name': dealer.business_name,
                'city': dealer.city,
                'state': dealer.state
            }
            
            # Enrich with AI (includes Class 3 verification)
            enriched = enricher.enrich_dealer(dealer_dict, verify_class3=True)
            
            # Update dealer with enriched data
            if enriched.get('website'):
                dealer.website = enriched['website']
                dealer.status = DealerStatus.ENRICHED
            
            if enriched.get('email'):
                dealer.email = enriched['email']
            
            if enriched.get('phone'):
                dealer.phone = enriched['phone']
            
            if enriched.get('contact_form_url'):
                dealer.contact_form_url = enriched['contact_form_url']
            
            # Store Class 3 verification results
            if enriched.get('class3_verified') is not None:
                dealer.sot_class = 'Class 3 SOT' if enriched['class3_verified'] else 'No Class 3'
                # SQLAlchemy doesn't detect in-place JSON mutations, so reassign the whole dict
                dealer.extra_data = {
                    **(dealer.extra_data or {}),
                    'class3_confidence': enriched.get('class3_confidence', 0.0),
                    'class3_evidence': enriched.get('class3_evidence', ''),
                    'class3_verified_at': datetime.now().isoformat()
                }
            
            # Commit after each dealer to avoid losing progress
            db.commit()
        
        activity.log('info', f"Re-enrichment complete for {len(dealers)} dealers")
    
    background_tasks.add_task(re_enrich_task)
    
    return {"message": "Re-enrichment started for all dealers"}

@app.get("/api/outreach", response_model=List[OutreachResponse])
def get_outreach_attempts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    attempts = db.query(OutreachAttempt).filter(
        OutreachAttempt.tenant_id == tenant_id
    ).offset(skip).limit(limit).all()
    return attempts

@app.post("/api/outreach", response_model=OutreachResponse)
def create_outreach(
    outreach: OutreachCreate,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """Create a new outreach attempt"""
    dealer = db.query(Dealer).filter(
        Dealer.id == outreach.dealer_id,
        Dealer.tenant_id == tenant_id
    ).first()
    
    if not dealer:
        raise HTTPException(status_code=404, detail="Dealer not found")
    
    template = None
    if outreach.template_id:
        template = db.query(MessageTemplate).filter(
            MessageTemplate.id == outreach.template_id,
            MessageTemplate.tenant_id == tenant_id
        ).first()
    else:
        template = db.query(MessageTemplate).filter(
            MessageTemplate.tenant_id == tenant_id,
            MessageTemplate.is_active == True
        ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="No message template found")
    
    from services.message_generator import MessageGenerator
    generator = MessageGenerator()
    
    message_data = generator.generate_personalized_message(
        dealer={
            'business_name': dealer.business_name,
            'city': dealer.city,
            'state': dealer.state
        },
        template={
            'subject_template': template.subject_template,
            'body_template': template.body_template
        },
        company_info={'company_name': 'Stingerworx'}
    )
    
    db_outreach = OutreachAttempt(
        tenant_id=tenant_id,
        dealer_id=outreach.dealer_id,
        template_id=template.id,
        method=outreach.method,
        subject=message_data['subject'],
        message=message_data['message'],
        status=OutreachStatus.PENDING
    )
    
    db.add(db_outreach)
    db.commit()
    db.refresh(db_outreach)
    
    return db_outreach

@app.put("/api/outreach/{outreach_id}/approve")
def approve_outreach(
    outreach_id: int,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """Approve and send an outreach message"""
    outreach = db.query(OutreachAttempt).filter(
        OutreachAttempt.id == outreach_id,
        OutreachAttempt.tenant_id == tenant_id
    ).first()
    
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach not found")
    
    outreach.status = OutreachStatus.APPROVED
    outreach.sent_at = datetime.now()
    
    dealer = db.query(Dealer).filter(Dealer.id == outreach.dealer_id).first()
    if dealer:
        dealer.status = DealerStatus.CONTACTED
        dealer.last_contact_date = datetime.now()
    
    db.commit()
    
    return {"message": "Outreach approved and sent", "id": outreach_id}

@app.get("/api/activity")
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

@app.get("/api/stats", response_model=StatsResponse)
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
    from sqlalchemy import func
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

@app.get("/api/templates", response_model=List[MessageTemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    templates = db.query(MessageTemplate).filter(
        MessageTemplate.tenant_id == tenant_id
    ).all()
    return templates

@app.get("/api/logs")
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

@app.post("/api/demo-browser")
def demo_visible_browser(
    dealer_name: str = "5 SHOT FIREARMS",
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Run browser automation in VISIBLE mode (non-headless) for demonstration.
    Open VNC viewer to watch it live!
    """
    from scrapers.crawl4ai_search import run_async_search
    import threading
    
    # Find the dealer in the database
    dealer = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id,
        Dealer.business_name.ilike(f"%{dealer_name}%")
    ).first()
    
    if not dealer:
        return {"error": f"Dealer '{dealer_name}' not found"}
    
    # Run browser automation in background thread so API responds immediately
    def run_browser_demo():
        try:
            print(f"\n🎬 Starting visible browser demo for {dealer.business_name}...")
            result = run_async_search(
                dealer.business_name,
                dealer.city,
                dealer.state,
                headless=False  # VISIBLE BROWSER!
            )
            print(f"✅ Browser demo completed! Found: {result.get('url') if result else 'Nothing'}")
        except Exception as e:
            print(f"❌ Browser demo error: {str(e)}")
    
    # Start background thread
    thread = threading.Thread(target=run_browser_demo, daemon=True)
    thread.start()
    
    return {
        "message": f"🎬 Browser demo started for {dealer.business_name}!",
        "dealer": dealer.business_name,
        "status": "running",
        "note": "The VNC viewer should appear automatically in your Replit workspace. Watch the browser navigate in real-time! Check the Logs page to see progress."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
