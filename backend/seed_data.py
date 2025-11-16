from database import SessionLocal, Base, engine
from models import Tenant, Dealer, MessageTemplate, TenantStatus, DealerStatus
from datetime import datetime

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        existing_tenant = db.query(Tenant).filter(Tenant.company == "Stingerworx").first()
        if existing_tenant:
            print("Stingerworx tenant already exists")
            return
        
        stingerworx = Tenant(
            name="Craig",
            company="Stingerworx",
            email="craig@stingerworx.com",
            status=TenantStatus.ACTIVE,
            settings={
                "industry": "suppressors",
                "target_states": ["TX", "FL", "GA", "AZ", "NC"]
            }
        )
        db.add(stingerworx)
        db.flush()
        
        sample_dealers = [
            Dealer(
                tenant_id=stingerworx.id,
                business_name="Texas Tactical Firearms",
                state="TX",
                city="Austin",
                address="123 Main St",
                zip_code="78701",
                phone="512-555-0101",
                website="https://texastactical.example.com",
                ffl_number="FFL-TX-001",
                sot_class="Class 3",
                source="ATF Directory",
                status=DealerStatus.DISCOVERED
            ),
            Dealer(
                tenant_id=stingerworx.id,
                business_name="Sunshine State Arms",
                state="FL",
                city="Miami",
                address="456 Ocean Dr",
                zip_code="33139",
                phone="305-555-0202",
                website="https://sunshinearms.example.com",
                ffl_number="FFL-FL-002",
                sot_class="Class 3",
                source="Web Scraping",
                status=DealerStatus.ENRICHED
            ),
            Dealer(
                tenant_id=stingerworx.id,
                business_name="Georgia Gun Works",
                state="GA",
                city="Atlanta",
                address="789 Peachtree St",
                zip_code="30303",
                phone="404-555-0303",
                ffl_number="FFL-GA-003",
                sot_class="Class 3",
                source="Directory",
                status=DealerStatus.DISCOVERED
            ),
            Dealer(
                tenant_id=stingerworx.id,
                business_name="Desert Defense Solutions",
                state="AZ",
                city="Phoenix",
                address="321 Desert Rd",
                zip_code="85001",
                phone="602-555-0404",
                website="https://desertdefense.example.com",
                contact_form_url="https://desertdefense.example.com/contact",
                ffl_number="FFL-AZ-004",
                sot_class="Class 3",
                source="ATF Directory",
                status=DealerStatus.ENRICHED
            ),
            Dealer(
                tenant_id=stingerworx.id,
                business_name="Carolina Class 3",
                state="NC",
                city="Charlotte",
                address="555 Trade St",
                zip_code="28202",
                phone="704-555-0505",
                ffl_number="FFL-NC-005",
                sot_class="Class 3",
                source="Web Scraping",
                status=DealerStatus.DISCOVERED
            ),
        ]
        
        for dealer in sample_dealers:
            db.add(dealer)
        
        template = MessageTemplate(
            tenant_id=stingerworx.id,
            name="Initial Outreach - Suppressors",
            subject_template="Partnership Opportunity: Stingerworx Suppressors",
            body_template="""Hello {dealer_name},

I'm reaching out from Stingerworx, a leading suppressor manufacturer. We're looking to expand our dealer network in {state} and believe {business_name} would be an excellent partner.

Our suppressors offer:
- Industry-leading sound reduction
- Competitive dealer pricing
- Full compliance support and paperwork assistance
- Marketing materials and training

We'd love to discuss how we can help you grow your NFA business. Are you interested in learning more about carrying Stingerworx products?

Best regards,
Craig
Stingerworx""",
            is_active=True
        )
        db.add(template)
        
        db.commit()
        print("✅ Seeded Stingerworx tenant with sample dealers and message template")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
