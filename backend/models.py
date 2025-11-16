from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRIAL = "trial"

class DealerStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    ENRICHED = "enriched"
    CONTACTED = "contacted"
    RESPONDED = "responded"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"

class OutreachStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SENT = "sent"
    FAILED = "failed"
    RESPONDED = "responded"

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    status = Column(SQLEnum(TenantStatus), default=TenantStatus.TRIAL)
    settings = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    users = relationship("User", back_populates="tenant")
    dealers = relationship("Dealer", back_populates="tenant")
    templates = relationship("MessageTemplate", back_populates="tenant")
    outreach_attempts = relationship("OutreachAttempt", back_populates="tenant")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="users")

class Dealer(Base):
    __tablename__ = "dealers"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    business_name = Column(String, nullable=False)
    ffl_number = Column(String)
    sot_class = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String, index=True)
    zip_code = Column(String)
    phone = Column(String)
    website = Column(String)
    email = Column(String)
    contact_form_url = Column(String)
    source = Column(String)
    status = Column(SQLEnum(DealerStatus), default=DealerStatus.DISCOVERED, index=True)
    extra_data = Column(JSON, default={})
    last_contact_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    tenant = relationship("Tenant", back_populates="dealers")
    outreach_attempts = relationship("OutreachAttempt", back_populates="dealer")

class MessageTemplate(Base):
    __tablename__ = "message_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String, nullable=False)
    subject_template = Column(String)
    body_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="templates")

class OutreachAttempt(Base):
    __tablename__ = "outreach_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("message_templates.id"))
    method = Column(String)
    subject = Column(String)
    message = Column(Text)
    status = Column(SQLEnum(OutreachStatus), default=OutreachStatus.PENDING, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"))
    sent_at = Column(DateTime(timezone=True))
    response_received_at = Column(DateTime(timezone=True))
    response_text = Column(Text)
    extra_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="outreach_attempts")
    dealer = relationship("Dealer", back_populates="outreach_attempts")
