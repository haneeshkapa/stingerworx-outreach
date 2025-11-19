from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database import get_db
from models import Dealer, MessageTemplate, OutreachAttempt, OutreachStatus, DealerStatus
from auth import get_current_tenant_id

router = APIRouter(
    prefix="/api/outreach",
    tags=["outreach"]
)

class OutreachCreate(BaseModel):
    dealer_id: int
    template_id: Optional[int] = None
    method: str = "contact_form"

class OutreachResponse(BaseModel):
    id: int
    dealer_id: int
    method: str
    subject: str | None
    status: str
    sent_at: datetime | None
    
    class Config:
        from_attributes = True

class MessageTemplateResponse(BaseModel):
    id: int
    name: str
    subject_template: Optional[str]
    body_template: str
    is_active: bool
    
    class Config:
        from_attributes = True

@router.get("", response_model=List[OutreachResponse])
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

@router.post("", response_model=OutreachResponse)
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
        # TODO: Fetch from tenant settings instead of hardcoding
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

@router.put("/{outreach_id}/approve")
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

@router.get("/templates", response_model=List[MessageTemplateResponse])
def get_templates(
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    templates = db.query(MessageTemplate).filter(
        MessageTemplate.tenant_id == tenant_id
    ).all()
    return templates
