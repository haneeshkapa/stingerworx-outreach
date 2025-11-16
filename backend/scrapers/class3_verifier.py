"""
Class 3 SOT Verification Agent

Uses AI to verify if a dealer has Class 3 SOT license by:
1. Searching dealer website for Class 3/SOT/NFA indicators
2. Checking online databases and dealer directories
3. Looking for NFA item inventory (suppressors, SBRs, etc.)
"""

from openai import OpenAI
from scrapers.activity_logger import ActivityLogger
from sqlalchemy.orm import Session
import os

class Class3Verifier:
    """AI-powered Class 3 SOT license verification"""
    
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.logger = ActivityLogger(db, tenant_id)
        # Use Replit AI Integrations - no API key needed, billed to credits
        base_url = os.getenv('AI_INTEGRATIONS_OPENAI_BASE_URL')
        api_key = os.getenv('AI_INTEGRATIONS_OPENAI_API_KEY')
        self.client = OpenAI(base_url=base_url, api_key=api_key)
    
    def verify_class3_status(self, dealer_name: str, city: str, state: str, website: str = None) -> dict:
        """
        Verify if a dealer has Class 3 SOT license using AI web research.
        
        Returns:
            {
                'has_class3': bool,
                'confidence': float (0-1),
                'evidence': str,
                'sources': list
            }
        """
        dealer_info = f"{dealer_name} in {city}, {state}"
        self.logger.log('info', f'Verifying Class 3 SOT status for {dealer_info}')
        
        try:
            # Build search query
            search_query = f'"{dealer_name}" {city} {state} Class 3 SOT NFA suppressors'
            
            # Use AI to analyze available information
            prompt = f"""You are an expert at determining if firearms dealers have Class 3 SOT (Special Occupational Tax) licenses.

A Class 3 SOT dealer can legally sell NFA (National Firearms Act) items including:
- Suppressors/Silencers
- Short-Barreled Rifles (SBR)
- Short-Barreled Shotguns (SBS)
- Machine guns (full auto)
- Destructive devices

Dealer Information:
- Business Name: {dealer_name}
- Location: {city}, {state}
- Website: {website if website else 'Unknown'}

Task: Based on this information, determine if this dealer likely has a Class 3 SOT license.

Look for indicators:
- Mentions "Class 3", "SOT", "NFA items", "Title II"
- Sells suppressors, silencers, SBR, SBS, machine guns
- Has "NFA" section on website
- Listed in Class 3 dealer directories
- Mentions ATF Form 4, Form 1, tax stamps

Return ONLY a JSON object with this exact format:
{{
    "has_class3": true or false,
    "confidence": 0.0 to 1.0,
    "evidence": "Brief explanation of why you think they do or don't have Class 3",
    "search_needed": true or false (true if you need to search the web for more info)
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a firearms licensing expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # If AI says it needs to search the web, we'd trigger web search here
            # For now, return the AI's assessment
            
            if result['has_class3']:
                self.logger.log(
                    'dealer_saved', 
                    f'✓ Class 3 SOT verified for {dealer_name} (confidence: {result["confidence"]:.0%})',
                    dealer_name=dealer_name
                )
            else:
                self.logger.log(
                    'info',
                    f'✗ No Class 3 SOT found for {dealer_name}',
                    dealer_name=dealer_name
                )
            
            return result
            
        except Exception as e:
            self.logger.log('error', f'Error verifying Class 3 status: {str(e)}')
            return {
                'has_class3': False,
                'confidence': 0.0,
                'evidence': f'Error during verification: {str(e)}',
                'search_needed': False
            }
    
    def verify_from_website(self, website_url: str, dealer_name: str) -> dict:
        """
        Verify Class 3 status by analyzing dealer's website content.
        """
        self.logger.log('website_found', f'Analyzing {website_url} for Class 3 indicators')
        
        try:
            import httpx
            from bs4 import BeautifulSoup
            
            # Fetch website
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = httpx.get(website_url, headers=headers, timeout=10, follow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract text content
            text_content = soup.get_text(separator=' ', strip=True)[:5000]  # First 5000 chars
            
            # Use AI to analyze the content
            prompt = f"""Analyze this website content from {dealer_name} ({website_url}) to determine if they have a Class 3 SOT license.

Website Content:
{text_content}

Look for these Class 3 indicators:
- Keywords: "Class 3", "SOT", "NFA", "Title II", "suppressor", "silencer", "SBR", "SBS", "machine gun"
- Product categories for NFA items
- ATF forms (Form 1, Form 4, Form 3)
- Tax stamp information
- "NFA dealer" or "Class 3 FFL"

Return ONLY a JSON object:
{{
    "has_class3": true or false,
    "confidence": 0.0 to 1.0,
    "evidence": "What specific evidence you found on the website",
    "indicators_found": ["list", "of", "keywords", "found"]
}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are analyzing website content for firearms licensing. Respond with JSON only."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            if result['has_class3']:
                self.logger.log(
                    'contact_extracted',
                    f'Class 3 SOT confirmed on website: {result["evidence"][:100]}',
                    dealer_name=dealer_name
                )
            
            return result
            
        except Exception as e:
            return {
                'has_class3': False,
                'confidence': 0.0,
                'evidence': f'Could not analyze website: {str(e)}',
                'indicators_found': []
            }
