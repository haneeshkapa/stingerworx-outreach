from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from database import get_db
from models import Dealer, DealerStatus
from auth import get_current_tenant_id

router = APIRouter(
    prefix="/api/dealers",
    tags=["dealers"]
)

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

@router.get("", response_model=List[DealerResponse])
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

@router.post("", response_model=DealerResponse)
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

@router.post("/import/{state}")
def import_dealers_from_state(
    state: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """Import dealers from ATF list for a specific state"""
    from scrapers.atf_importer import ATFImporter
    from scrapers.contact_enricher import ContactEnricher
    
    # Create a new session for the background task to avoid "Session is closed" errors
    # Note: In a real production app, we'd use a proper worker queue (Celery/Redis)
    # For now, we'll just pass the parameters and let the task create its own session if needed
    # But since the current implementation expects a session, we'll stick to the existing pattern
    # knowing it's a limitation we identified in the review.
    
    def import_task():
        from scrapers.activity_logger import ActivityLogger
        
        # Create new DB session for background task
        # This prevents "Session is closed" errors since the request session closes
        from database import SessionLocal
        db_session = SessionLocal()
        
        try:
            importer = ATFImporter(db_session, tenant_id)
            enricher = ContactEnricher(db_session, tenant_id)
            activity = ActivityLogger(db_session, tenant_id)
            
            activity.log('info', f'Starting import for {state}')
            
            # Import dealers from ATF list
            try:
                num_imported = importer.import_dealers_from_state(state)
            except Exception as e:
                activity.log('error', f'Failed to import ATF data for {state}: {str(e)}')
                return
            
            if num_imported == 0:
                activity.log('info', f'No new dealers found in {state}')
                return
            
            # Get the newly imported dealers that need enrichment
            new_dealers = db_session.query(Dealer).filter(
                Dealer.tenant_id == tenant_id,
                Dealer.state == state,
                Dealer.status == DealerStatus.DISCOVERED
            ).limit(min(num_imported, 5)).all()  # Limit to 5 for testing
            
            activity.log('info', f'Enriching {len(new_dealers)} dealers from {state}')
            
            # Enrich each dealer with AI (website, contact info, Class 3 verification)
            success_count = 0
            for i, dealer in enumerate(new_dealers):
                try:
                    activity.log('dealer_search', f'Enriching {dealer.business_name} ({i+1}/{len(new_dealers)})', dealer_name=dealer.business_name)
                    
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
                            'class3_verified_at': datetime.now().isoformat(),
                            'contact_pages': enriched.get('contact_pages', []),
                            'preferred_contact_method': enriched.get('preferred_contact_method', 'none')
                        }
                    
                    success_count += 1
                    db_session.commit()
                    
                except Exception as e:
                    activity.log('error', f'Error enriching {dealer.business_name}: {str(e)}')
                    # Continue to next dealer even if one fails
                    continue
            
            activity.log('info', f"Import complete for {state}. Enriched {success_count}/{len(new_dealers)} dealers.")
            
        except Exception as e:
            # Catch-all for any other crashes
            print(f"Critical background task error: {e}")
            # Try to log to DB if possible
            try:
                activity = ActivityLogger(db_session, tenant_id)
                activity.log('error', f'Critical import error: {str(e)}')
            except:
                pass
        finally:
            db_session.close()
    
    background_tasks.add_task(import_task)
    
    return {"message": f"Import started for {state}", "state": state}

@router.post("/re-enrich")
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
                    'class3_verified_at': datetime.now().isoformat(),
                    'contact_pages': enriched.get('contact_pages', []),
                    'preferred_contact_method': enriched.get('preferred_contact_method', 'none')
                }
            
            # Commit after each dealer to avoid losing progress
            db.commit()
        
        activity.log('info', f"Re-enrichment complete for {len(dealers)} dealers")
    
    background_tasks.add_task(re_enrich_task)
    
    return {"message": "Re-enrichment started for all dealers"}
