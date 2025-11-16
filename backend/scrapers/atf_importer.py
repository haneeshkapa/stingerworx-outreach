"""
ATF FFL List Importer - Updated to use real ATF Excel data

Imports Class 3 SOT dealers (SOT Type 2) from uploaded ATF dealer list.
"""

import pandas as pd
from sqlalchemy.orm import Session
from models import Dealer
from scrapers.activity_logger import ActivityLogger
import os

class ATFImporter:
    """Imports Class 3 SOT dealers from real ATF Excel data"""
    
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.logger = ActivityLogger(db, tenant_id)
        
        # Path to the uploaded ATF Excel file
        self.atf_file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            '..', 
            'attached_assets', 
            'atf_dealers_1763322022600.xlsx'
        )
    
    def import_dealers_from_state(self, state_code: str):
        """
        Import Class 3 SOT dealers from ATF list for a specific state.
        Filters for SOT Type 2 (Class 3 - Dealers with NFA/suppressor licenses).
        
        Returns: number of new dealers imported
        """
        self.logger.log('info', f'Starting import for {state_code}')
        
        try:
            # Read the Excel file
            df = pd.read_excel(self.atf_file_path)
            
            # Filter for Class 3 SOT (type 2) dealers in the specified state
            state_dealers = df[
                (df['state'] == state_code) & 
                (df['sot_type'] == 2)
            ]
            
            if len(state_dealers) == 0:
                self.logger.log('info', f'No Class 3 SOT dealers found in {state_code}')
                return 0
            
            self.logger.log('info', f'Found {len(state_dealers)} Class 3 SOT dealers from ATF list in {state_code}')
            
            imported_count = 0
            
            for _, row in state_dealers.iterrows():
                # Check if dealer already exists (by license number or business name)
                existing = self.db.query(Dealer).filter(
                    Dealer.tenant_id == self.tenant_id,
                    Dealer.business_name == row['business_name'],
                    Dealer.state == row['state']
                ).first()
                
                if existing:
                    continue
                
                # Clean phone number if exists
                phone = None
                if pd.notna(row['phone']):
                    phone = str(row['phone']).strip()
                
                # Create new dealer record
                dealer = Dealer(
                    tenant_id=self.tenant_id,
                    business_name=row['business_name'],
                    city=row['city'],
                    state=row['state'],
                    zip_code=str(row['zip_code']) if pd.notna(row['zip_code']) else None,
                    phone=phone,
                    email=str(row['email']) if pd.notna(row['email']) else None,
                    address=str(row['address']) if pd.notna(row['address']) else None,
                    status='DISCOVERED',
                    source='ATF FFL List (Class 3 SOT)',
                    extra_data={
                        'license_number': row['license_number'],
                        'contact_name': str(row['contact_name']) if pd.notna(row['contact_name']) else None,
                        'sot_type': int(row['sot_type']),
                        'dealer_type': str(row['dealer_type']) if pd.notna(row['dealer_type']) else None,
                    }
                )
                
                self.db.add(dealer)
                imported_count += 1
            
            self.db.commit()
            self.logger.log('info', f'Import complete for {state_code}: {imported_count} new Class 3 dealers added')
            
            return imported_count
            
        except Exception as e:
            self.logger.log('error', f'Error importing dealers from {state_code}: {str(e)}')
            raise
    
    def get_class3_stats(self):
        """Get statistics about Class 3 dealers in the ATF database"""
        try:
            df = pd.read_excel(self.atf_file_path)
            class_3 = df[df['sot_type'] == 2]
            
            return {
                'total_class3_dealers': len(class_3),
                'states_with_class3': class_3['state'].nunique(),
                'top_states': class_3['state'].value_counts().head(10).to_dict()
            }
        except Exception as e:
            return {'error': str(e)}
