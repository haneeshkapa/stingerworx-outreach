"""
Simple HTTP-based web search without browser automation
Uses SerpAPI or direct HTTP requests to find dealer websites
"""
import httpx
import logging
from typing import Optional, Dict, List
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class HTTPSearch:
    """
    HTTP-only search for dealer websites.
    No browser automation required - works in any environment.
    """
    
    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
    
    def search_duckduckgo_html(self, query: str) -> List[str]:
        """
        Search DuckDuckGo using HTML scraping (no API needed).
        """
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            
            response = self.client.get(search_url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"DuckDuckGo returned status {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = []
            
            # Find all result links
            for result_link in soup.find_all('a', class_='result__a'):
                href = result_link.get('href', '')
                
                # Skip unwanted domains
                if any(skip in href.lower() for skip in [
                    'duckduckgo.com', 'facebook.com', 'yelp.com', 
                    'yellowpages.com', 'wikipedia.org', 'youtube.com'
                ]):
                    continue
                
                if href.startswith('http'):
                    urls.append(href)
                    if len(urls) >= 5:
                        break
            
            logger.info(f"Found {len(urls)} URLs from DuckDuckGo")
            return urls
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def validate_url(self, url: str) -> bool:
        """
        Check if URL is accessible and returns 200 OK.
        """
        try:
            # Try HEAD first (faster)
            response = self.client.head(url, timeout=10)
            if response.status_code == 200:
                return True
            
            # Fallback to GET if HEAD doesn't work
            response = self.client.get(url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"URL validation failed for {url}: {e}")
            return False
    
    def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch webpage HTML content.
        """
        try:
            response = self.client.get(url, timeout=15)
            
            if response.status_code == 200:
                return response.text
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_contact_info(self, html: str, url: str) -> Dict:
        """
        Extract contact information from HTML.
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        contact_info = {
            'email': None,
            'phone': None,
            'contact_form_url': None
        }
        
        # Extract email
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if emails:
            # Filter out common non-contact emails
            valid_emails = [e for e in emails if not any(skip in e.lower() for skip in ['example.com', 'sentry.io', 'test.com'])]
            if valid_emails:
                contact_info['email'] = valid_emails[0]
        
        # Extract phone
        phones = re.findall(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text)
        if phones:
            contact_info['phone'] = phones[0]
        
        # Find contact form URL
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').lower()
            link_text = link.get_text().lower()
            
            if 'contact' in href or 'contact' in link_text:
                contact_url = href if href.startswith('http') else url.rstrip('/') + '/' + href.lstrip('/')
                contact_info['contact_form_url'] = contact_url
                break
        
        return contact_info
    
    def find_dealer_website(self, business_name: str, city: str, state: str) -> Optional[Dict]:
        """
        Search for dealer website and return validated result with contact info.
        """
        logger.info(f"HTTP search for: {business_name}, {city}, {state}")
        
        # Try multiple search queries
        queries = [
            f"{business_name} {city} {state} firearms dealer",
            f"{business_name} {city} {state} gun shop",
            f'"{business_name}" {state} FFL'
        ]
        
        for query in queries:
            urls = self.search_duckduckgo_html(query)
            
            if not urls:
                continue
            
            # Try each URL until we find one that works
            for url in urls[:3]:
                logger.info(f"Validating URL: {url}")
                
                if not self.validate_url(url):
                    logger.warning(f"❌ URL validation failed: {url}")
                    continue
                
                logger.info(f"✅ Validated working URL: {url}")
                
                # Fetch content and extract contact info
                html = self.fetch_page_content(url)
                if html:
                    contact_info = self.extract_contact_info(html, url)
                    contact_info['website'] = url
                    contact_info['html_snippet'] = html[:1000]  # First 1000 chars for Class 3 verification
                    
                    return contact_info
        
        logger.warning(f"No working URLs found for {business_name}")
        return None
