"""
ATF FFL List Importer

Downloads and parses monthly FFL lists from ATF to discover Class 3 SOT dealers.
ATF publishes updated lists at: https://www.atf.gov/firearms/listing-federal-firearms-licensees
"""

import csv
import httpx
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ATFImporter:
    """Imports and parses ATF FFL listings to find Class 3 dealers"""
    
    ATF_BASE_URL = "https://www.atf.gov/firearms/listing-federal-firearms-licensees"
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0)
    
    def parse_ffl_csv(self, csv_content: str) -> List[Dict]:
        """
        Parse ATF FFL CSV data
        
        Expected columns: License Number, Business Name, Premises Street, Premises City, 
                         Premises State, Premises Zip Code, License Expiration Date
        """
        dealers = []
        reader = csv.DictReader(csv_content.splitlines())
        
        for row in reader:
            license_type = row.get('License Type', '')
            
            if self._is_class3_eligible(license_type):
                dealer = {
                    'ffl_number': row.get('License Number', '').strip(),
                    'business_name': row.get('Business Name', '').strip(),
                    'address': row.get('Premises Street', '').strip(),
                    'city': row.get('Premises City', '').strip(),
                    'state': row.get('Premises State', '').strip(),
                    'zip_code': row.get('Premises Zip Code', '').strip(),
                    'license_type': license_type,
                    'source': 'ATF Directory'
                }
                dealers.append(dealer)
        
        return dealers
    
    def _is_class3_eligible(self, license_type: str) -> bool:
        """
        Check if FFL type is eligible for Class 3 SOT
        
        Type 01 (Dealer) and Type 07 (Manufacturer) can get Class 3 SOT.
        We can't tell from basic FFL list if they have SOT, but these are candidates.
        """
        eligible_types = ['01', '07', 'Type 01', 'Type 07', 'Dealer', 'Manufacturer']
        return any(t in license_type for t in eligible_types)
    
    def import_from_state(self, state_code: str) -> List[Dict]:
        """
        Import FFLs from a specific state
        
        Note: In production, this would download actual ATF CSV files.
        For MVP, we'll return sample data structure.
        """
        logger.info(f"Importing ATF FFLs for state: {state_code}")
        
        sample_csv = f"""License Number,Business Name,License Type,Premises Street,Premises City,Premises State,Premises Zip Code
1-12-345-67-8A-12345,"{state_code} Tactical Arms",01 - Dealer in Firearms,"123 Main St","{state_code} City",{state_code},12345
1-12-345-67-8B-12346,"{state_code} Gun Works",07 - Manufacturer of Firearms,"456 Oak Ave","{state_code} Town",{state_code},12346"""
        
        dealers = self.parse_ffl_csv(sample_csv)
        logger.info(f"Found {len(dealers)} eligible FFLs in {state_code}")
        
        return dealers
    
    def import_all_states(self) -> Dict[str, List[Dict]]:
        """Import FFLs from all states"""
        states = [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]
        results = {}
        
        for state in states:
            results[state] = self.import_from_state(state)
        
        return results
    
    def get_all_states(self) -> List[str]:
        """Get list of all 50 US states"""
        return [
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
        ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    importer = ATFImporter()
    
    dealers = importer.import_from_state('TX')
    print(f"Imported {len(dealers)} dealers from Texas")
    for dealer in dealers:
        print(f"  - {dealer['business_name']} ({dealer['ffl_number']})")
