"""
AI Message Generation Service

Uses OpenAI to generate personalized outreach messages for dealers.
"""

import os
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class MessageGenerator:
    """Generates personalized outreach messages using LLM"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            logger.warning("OpenAI API key not set - will use template-based generation")
    
    def generate_personalized_message(
        self,
        dealer: Dict,
        template: Dict,
        company_info: Dict
    ) -> Dict[str, str]:
        """
        Generate personalized subject and message for a dealer
        
        Args:
            dealer: Dealer information (name, location, etc.)
            template: Message template with subject_template and body_template
            company_info: Information about the company (Stingerworx)
        
        Returns:
            Dict with 'subject' and 'message' keys
        """
        
        dealer_name = dealer.get('business_name', 'there')
        state = dealer.get('state', '')
        city = dealer.get('city', '')
        
        subject = template.get('subject_template', '').format(
            dealer_name=dealer_name,
            state=state
        )
        
        body = template.get('body_template', '').format(
            dealer_name=dealer_name,
            business_name=dealer_name,
            state=state,
            city=city
        )
        
        if self.api_key:
            try:
                personalized = self._generate_with_llm(dealer, template, company_info)
                return personalized
            except Exception as e:
                logger.error(f"LLM generation failed, using template: {e}")
        
        return {
            'subject': subject,
            'message': body
        }
    
    def _generate_with_llm(self, dealer: Dict, template: Dict, company_info: Dict) -> Dict[str, str]:
        """
        Generate using OpenAI (placeholder for future implementation)
        """
        
        prompt = f"""Generate a personalized outreach message for the following dealer:

Dealer Information:
- Business: {dealer.get('business_name')}
- Location: {dealer.get('city')}, {dealer.get('state')}

Company: {company_info.get('company_name', 'Stingerworx')}
Product: {company_info.get('product', 'High-quality suppressors')}

Template:
Subject: {template.get('subject_template')}
Body: {template.get('body_template')}

Make the message feel personal and relevant to this specific dealer's location and business.
Keep it professional, concise, and focused on the partnership opportunity."""

        logger.info("Would call OpenAI here with prompt")
        
        return {
            'subject': template.get('subject_template'),
            'message': template.get('body_template')
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    generator = MessageGenerator()
    
    dealer = {
        'business_name': 'Texas Tactical Arms',
        'city': 'Austin',
        'state': 'TX'
    }
    
    template = {
        'subject_template': 'Partnership Opportunity: Stingerworx Suppressors',
        'body_template': 'Hello {dealer_name}, we make great suppressors...'
    }
    
    company = {
        'company_name': 'Stingerworx',
        'product': 'High-quality suppressors'
    }
    
    message = generator.generate_personalized_message(dealer, template, company)
    print(f"Subject: {message['subject']}")
    print(f"Message: {message['message']}")
