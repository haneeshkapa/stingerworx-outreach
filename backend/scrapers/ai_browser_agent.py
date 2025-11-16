import os
import logging
import httpx
from bs4 import BeautifulSoup
from typing import Optional, Dict
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIBrowserAgent:
    """
    AI-powered web agent that searches the web and extracts contact information
    using real web requests and OpenAI to analyze page content.
    """
    
    def __init__(self):
        self.client = httpx.Client(
            timeout=30.0, 
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        base_url = os.getenv('AI_INTEGRATIONS_OPENAI_BASE_URL')
        api_key = os.getenv('AI_INTEGRATIONS_OPENAI_API_KEY')
        
        self.openai = OpenAI(base_url=base_url, api_key=api_key)
        logger.info("AI Browser Agent initialized with OpenAI")
    
    def search_google(self, query: str) -> list[str]:
        """
        Search Google using HTTP requests and extract result URLs.
        """
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            response = self.client.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                urls = []
                
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if '/url?q=' in href:
                        url = href.split('/url?q=')[1].split('&')[0]
                        if url.startswith('http') and not any(skip in url.lower() for skip in 
                            ['google.com', 'youtube.com', 'facebook.com', 'yelp.com', 'yellowpages.com']):
                            urls.append(url)
                            if len(urls) >= 5:
                                break
                
                logger.info(f"Found {len(urls)} URLs from Google search")
                return urls
            
            return []
            
        except Exception as e:
            logger.error(f"Google search error: {e}")
            return []
    
    def search_duckduckgo(self, query: str) -> list[str]:
        """
        Search DuckDuckGo (more reliable for scraping) and extract URLs.
        """
        try:
            search_url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            response = self.client.get(search_url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                urls = []
                
                results = soup.find_all('a', class_='result__url')
                for result in results[:5]:
                    href = result.get('href', '')
                    if href and href.startswith('http'):
                        if not any(skip in href.lower() for skip in 
                            ['duckduckgo.com', 'facebook.com', 'yelp.com', 'yellowpages.com']):
                            urls.append(href)
                
                logger.info(f"Found {len(urls)} URLs from DuckDuckGo")
                return urls
            
            return []
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    def fetch_page_content(self, url: str) -> Optional[str]:
        """
        Fetch and extract text content from a webpage.
        """
        try:
            response = self.client.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                    script.decompose()
                
                text = soup.get_text(separator='\n', strip=True)
                
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                text = '\n'.join(lines[:150])
                
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
    
    def ai_extract_contact_info(self, url: str, page_content: str) -> Dict:
        """
        Use AI to extract contact information from page content.
        """
        try:
            prompt = f"""Analyze this business website content and extract contact information.

URL: {url}

Page Content:
{page_content[:3000]}

Extract the following information if available:
- Email address (look for contact@, info@, sales@, etc.)
- Phone number (look for various formats)
- Physical address (street address, city, state, zip)
- Contact form URL (if they mention a contact page)

Respond in this exact JSON format:
{{
    "email": "email@example.com or null",
    "phone": "123-456-7890 or null",
    "address": "street address or null",
    "contact_form_url": "full URL or null"
}}

Only include information that is clearly present. Use null if not found."""

            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting contact information from websites. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )
            
            result = response.choices[0].message.content
            
            import json
            contact_info = json.loads(result)
            
            logger.info(f"AI extracted contact info from {url}: {contact_info}")
            return contact_info
            
        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            return {}
    
    def find_dealer_website_and_contacts(self, business_name: str, city: str, state: str) -> Dict:
        """
        Main method: Search for dealer, find website, and extract contact info using AI.
        """
        logger.info(f"AI Agent searching for: {business_name}, {city}, {state}")
        
        search_query = f"{business_name} {city} {state} gun shop firearms"
        
        urls = self.search_duckduckgo(search_query)
        if not urls:
            urls = self.search_google(search_query)
        
        if not urls:
            logger.warning(f"No URLs found for {business_name}")
            return {
                'website': None,
                'email': None,
                'phone': None,
                'address': None,
                'contact_form_url': None
            }
        
        website_url = urls[0]
        logger.info(f"Found website: {website_url}")
        
        page_content = self.fetch_page_content(website_url)
        if not page_content:
            return {
                'website': website_url,
                'email': None,
                'phone': None,
                'address': None,
                'contact_form_url': None
            }
        
        contact_info = self.ai_extract_contact_info(website_url, page_content)
        contact_info['website'] = website_url
        
        return contact_info
