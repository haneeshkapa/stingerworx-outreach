from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base

class ActivityLog(Base):
    """
    Real-time activity log for tracking dealer discovery and enrichment progress
    """
    __tablename__ = 'activity_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, index=True)
    
    activity_type = Column(String(50), nullable=False, index=True)
    dealer_name = Column(String(255))
    message = Column(Text, nullable=False)
    status = Column(String(20), default='info')
    
    metadata = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ActivityLog {self.activity_type}: {self.dealer_name}>"
