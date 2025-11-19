"""
Contact Enrichment Service

Finds website, email, and contact form info for dealers using AI-powered web search.
"""

import httpx
from bs4 import BeautifulSoup
import re
from typing import Dict, Optional
import logging
from scrapers.ai_browser_agent import AIBrowserAgent
from scrapers.class3_verifier import Class3Verifier
from scrapers.contact_page_detector import ContactPageDetector
from scrapers.crawl4ai_search import run_async_search
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ContactEnricher:
    """Enriches dealer records with website and contact information using Crawl4AI"""
    
    def __init__(self, db: Session = None, tenant_id: int = None):
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)
        self.ai_agent = AIBrowserAgent()  # Keep for legacy support
        self.class3_verifier = Class3Verifier(db, tenant_id) if db and tenant_id else None
        self.contact_page_detector = ContactPageDetector(db, tenant_id) if db and tenant_id else None
        self.use_crawl4ai = True  # Use Crawl4AI with Chromium browser automation
    
    def find_website(self, business_name: str, city: str, state: str) -> Optional[str]:
        """
        Find dealer website using DuckDuckGo search (no API key required)
        
        This does a real web search to find the dealer's actual website.
        """
        logger.info(f"Searching for website: {business_name}, {city}, {state}")
        
        try:
            search_query = f"{business_name} {city} {state} gun shop firearms dealer"
            search_url = f"https://html.duckduckgo.com/html/?q={search_query.replace(' ', '+')}"
            
            response = self.client.get(search_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                results = soup.find_all('a', class_='result__a')
                for result in results[:3]:
                    href = result.get('href', '')
                    if href and not any(skip in href.lower() for skip in ['facebook', 'yelp', 'yellowpages', 'google', 'duckduckgo']):
                        if 'http' in href:
                            logger.info(f"Found website: {href}")
                            return href
            
            logger.info(f"No website found for {business_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for website: {e}")
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
    
    def enrich_dealer(self, dealer: Dict, verify_class3: bool = True) -> Dict:
        """
        Enrich a dealer record with website and contact information using Crawl4AI.
        Optionally verify Class 3 SOT status.
        """
        enriched = dealer.copy()
        
        logger.info(f"Enriching dealer with Crawl4AI: {dealer['business_name']}")
        
        # Find website and contact info using Crawl4AI (browser automation)
        if self.use_crawl4ai:
            search_result = run_async_search(
                dealer['business_name'],
                dealer.get('city', ''),
                dealer.get('state', '')
            )
            
            if search_result:
                markdown = search_result.get('markdown', '')
                
                # Extract contact info from markdown using regex
                contact_data = {
                    'website': search_result.get('url'),
                    'email': None,
                    'phone': None,
                    'address': None,
                    'contact_form_url': None,
                    'html_snippet': markdown[:1000]  # For Class 3 verification
                }
                
                # Extract email
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', markdown)
                if emails:
                    # Filter out common non-contact emails
                    valid_emails = [e for e in emails if not any(skip in e.lower() for skip in ['example.com', 'sentry.io'])]
                    if valid_emails:
                        contact_data['email'] = valid_emails[0]
                
                # Extract phone
                phones = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', markdown)
                if phones:
                    contact_data['phone'] = phones[0]
            else:
                contact_data = {
                    'website': None,
                    'email': None,
                    'phone': None,
                    'address': None,
                    'contact_form_url': None
                }
        else:
            # Fallback to old method
            contact_data = self.ai_agent.find_dealer_website_and_contacts(
                dealer['business_name'],
                dealer.get('city', ''),
                dealer.get('state', '')
            )
        
        if contact_data.get('website'):
            enriched['website'] = contact_data['website']
        
        if contact_data.get('email'):
            enriched['email'] = contact_data['email']
        
        if contact_data.get('phone'):
            enriched['phone'] = contact_data['phone']
        
        if contact_data.get('address'):
            enriched['address'] = contact_data['address']
        
        if contact_data.get('contact_form_url'):
            enriched['contact_form_url'] = contact_data['contact_form_url']
        
        # Verify Class 3 SOT status if requested
        if verify_class3 and self.class3_verifier:
            website = enriched.get('website')
            if website:
                # Verify from website content
                class3_result = self.class3_verifier.verify_from_website(
                    website,
                    dealer['business_name']
                )
            else:
                # Verify from basic info only
                class3_result = self.class3_verifier.verify_class3_status(
                    dealer['business_name'],
                    dealer.get('city', ''),
                    dealer.get('state', ''),
                    None
                )
            
            # Add Class 3 verification data to enriched info
            enriched['class3_verified'] = class3_result.get('has_class3', False)
            enriched['class3_confidence'] = class3_result.get('confidence', 0.0)
            enriched['class3_evidence'] = class3_result.get('evidence', '')
            
            # If Class 3 verified, find contact pages for outreach
            if class3_result.get('has_class3') and self.contact_page_detector:
                website = enriched.get('website')
                if website:
                    contact_pages = self.contact_page_detector.find_contact_pages(
                        website,
                        dealer['business_name']
                    )
                    
                    if contact_pages:
                        enriched['contact_pages'] = contact_pages
                        enriched['preferred_contact_method'] = self.contact_page_detector.determine_preferred_method(contact_pages)
                    else:
                        enriched['contact_pages'] = []
                        enriched['preferred_contact_method'] = 'none'
        
        logger.info(f"Enriched dealer: {enriched}")
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
