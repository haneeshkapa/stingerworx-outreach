"""
Contact Page Detection and Form Analysis

Finds contact pages on dealer websites and analyzes form fields for future automation.
Only runs for Class 3 verified dealers.
"""

import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from urllib.parse import urljoin, urlparse
from scrapers.activity_logger import ActivityLogger
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class ContactPageDetector:
    """Detects contact pages and analyzes form fields for automated outreach"""
    
    # Common contact page patterns to search for
    CONTACT_PAGE_PATTERNS = [
        '/contact',
        '/contact-us',
        '/contactus',
        '/get-in-touch',
        '/contact.html',
        '/contact.php',
        '/dealer-inquiry',
        '/dealer-enquiry',
        '/become-a-dealer',
        '/become-dealer',
        '/dealer-application',
        '/wholesale-inquiry',
        '/wholesale',
        '/dealer-info',
        '/dealer-signup'
    ]
    
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id
        self.logger = ActivityLogger(db, tenant_id)
        self.client = httpx.Client(timeout=15.0, follow_redirects=True)
    
    def find_contact_pages(self, base_url: str, dealer_name: str) -> List[Dict]:
        """
        Find all contact pages on dealer website.
        
        Returns list of contact pages with their form data:
        [
            {
                'url': '/contact',
                'full_url': 'https://dealer.com/contact',
                'has_form': True,
                'form_fields': [...],
                'fallback_email': 'info@dealer.com',
                'fallback_phone': '555-1234'
            }
        ]
        """
        self.logger.log('info', f'🔍 Searching for contact pages on {base_url}', dealer_name=dealer_name)
        
        contact_pages = []
        
        try:
            # Try each common contact page pattern
            for pattern in self.CONTACT_PAGE_PATTERNS:
                full_url = urljoin(base_url, pattern)
                
                try:
                    response = self.client.get(full_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }, timeout=10)
                    
                    # Check if page exists (200 status)
                    if response.status_code == 200:
                        page_data = self._analyze_contact_page(full_url, response.text, dealer_name)
                        if page_data:
                            contact_pages.append(page_data)
                            self.logger.log(
                                'contact_extracted',
                                f'📄 Found contact page: {pattern}',
                                dealer_name=dealer_name
                            )
                
                except httpx.TimeoutException:
                    logger.warning(f"Timeout accessing {full_url}")
                    continue
                except Exception as e:
                    logger.warning(f"Error checking {full_url}: {str(e)}")
                    continue
            
            # Log summary
            if contact_pages:
                form_count = sum(1 for p in contact_pages if p['has_form'])
                self.logger.log(
                    'contact_extracted',
                    f'✓ Found {len(contact_pages)} contact page(s), {form_count} with forms',
                    dealer_name=dealer_name
                )
            else:
                self.logger.log('info', f'No contact pages found on {base_url}', dealer_name=dealer_name)
            
            return contact_pages
            
        except Exception as e:
            self.logger.log('error', f'Error finding contact pages: {str(e)}', dealer_name=dealer_name)
            return []
    
    def _analyze_contact_page(self, url: str, html_content: str, dealer_name: str) -> Optional[Dict]:
        """
        Analyze a contact page for forms and fallback contact info.
        
        Returns:
            {
                'url': relative URL,
                'full_url': absolute URL,
                'has_form': bool,
                'form_fields': [...],
                'fallback_email': str or None,
                'fallback_phone': str or None
            }
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Parse URL
            parsed_url = urlparse(url)
            relative_url = parsed_url.path or '/'
            
            page_data = {
                'url': relative_url,
                'full_url': url,
                'has_form': False,
                'form_fields': [],
                'fallback_email': None,
                'fallback_phone': None
            }
            
            # 1. Look for forms
            forms = soup.find_all('form')
            if forms:
                # Analyze the first form (usually the contact form)
                form = forms[0]
                form_fields = self._extract_form_fields(form)
                
                if form_fields:
                    page_data['has_form'] = True
                    page_data['form_fields'] = form_fields
                    logger.info(f"Found form with {len(form_fields)} fields on {url}")
            
            # 2. Fallback: Extract email and phone if no form found
            if not page_data['has_form']:
                # Extract emails
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = soup.find_all(string=lambda text: text and '@' in text)
                for email_tag in emails:
                    import re
                    matches = re.findall(email_pattern, str(email_tag))
                    if matches:
                        page_data['fallback_email'] = matches[0]
                        break
                
                # Extract phone numbers
                phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
                text_content = soup.get_text()
                import re
                phone_matches = re.findall(phone_pattern, text_content)
                if phone_matches:
                    page_data['fallback_phone'] = phone_matches[0]
            
            return page_data
            
        except Exception as e:
            logger.error(f"Error analyzing contact page {url}: {str(e)}")
            return None
    
    def _extract_form_fields(self, form) -> List[Dict]:
        """
        Extract all input fields from a form.
        
        Returns:
            [
                {
                    'name': 'email',
                    'type': 'email',
                    'id': 'user-email',
                    'required': True,
                    'placeholder': 'Your email address'
                }
            ]
        """
        fields = []
        
        # Find all input, textarea, and select fields
        inputs = form.find_all(['input', 'textarea', 'select'])
        
        for input_field in inputs:
            field_type = input_field.get('type', 'text')
            field_name = input_field.get('name', '')
            
            # Skip submit buttons, hidden fields, and unnamed fields
            if field_type in ['submit', 'button', 'hidden', 'image'] or not field_name:
                continue
            
            field_data = {
                'name': field_name,
                'type': field_type,
                'id': input_field.get('id', ''),
                'required': input_field.has_attr('required'),
                'placeholder': input_field.get('placeholder', '')
            }
            
            # For textarea, override type
            if input_field.name == 'textarea':
                field_data['type'] = 'textarea'
            
            # For select, override type
            if input_field.name == 'select':
                field_data['type'] = 'select'
                # Extract options
                options = [opt.get_text(strip=True) for opt in input_field.find_all('option')]
                field_data['options'] = options
            
            fields.append(field_data)
        
        return fields
    
    def determine_preferred_method(self, contact_pages: List[Dict]) -> str:
        """
        Determine the preferred contact method based on available pages.
        
        Priority: form > email > phone
        """
        if not contact_pages:
            return 'none'
        
        # Check if any page has a form
        has_form = any(page['has_form'] for page in contact_pages)
        if has_form:
            return 'form'
        
        # Check if any page has email
        has_email = any(page['fallback_email'] for page in contact_pages)
        if has_email:
            return 'email'
        
        # Check if any page has phone
        has_phone = any(page['fallback_phone'] for page in contact_pages)
        if has_phone:
            return 'phone'
        
        return 'none'
