"""
Activity Logger for tracking dealer discovery and enrichment progress
"""
import logging
from sqlalchemy.orm import Session
from models import ActivityLog, ActivityType

logger = logging.getLogger(__name__)

class ActivityLogger:
    """Logs activities to database for real-time tracking"""
    
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
    
    def log(self, activity_type: ActivityType, message: str, dealer_name: str = None, details: dict = None):
        """Log an activity to the database"""
        try:
            activity = ActivityLog(
                tenant_id=self.tenant_id,
                activity_type=activity_type,
                dealer_name=dealer_name,
                message=message,
                details=details or {}
            )
            self.db.add(activity)
            self.db.commit()
            logger.info(f"[{dealer_name or 'SYSTEM'}] {message}")
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            self.db.rollback()
    
    def dealer_search(self, dealer_name: str, city: str, state: str):
        self.log(
            ActivityType.DEALER_SEARCH,
            f"🔍 Searching for {dealer_name} in {city}, {state}",
            dealer_name=dealer_name
        )
    
    def website_found(self, dealer_name: str, website: str):
        self.log(
            ActivityType.WEBSITE_FOUND,
            f"✅ Found website: {website}",
            dealer_name=dealer_name,
            details={"website": website}
        )
    
    def contact_extracted(self, dealer_name: str, contact_info: dict):
        details_str = []
        if contact_info.get('email'):
            details_str.append(f"email: {contact_info['email']}")
        if contact_info.get('phone'):
            details_str.append(f"phone: {contact_info['phone']}")
        if contact_info.get('contact_form_url'):
            details_str.append("contact form found")
        
        message = f"📧 Extracted: {', '.join(details_str)}" if details_str else "No contact info found"
        
        self.log(
            ActivityType.CONTACT_EXTRACTED,
            message,
            dealer_name=dealer_name,
            details=contact_info
        )
    
    def dealer_saved(self, dealer_name: str):
        self.log(
            ActivityType.DEALER_SAVED,
            f"💾 Saved to database",
            dealer_name=dealer_name
        )
    
    def error(self, dealer_name: str, error_message: str):
        self.log(
            ActivityType.ERROR,
            f"❌ Error: {error_message}",
            dealer_name=dealer_name
        )
    
    def info(self, message: str, dealer_name: str = None):
        self.log(
            ActivityType.INFO,
            f"ℹ️ {message}",
            dealer_name=dealer_name
        )
