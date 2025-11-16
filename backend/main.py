from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from database import engine, get_db, Base
from models import Tenant, User, Dealer, MessageTemplate, OutreachAttempt, DealerStatus, OutreachStatus
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
    status: str
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
        importer = ATFImporter()
        enricher = ContactEnricher()
        
        dealers = importer.import_from_state(state)
        
        for dealer_data in dealers:
            enriched = enricher.enrich_dealer(dealer_data)
            
            existing = db.query(Dealer).filter(
                Dealer.tenant_id == tenant_id,
                Dealer.ffl_number == enriched.get('ffl_number')
            ).first()
            
            if not existing:
                db_dealer = Dealer(
                    tenant_id=tenant_id,
                    business_name=enriched['business_name'],
                    ffl_number=enriched.get('ffl_number'),
                    sot_class=enriched.get('license_type', 'Class 3'),
                    address=enriched.get('address'),
                    city=enriched.get('city'),
                    state=enriched.get('state'),
                    zip_code=enriched.get('zip_code'),
                    phone=enriched.get('phone'),
                    website=enriched.get('website'),
                    email=enriched.get('email'),
                    contact_form_url=enriched.get('contact_form_url'),
                    source=enriched.get('source', 'ATF Directory'),
                    status=DealerStatus.ENRICHED if enriched.get('website') else DealerStatus.DISCOVERED
                )
                db.add(db_dealer)
        
        db.commit()
    
    background_tasks.add_task(import_task)
    
    return {"message": f"Import started for {state}", "state": state}

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
    
    return {
        "total_dealers": total_dealers,
        "contacted_dealers": contacted,
        "interested_leads": interested,
        "pending_approvals": pending
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
