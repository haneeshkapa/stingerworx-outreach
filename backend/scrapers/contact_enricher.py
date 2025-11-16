"""
Contact Enrichment Service

Finds website, email, and contact form info for dealers using web search and scraping.
"""

import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ContactEnricher:
    """Enriches dealer records with website and contact information"""
    
    def __init__(self):
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
    
    def find_website(self, business_name: str, city: str, state: str) -> Optional[str]:
        """
        Find dealer website using search
        
        In production, this would use Google/Bing API or web scraping.
        For MVP, we'll simulate the search.
        """
        logger.info(f"Searching for website: {business_name}, {city}, {state}")
        
        search_query = f"{business_name} {city} {state} gun dealer"
        
        normalized_name = business_name.lower().replace(' ', '')
        if 'tactical' in normalized_name or 'arms' in normalized_name:
            return f"https://www.{normalized_name.replace(' ', '')}.com"
        
        return None
    
    def extract_contact_info(self, url: str) -> Dict:
        """
        Extract contact information from dealer website
        
        Looks for:
        - Email addresses
        - Phone numbers  
        - Contact form URL
        """
        contact_info = {
            'email': None,
            'phone': None,
            'contact_form_url': None
        }
        
        try:
            response = self.client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code != 200:
                return contact_info
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            text = soup.get_text()
            
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            if emails:
                contact_info['email'] = emails[0]
            
            phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', text)
            if phones:
                contact_info['phone'] = phones[0]
            
            contact_links = soup.find_all('a', href=True)
            for link in contact_links:
                href = link.get('href', '').lower()
                link_text = link.get_text().lower()
                
                if 'contact' in href or 'contact' in link_text:
                    contact_url = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                    contact_info['contact_form_url'] = contact_url
                    break
            
            logger.info(f"Extracted contact info from {url}: {contact_info}")
            
        except Exception as e:
            logger.error(f"Error extracting contact info from {url}: {e}")
        
        return contact_info
    
    def enrich_dealer(self, dealer: Dict) -> Dict:
        """
        Enrich a dealer record with website and contact information
        """
        enriched = dealer.copy()
        
        if not enriched.get('website'):
            website = self.find_website(
                dealer['business_name'],
                dealer.get('city', ''),
                dealer.get('state', '')
            )
            if website:
                enriched['website'] = website
        
        if enriched.get('website'):
            contact_info = self.extract_contact_info(enriched['website'])
            enriched.update(contact_info)
        
        return enriched


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    enricher = ContactEnricher()
    
    test_dealer = {
        'business_name': 'Texas Tactical Arms',
        'city': 'Austin',
        'state': 'TX'
    }
    
    enriched = enricher.enrich_dealer(test_dealer)
    print(f"Enriched dealer: {enriched}")
