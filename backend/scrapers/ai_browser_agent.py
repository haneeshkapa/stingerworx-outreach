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
                            ['google.com', 'youtube.com', 'facebook.com', 'yelp.com', 'yellowpages.com', 'wikipedia.org']):
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
        Search DuckDuckGo using JSON API (more reliable) and extract URLs.
        """
        try:
            search_url = f"https://api.duckduckgo.com/?q={query.replace(' ', '+')}&format=json"
            response = self.client.get(search_url, timeout=10)
            
            urls = []
            if response.status_code == 200:
                data = response.json()
                
                if data.get('AbstractURL'):
                    urls.append(data['AbstractURL'])
                
                for result in data.get('RelatedTopics', [])[:5]:
                    if isinstance(result, dict) and result.get('FirstURL'):
                        url = result['FirstURL']
                        if not any(skip in url.lower() for skip in 
                            ['wikipedia.org', 'duckduckgo.com', 'facebook.com']):
                            urls.append(url)
                
                logger.info(f"Found {len(urls)} URLs from DuckDuckGo API")
            
            if not urls:
                logger.info("DuckDuckGo API returned no results, trying lite search")
                search_url = f"https://lite.duckduckgo.com/lite/?q={query.replace(' ', '+')}"
                response = self.client.get(search_url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('http') and not any(skip in href.lower() for skip in 
                            ['duckduckgo.com', 'facebook.com', 'yelp.com', 'wikipedia.org']):
                            urls.append(href)
                            if len(urls) >= 5:
                                break
                    
                    logger.info(f"Found {len(urls)} URLs from DuckDuckGo Lite")
            
            return urls[:5]
            
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
            prompt = f"""Analyze this Class 3 SOT/NFA firearms dealer website and extract contact information.

URL: {url}

Page Content:
{page_content[:3000]}

Extract the following information if available:
- Email address (look for contact@, info@, sales@, nfa@, class3@, etc.)
- Phone number (look for various formats)
- Physical address (street address, city, state, zip)
- Contact form URL (IMPORTANT: Look for contact form, contact page, or dealer inquiry form)

Priority: Contact forms are preferred over email for reaching dealers.

Respond with ONLY valid JSON in this exact format (use null without quotes for missing values):
{{
    "email": "email@example.com",
    "phone": "123-456-7890",
    "address": "street address",
    "contact_form_url": "full URL"
}}"""

            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting contact information from websites. Respond ONLY with valid JSON, no markdown, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content.strip()
            
            import json
            
            if result.startswith('```json'):
                result = result.replace('```json', '').replace('```', '').strip()
            
            contact_info = json.loads(result)
            
            logger.info(f"AI extracted contact info from {url}: {contact_info}")
            return contact_info
            
        except Exception as e:
            logger.error(f"AI extraction error: {e}")
            logger.error(f"Response was: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
            return {}
    
    def ai_search_for_website(self, business_name: str, city: str, state: str) -> Optional[str]:
        """
        Use AI to generate likely website URL based on business name.
        """
        try:
            prompt = f"""Based on the business name, generate the most likely website URL for this gun dealer/firearms business.

Business Name: {business_name}
City: {city}
State: {state}

Common patterns for gun dealers:
- businessname.com
- citynameguns.com  
- statearms.com
- businessnamefirearms.com

Generate the single most likely website URL. Respond with ONLY the URL, nothing else.
Example format: https://www.example.com"""

            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at predicting business websites. Respond with only a URL."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            url = response.choices[0].message.content.strip()
            logger.info(f"AI predicted website: {url}")
            return url
            
        except Exception as e:
            logger.error(f"AI URL prediction error: {e}")
            return None
    
    def find_dealer_website_and_contacts(self, business_name: str, city: str, state: str) -> Dict:
        """
        Main method: Search for dealer, find website, and extract contact info using AI.
        Specifically targets Class 3 SOT dealers (NFA/suppressor dealers).
        """
        logger.info(f"AI Agent searching for Class 3 SOT dealer: {business_name}, {city}, {state}")
        
        search_query = f"{business_name} {city} {state} Class 3 SOT NFA suppressor dealer firearms"
        
        urls = self.search_duckduckgo(search_query)
        if not urls:
            urls = self.search_google(search_query)
        
        if not urls:
            logger.info(f"No URLs from search, using AI prediction for {business_name}")
            predicted_url = self.ai_search_for_website(business_name, city, state)
            if predicted_url:
                urls = [predicted_url]
        
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
