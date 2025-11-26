import requests
from bs4 import BeautifulSoup
from typing import Optional
import re


class ScraperService:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        self.timeout = 15
        
        # Predefined URLs for popular platforms
        self.known_urls = {
            'linkedin': {
                'terms': 'https://www.linkedin.com/legal/user-agreement',
                'privacy': 'https://www.linkedin.com/legal/privacy-policy',
                'cookie': 'https://www.linkedin.com/legal/cookie-policy'
            },
            'instagram': {
                'terms': 'https://help.instagram.com/581066165581870',
                'privacy': 'https://help.instagram.com/519522125107875',
                'cookie': 'https://help.instagram.com/1896641480634370'
            },
            'tiktok': {
                'terms': 'https://www.tiktok.com/legal/page/us/terms-of-service/en',
                'privacy': 'https://www.tiktok.com/legal/page/us/privacy-policy/en',
                'cookie': 'https://www.tiktok.com/legal/page/us/cookie-policy/en'
            },
            'tinder': {
                'terms': 'https://policies.tinder.com/terms',
                'privacy': 'https://policies.tinder.com/privacy',
                'cookie': 'https://policies.tinder.com/cookie-policy'
            },
            'facebook': {
                'terms': 'https://www.facebook.com/legal/terms',
                'privacy': 'https://www.facebook.com/privacy/policy',
                'cookie': 'https://www.facebook.com/policies/cookies'
            },
            'twitter': {
                'terms': 'https://twitter.com/en/tos',
                'privacy': 'https://twitter.com/en/privacy',
                'cookie': 'https://twitter.com/en/privacy#update'
            },
            'x': {
                'terms': 'https://x.com/en/tos',
                'privacy': 'https://x.com/en/privacy',
                'cookie': 'https://x.com/en/privacy#update'
            },
            'snapchat': {
                'terms': 'https://www.snap.com/en-US/terms',
                'privacy': 'https://www.snap.com/en-US/privacy/privacy-policy',
                'cookie': 'https://www.snap.com/en-US/cookie-policy'
            },
            'whatsapp': {
                'terms': 'https://www.whatsapp.com/legal/terms-of-service',
                'privacy': 'https://www.whatsapp.com/legal/privacy-policy',
                'cookie': 'https://www.whatsapp.com/legal/cookies'
            },
            'spotify': {
                'terms': 'https://www.spotify.com/us/legal/end-user-agreement/',
                'privacy': 'https://www.spotify.com/us/legal/privacy-policy/',
                'cookie': 'https://www.spotify.com/us/legal/cookies-policy/'
            },
            'netflix': {
                'terms': 'https://help.netflix.com/legal/termsofuse',
                'privacy': 'https://help.netflix.com/legal/privacy',
                'cookie': 'https://help.netflix.com/legal/privacy#cookies'
            },
            'amazon': {
                'terms': 'https://www.amazon.com/gp/help/customer/display.html?nodeId=508088',
                'privacy': 'https://www.amazon.com/gp/help/customer/display.html?nodeId=468496',
                'cookie': 'https://www.amazon.com/gp/help/customer/display.html?nodeId=201890250'
            },
            'uber': {
                'terms': 'https://www.uber.com/legal/en/document/?name=general-terms-of-use',
                'privacy': 'https://www.uber.com/legal/en/document/?name=privacy-notice',
                'cookie': 'https://www.uber.com/legal/en/document/?name=cookie-notice'
            },
            'airbnb': {
                'terms': 'https://www.airbnb.com/help/article/2908',
                'privacy': 'https://www.airbnb.com/help/article/2855',
                'cookie': 'https://www.airbnb.com/help/article/2855'
            },
            'discord': {
                'terms': 'https://discord.com/terms',
                'privacy': 'https://discord.com/privacy',
                'cookie': 'https://discord.com/privacy'
            },
            'reddit': {
                'terms': 'https://www.redditinc.com/policies/user-agreement',
                'privacy': 'https://www.reddit.com/policies/privacy-policy',
                'cookie': 'https://www.reddit.com/policies/cookies'
            },
            'pinterest': {
                'terms': 'https://policy.pinterest.com/en/terms-of-service',
                'privacy': 'https://policy.pinterest.com/en/privacy-policy',
                'cookie': 'https://policy.pinterest.com/en/cookies'
            },
            'zoom': {
                'terms': 'https://explore.zoom.us/en/terms/',
                'privacy': 'https://explore.zoom.us/en/privacy/',
                'cookie': 'https://explore.zoom.us/en/cookie-policy/'
            }
        }

    def get_known_url(self, company_name: str, doc_type: str = 'terms') -> Optional[str]:
        """
        Get the known URL for a popular platform
        
        Args:
            company_name: Name of the company (case-insensitive)
            doc_type: Type of document ('terms', 'privacy', 'cookie')
        
        Returns:
            URL if found, None otherwise
        """
        company_key = company_name.lower().strip()
        
        if company_key in self.known_urls:
            return self.known_urls[company_key].get(doc_type)
        
        return None

    def fetch_terms_from_url(self, url: str, company_name: Optional[str] = None) -> str:
        """
        Fetch and extract terms and conditions text from a URL
        
        Args:
            url: URL to fetch from, or 'auto' to use known URL
            company_name: Company name (required if url is 'auto')
        
        Returns:
            Extracted text content
        """
        # Handle auto-fetch for known platforms
        if url.lower() == 'auto' and company_name:
            known_url = self.get_known_url(company_name, 'terms')
            if known_url:
                url = known_url
            else:
                raise ValueError(f"No known terms URL for '{company_name}'. Please provide a URL manually.")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout, allow_redirects=True)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer',
                                'aside', 'form', 'button', 'iframe', 'noscript']):
                element.decompose()

            # Try to find main content area
            main_content = self._find_main_content(soup)

            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
            else:
                # Fallback to body
                body = soup.find('body')
                text = body.get_text(separator='\n', strip=True) if body else ''

            # Clean up the text
            text = self._clean_text(text)

            if len(text) < 100:
                raise ValueError("Could not extract meaningful content from the page")

            return text

        except requests.exceptions.Timeout:
            raise ValueError("Request timed out. The website took too long to respond.")
        except requests.exceptions.ConnectionError:
            raise ValueError("Could not connect to the website. Please check the URL.")
        except requests.exceptions.HTTPError as e:
            raise ValueError(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            raise ValueError(f"Failed to fetch content: {str(e)}")

    def _find_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """
        Try to find the main content area of the page
        """
        # Common selectors for terms/policy pages
        selectors = [
            'main',
            'article',
            '[role="main"]',
            '.terms-content',
            '.policy-content',
            '.legal-content',
            '.terms-and-conditions',
            '.content',
            '#content',
            '#main-content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.page-content',
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element and len(element.get_text(strip=True)) > 500:
                return element

        # Try finding largest text block
        paragraphs = soup.find_all(['p', 'div', 'section'])
        if paragraphs:
            largest = max(paragraphs, key=lambda x: len(x.get_text(strip=True)), default=None)
            if largest and len(largest.get_text(strip=True)) > 500:
                return largest.parent if largest.parent else largest

        return None

    def _clean_text(self, text: str) -> str:
        """
        Clean up extracted text
        """
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        # Remove common cookie/banner text patterns
        patterns_to_remove = [
            r'Accept all cookies.*?settings',
            r'We use cookies.*?accept',
            r'Cookie Policy.*?Accept',
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)

        # Trim to reasonable length (keep first 50k chars)
        if len(text) > 50000:
            text = text[:50000] + '\n\n[Content truncated...]'

        return text.strip()
