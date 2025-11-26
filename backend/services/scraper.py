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

    def fetch_terms_from_url(self, url: str) -> str:
        """
        Fetch and extract terms and conditions text from a URL
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
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
