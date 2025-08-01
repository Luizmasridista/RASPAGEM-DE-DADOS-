"""
Main web scraper class that integrates HTTP client and HTML parser.
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse

from services.http_client import HTTPClient, RequestConfig
from services.html_parser import HTMLParser

logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    """Result of a scraping operation."""
    success: bool
    product_name: Optional[str] = None
    price: Optional[float] = None
    url: str = ""
    error_message: Optional[str] = None
    response_time: float = 0.0
    attempts: int = 1
    status_code: Optional[int] = None


@dataclass
class ScrapingConfig:
    """Configuration for web scraping operations."""
    timeout: int = 10
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    backoff_factor: float = 1.0
    verify_ssl: bool = True
    custom_selectors: Optional[Dict[str, List[str]]] = None
    custom_headers: Optional[Dict[str, str]] = None


class WebScraper:
    """Main web scraper class that integrates HTTP client and HTML parser."""
    
    def __init__(self, config: Optional[ScrapingConfig] = None):
        """Initialize web scraper with configuration."""
        self.config = config or ScrapingConfig()
        
        # Initialize HTTP client
        http_config = RequestConfig(
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            rate_limit_delay=self.config.rate_limit_delay,
            verify_ssl=self.config.verify_ssl
        )
        self.http_client = HTTPClient(http_config)
        
        # Initialize HTML parser
        self.html_parser = HTMLParser()
        
        # Performance tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        
        logger.info(f"WebScraper initialized with timeout={self.config.timeout}s")
    
    def scrape_product(self, url: str, custom_selectors: Optional[Dict[str, List[str]]] = None) -> ScrapingResult:
        """Scrape product data from a URL."""
        start_time = time.time()
        self.total_requests += 1
        
        try:
            if not self._is_valid_url(url):
                return ScrapingResult(
                    success=False,
                    url=url,
                    error_message="Invalid URL format",
                    response_time=time.time() - start_time
                )
            
            response = self.http_client.get(url)
            
            if not response.content:
                return ScrapingResult(
                    success=False,
                    url=url,
                    error_message="Empty response content",
                    status_code=response.status_code,
                    response_time=time.time() - start_time
                )
            
            # Use custom selectors if provided, otherwise use config selectors
            selectors_to_use = custom_selectors or self.config.custom_selectors
            
            product_name, price = self.html_parser.parse_product_data(
                response.text, url, selectors_to_use
            )
            
            is_valid, validation_errors = self.html_parser.validate_extracted_data(product_name, price)
            
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            if is_valid:
                self.successful_requests += 1
                return ScrapingResult(
                    success=True,
                    product_name=product_name,
                    price=price,
                    url=url,
                    response_time=response_time,
                    status_code=response.status_code
                )
            else:
                self.failed_requests += 1
                return ScrapingResult(
                    success=False,
                    product_name=product_name,
                    price=price,
                    url=url,
                    error_message=f"Data validation failed: {'; '.join(validation_errors)}",
                    response_time=response_time,
                    status_code=response.status_code
                )
        
        except Exception as e:
            self.failed_requests += 1
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            return ScrapingResult(
                success=False,
                url=url,
                error_message=f"Scraping failed: {str(e)}",
                response_time=response_time
            )
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
        except Exception:
            return False
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics for scraping operations."""
        if self.total_requests == 0:
            return {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'success_rate': 0.0,
                'average_response_time': 0.0
            }
        
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / self.total_requests) * 100,
            'average_response_time': self.total_response_time / self.total_requests
        }
    
    def reset_metrics(self) -> None:
        """Reset performance metrics counters."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_response_time = 0.0
        logger.info("Performance metrics reset")
    
    def scrape_multiple_products(self, urls: List[str]) -> List[ScrapingResult]:
        """
        Scrape multiple products from a list of URLs.
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of ScrapingResult objects
        """
        if not urls:
            return []
        
        results = []
        for url in urls:
            result = self.scrape_product(url)
            results.append(result)
        
        logger.info(f"Scraped {len(urls)} products: {self.successful_requests} successful, {self.failed_requests} failed")
        return results
    
    def debug_scraping(self, url: str) -> Dict[str, any]:
        """
        Debug scraping functionality for a URL.
        
        Args:
            url: URL to debug
            
        Returns:
            Dictionary with debug information
        """
        try:
            domain = self._get_domain_from_url(url)
            
            # Check if we have specific selectors for this domain
            has_specific_selectors = domain in self.html_parser.site_selectors
            
            # Make the request
            response = self.http_client.get(url)
            
            # Get selector debug info
            selector_results = self.html_parser.debug_selectors(response.text, url)
            
            return {
                'url': url,
                'domain': domain,
                'has_specific_selectors': has_specific_selectors,
                'response_status': response.status_code,
                'response_size': len(response.text),
                'selector_results': selector_results,
                'performance_metrics': self.get_performance_metrics()
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e)
            }
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""
    
    def add_site_configuration(self, domain: str, selectors: Dict[str, List[str]], 
                              headers: Optional[Dict[str, str]] = None) -> None:
        """Add site-specific configuration for selectors and headers."""
        self.html_parser.add_site_selectors(domain, selectors)
        
        if headers:
            self.http_client.set_domain_headers(domain, headers)
        
        logger.info(f"Added site configuration for domain: {domain}")
    
    def close(self) -> None:
        """Close the scraper and clean up resources."""
        if self.http_client:
            self.http_client.close()
        
        metrics = self.get_performance_metrics()
        logger.info(f"WebScraper closing - Final metrics: {metrics}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


if __name__ == "__main__":
    print("WebScraper module loaded successfully")
    print(f"WebScraper class: {WebScraper}")
    print(f"ScrapingResult class: {ScrapingResult}")
    print(f"ScrapingConfig class: {ScrapingConfig}")