"""
Web Search using Crawl4AI for reliable dealer website discovery
"""
import asyncio
import logging
from typing import Optional, List, Dict
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
import json
import re

logger = logging.getLogger(__name__)

class Crawl4AISearch:
    """
    Use Crawl4AI to search for dealer websites using Google search
    and validate URLs actually work.
    """
    
    def __init__(self, headless=True):
        import os
        # Set DISPLAY for VNC if not headless
        if not headless:
            os.environ['DISPLAY'] = ':0'
        
        self.browser_config = BrowserConfig(
            headless=headless,
            browser_type="chromium",
            java_script_enabled=True,
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security"
            ]
        )
    
    async def search_google(self, query: str) -> List[str]:
        """
        Search Google and extract result URLs using Crawl4AI.
        """
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(
                    search_url,
                    config=CrawlerRunConfig(
                        cache_mode="bypass"
                    )
                )
                
                if not result.success:
                    logger.warning(f"Google search failed for: {query}")
                    return []
                
                # Extract URLs from search results
                urls = []
                for link in result.links.get('internal', []) + result.links.get('external', []):
                    href = link.get('href', '')
                    
                    # Skip Google's own URLs and unwanted domains
                    if any(skip in href.lower() for skip in [
                        'google.com', 'youtube.com', 'facebook.com', 
                        'yelp.com', 'yellowpages.com', 'wikipedia.org',
                        '/search?', '/url?'
                    ]):
                        continue
                    
                    if href.startswith('http'):
                        urls.append(href)
                        if len(urls) >= 5:
                            break
                
                logger.info(f"Found {len(urls)} URLs from Google search")
                return urls
                
        except Exception as e:
            logger.error(f"Crawl4AI Google search error: {e}")
            return []
    
    async def validate_and_fetch(self, url: str) -> Optional[Dict]:
        """
        Validate URL works and fetch content using Crawl4AI.
        Returns dict with url, markdown, and links if successful.
        """
        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                result = await crawler.arun(
                    url,
                    config=CrawlerRunConfig(
                        cache_mode="bypass"
                    )
                )
                
                if not result.success:
                    logger.warning(f"❌ URL validation failed: {url}")
                    return None
                
                logger.info(f"✅ Validated working URL: {url}")
                
                return {
                    'url': url,
                    'markdown': result.markdown[:5000],  # First 5000 chars
                    'html': result.html[:10000] if result.html else '',
                    'links': result.links
                }
                
        except Exception as e:
            logger.warning(f"URL validation error for {url}: {e}")
            return None
    
    async def find_dealer_website(self, business_name: str, city: str, state: str) -> Optional[Dict]:
        """
        Search for dealer website and return validated result with content.
        Returns dict with url, markdown, and contact info if found.
        """
        logger.info(f"Crawl4AI searching for: {business_name}, {city}, {state}")
        
        # Try multiple search queries
        queries = [
            f"{business_name} {city} {state} firearms dealer",
            f"{business_name} {city} {state} gun shop",
            f"{business_name} {state} FFL dealer"
        ]
        
        for query in queries:
            urls = await self.search_google(query)
            
            if urls:
                # Try each URL until we find one that works
                for url in urls[:3]:
                    result = await self.validate_and_fetch(url)
                    if result:
                        return result
        
        logger.warning(f"No working URLs found for {business_name}")
        return None


def run_async_search(business_name: str, city: str, state: str, headless: bool = True) -> Optional[Dict]:
    """
    Synchronous wrapper for async search function.
    Set headless=False to watch browser automation in VNC viewer.
    """
    try:
        searcher = Crawl4AISearch(headless=headless)
        result = asyncio.run(searcher.find_dealer_website(business_name, city, state))
        return result
    except Exception as e:
        logger.error(f"Async search error: {e}")
        return None
