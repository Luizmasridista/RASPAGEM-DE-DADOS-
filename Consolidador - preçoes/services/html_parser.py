"""
HTML parsing and data extraction for price monitoring.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class HTMLParser:
    """
    HTML parser for extracting product data from e-commerce sites.
    
    Features:
    - Multiple selector support with fallbacks
    - Price extraction with regex for different formats
    - Product name extraction with fallback selectors
    - Site-specific selector configurations
    - Robust error handling and logging
    """
    
    # Default selectors for common e-commerce sites
    DEFAULT_SELECTORS = {
        'amazon.com': {
            'price': [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price-range .a-price .a-offscreen'
            ],
            'name': [
                '#productTitle',
                '.product-title',
                'h1.a-size-large'
            ]
        },
        'mercadolivre.com.br': {
            'price': [
                '.andes-money-amount__fraction',
                '.price-tag-fraction',
                '.price-tag-amount',
                '.ui-pdp-price__fraction'
            ],
            'name': [
                '.ui-pdp-title',
                '.item-title',
                'h1.ui-pdp-title'
            ]
        },
        'americanas.com.br': {
            'price': [
                '.price-value',
                '.sales-price',
                '.best-price'
            ],
            'name': [
                '.product-title',
                'h1.product-title',
                '.pdp-product-name'
            ]
        },
        'magazineluiza.com.br': {
            'price': [
                '.price-value',
                '.price-template__text',
                '[data-testid="price-value"]'
            ],
            'name': [
                '.header-product__title',
                'h1[data-testid="heading-product-title"]',
                '.product-title'
            ]
        },
        'casasbahia.com.br': {
            'price': [
                '.price-value',
                '.sales-price',
                '.best-price'
            ],
            'name': [
                '.product-title',
                'h1.product-title'
            ]
        },
        'extra.com.br': {
            'price': [
                '.price-value',
                '.sales-price'
            ],
            'name': [
                '.product-title',
                'h1.product-title'
            ]
        }
    }
    
    # Generic fallback selectors
    GENERIC_SELECTORS = {
        'price': [
            '[class*="price"]',
            '[id*="price"]',
            '[data-testid*="price"]',
            '.price',
            '#price',
            '.valor',
            '.preco',
            '.money',
            '.currency'
        ],
        'name': [
            'h1',
            '.product-title',
            '.product-name',
            '.item-title',
            '.title',
            '[class*="title"]',
            '[class*="name"]'
        ]
    }
    
    # Price regex patterns for different formats
    PRICE_PATTERNS = [
        # R$ 1.234,56 or R$1.234,56
        r'R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)',
        # 1.234,56 (Brazilian format)
        r'(\d{1,3}(?:\.\d{3})*,\d{2})',
        # 1234.56 (US format)
        r'(\d+\.?\d*)',
        # Just numbers with possible decimal
        r'(\d+(?:,\d{2})?)',
    ]
    
    def __init__(self):
        """Initialize HTML parser."""
        self.site_selectors = self.DEFAULT_SELECTORS.copy()
        logger.info("HTMLParser initialized with default selectors")
    
    def add_site_selectors(self, domain: str, selectors: Dict[str, List[str]]) -> None:
        """
        Add custom selectors for a specific site.
        
        Args:
            domain: Domain name (e.g., 'example.com')
            selectors: Dictionary with 'price' and 'name' selector lists
        """
        self.site_selectors[domain.lower()] = selectors
        logger.info(f"Added custom selectors for domain: {domain}")
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc.lower()
        except Exception as e:
            logger.warning(f"Failed to parse domain from URL {url}: {e}")
            return ""
    
    def _get_selectors_for_url(self, url: str, custom_selectors: Optional[Dict[str, List[str]]] = None) -> Dict[str, List[str]]:
        """
        Get appropriate selectors for a URL.
        
        Args:
            url: Target URL
            custom_selectors: Custom selectors to use instead of defaults
            
        Returns:
            Dictionary with 'price' and 'name' selector lists
        """
        if custom_selectors:
            return custom_selectors
        
        domain = self._get_domain_from_url(url)
        
        # Try exact domain match
        if domain in self.site_selectors:
            logger.debug(f"Using site-specific selectors for {domain}")
            return self.site_selectors[domain]
        
        # Try partial domain match (for subdomains)
        for site_domain, selectors in self.site_selectors.items():
            if site_domain in domain:
                logger.debug(f"Using partial match selectors for {domain} (matched {site_domain})")
                return selectors
        
        # Fall back to generic selectors
        logger.debug(f"Using generic selectors for {domain}")
        return self.GENERIC_SELECTORS
    
    def _extract_text_from_element(self, element: Tag) -> str:
        """
        Extract clean text from a BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Cleaned text content
        """
        if not element:
            return ""
        
        # Get text with separator to preserve spaces between elements
        text = element.get_text(separator=' ', strip=True)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _parse_price_from_text(self, text: str) -> Optional[float]:
        """
        Parse price from text using regex patterns.
        
        Args:
            text: Text containing price information
            
        Returns:
            Parsed price as float, or None if not found
        """
        if not text:
            return None
        
        logger.debug(f"Parsing price from text: '{text}'")
        
        for pattern in self.PRICE_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                price_str = matches[0]
                logger.debug(f"Found price match: '{price_str}' using pattern: {pattern}")
                
                try:
                    # Handle Brazilian format (1.234,56)
                    if ',' in price_str and '.' in price_str:
                        # Remove thousands separator (.) and replace decimal separator (,)
                        price_str = price_str.replace('.', '').replace(',', '.')
                    elif ',' in price_str and price_str.count(',') == 1:
                        # Only decimal separator
                        price_str = price_str.replace(',', '.')
                    
                    price = float(price_str)
                    logger.debug(f"Successfully parsed price: {price}")
                    return price
                    
                except ValueError as e:
                    logger.debug(f"Failed to convert '{price_str}' to float: {e}")
                    continue
        
        logger.warning(f"No price found in text: '{text}'")
        return None
    
    def _extract_price_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[float]:
        """
        Extract price using multiple selectors with fallbacks.
        
        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try
            
        Returns:
            Extracted price as float, or None if not found
        """
        for selector in selectors:
            try:
                logger.debug(f"Trying price selector: {selector}")
                elements = soup.select(selector)
                
                for element in elements:
                    text = self._extract_text_from_element(element)
                    if text:
                        price = self._parse_price_from_text(text)
                        if price is not None:
                            logger.info(f"Successfully extracted price {price} using selector: {selector}")
                            return price
                
            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue
        
        return None
    
    def _extract_name_with_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """
        Extract product name using multiple selectors with fallbacks.
        
        Args:
            soup: BeautifulSoup object
            selectors: List of CSS selectors to try
            
        Returns:
            Extracted product name, or None if not found
        """
        for selector in selectors:
            try:
                logger.debug(f"Trying name selector: {selector}")
                elements = soup.select(selector)
                
                for element in elements:
                    text = self._extract_text_from_element(element)
                    if text and len(text.strip()) > 0:
                        # Clean up the name
                        name = text.strip()
                        # Remove excessive whitespace and newlines
                        name = re.sub(r'\s+', ' ', name)
                        # Limit length to reasonable size
                        if len(name) > 200:
                            name = name[:200] + "..."
                        
                        logger.info(f"Successfully extracted name '{name}' using selector: {selector}")
                        return name
                
            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue
        
        return None
    
    def parse_product_data(self, html_content: str, url: str, 
                          custom_selectors: Optional[Dict[str, List[str]]] = None) -> Tuple[Optional[str], Optional[float]]:
        """
        Parse product data from HTML content.
        
        Args:
            html_content: HTML content to parse
            url: Source URL (used for selector selection)
            custom_selectors: Custom selectors to use instead of defaults
            
        Returns:
            Tuple of (product_name, price) or (None, None) if extraction fails
        """
        if not html_content or not html_content.strip():
            logger.error("Empty HTML content provided")
            return None, None
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            logger.debug(f"Successfully parsed HTML content ({len(html_content)} chars)")
            
            # Get selectors for this URL
            selectors = self._get_selectors_for_url(url, custom_selectors)
            
            # Extract price
            price = None
            if 'price' in selectors:
                price = self._extract_price_with_selectors(soup, selectors['price'])
            
            # Extract name
            name = None
            if 'name' in selectors:
                name = self._extract_name_with_selectors(soup, selectors['name'])
            
            # Log results
            if price is not None and name:
                logger.info(f"Successfully extracted product data: '{name}' - R$ {price:.2f}")
            elif price is not None:
                logger.warning(f"Extracted price R$ {price:.2f} but no product name")
            elif name:
                logger.warning(f"Extracted product name '{name}' but no price")
            else:
                logger.error("Failed to extract both price and product name")
            
            return name, price
            
        except Exception as e:
            logger.error(f"Error parsing HTML content: {e}")
            return None, None
    
    def validate_extracted_data(self, name: Optional[str], price: Optional[float]) -> Tuple[bool, List[str]]:
        """
        Validate extracted product data.
        
        Args:
            name: Extracted product name
            price: Extracted price
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not name or not name.strip():
            errors.append("Product name is empty or invalid")
        elif len(name.strip()) < 3:
            errors.append("Product name is too short (minimum 3 characters)")
        
        if price is None:
            errors.append("Price is missing")
        elif price <= 0:
            errors.append("Price must be greater than zero")
        elif price > 1000000:  # Sanity check
            errors.append("Price seems unreasonably high (> R$ 1,000,000)")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(f"Data validation failed: {'; '.join(errors)}")
        
        return is_valid, errors
    
    def get_supported_domains(self) -> List[str]:
        """
        Get list of domains with specific selector support.
        
        Returns:
            List of supported domain names
        """
        return list(self.site_selectors.keys())
    
    def debug_selectors(self, html_content: str, url: str) -> Dict[str, List[str]]:
        """
        Debug helper to test selectors against HTML content.
        
        Args:
            html_content: HTML content to test
            url: Source URL
            
        Returns:
            Dictionary with found elements for each selector
        """
        if not html_content:
            return {}
        
        soup = BeautifulSoup(html_content, 'html.parser')
        selectors = self._get_selectors_for_url(url)
        results = {}
        
        for data_type, selector_list in selectors.items():
            results[data_type] = []
            for selector in selector_list:
                try:
                    elements = soup.select(selector)
                    if elements:
                        texts = [self._extract_text_from_element(el) for el in elements[:3]]  # Limit to first 3
                        results[data_type].append({
                            'selector': selector,
                            'found': len(elements),
                            'samples': [t for t in texts if t]
                        })
                except Exception as e:
                    results[data_type].append({
                        'selector': selector,
                        'error': str(e)
                    })
        
        return results