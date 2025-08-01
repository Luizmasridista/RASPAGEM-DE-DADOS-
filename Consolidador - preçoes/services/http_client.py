"""
HTTP client with retry mechanism, user-agent rotation, and rate limiting.
"""

import time
import random
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(InsecureRequestWarning)

logger = logging.getLogger(__name__)


@dataclass
class RequestConfig:
    """Configuration for HTTP requests."""
    timeout: int = 10
    max_retries: int = 3
    backoff_factor: float = 1.0
    rate_limit_delay: float = 1.0
    verify_ssl: bool = True
    follow_redirects: bool = True


class HTTPClient:
    """
    HTTP client with retry mechanism, user-agent rotation, and rate limiting.
    
    Features:
    - Exponential backoff retry mechanism
    - User-agent rotation to avoid detection
    - Rate limiting between requests
    - Custom headers per domain
    - Timeout handling
    - SSL verification control
    """
    
    # Common user agents to rotate through
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
    ]
    
    def __init__(self, config: Optional[RequestConfig] = None):
        """
        Initialize HTTP client with configuration.
        
        Args:
            config: Request configuration settings
        """
        self.config = config or RequestConfig()
        self.session = self._create_session()
        self.last_request_time = 0.0
        self.domain_headers: Dict[str, Dict[str, str]] = {}
        
        logger.info(f"HTTPClient initialized with timeout={self.config.timeout}s, "
                   f"max_retries={self.config.max_retries}, "
                   f"rate_limit={self.config.rate_limit_delay}s")
    
    def _create_session(self) -> requests.Session:
        """Create and configure requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent from the list."""
        return random.choice(self.USER_AGENTS)
    
    def _apply_rate_limiting(self) -> None:
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.config.rate_limit_delay:
            sleep_time = self.config.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc.lower()
        except Exception:
            return ""
    
    def set_domain_headers(self, domain: str, headers: Dict[str, str]) -> None:
        """
        Set custom headers for a specific domain.
        
        Args:
            domain: Domain name (e.g., 'amazon.com')
            headers: Dictionary of headers to set for this domain
        """
        self.domain_headers[domain.lower()] = headers
        logger.info(f"Set custom headers for domain: {domain}")
    
    def _build_headers(self, url: str, custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Build headers for the request including user-agent rotation and domain-specific headers.
        
        Args:
            url: Target URL
            custom_headers: Additional custom headers
            
        Returns:
            Dictionary of headers to use
        """
        headers = {
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Add domain-specific headers
        domain = self._get_domain_from_url(url)
        if domain in self.domain_headers:
            headers.update(self.domain_headers[domain])
            logger.debug(f"Applied domain-specific headers for {domain}")
        
        # Add custom headers
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        Perform GET request with retry mechanism and rate limiting.
        
        Args:
            url: Target URL
            headers: Additional headers
            **kwargs: Additional arguments for requests.get
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
        return self._make_request('GET', url, headers=headers, **kwargs)
    
    def post(self, url: str, data: Optional[Any] = None, json: Optional[Any] = None, 
             headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        Perform POST request with retry mechanism and rate limiting.
        
        Args:
            url: Target URL
            data: Form data to send
            json: JSON data to send
            headers: Additional headers
            **kwargs: Additional arguments for requests.post
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
        return self._make_request('POST', url, data=data, json=json, headers=headers, **kwargs)
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with full error handling and logging.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Target URL
            **kwargs: Additional arguments for the request
            
        Returns:
            Response object
            
        Raises:
            requests.RequestException: If request fails after all retries
        """
        # Apply rate limiting
        self._apply_rate_limiting()
        
        # Build headers
        custom_headers = kwargs.pop('headers', None)
        headers = self._build_headers(url, custom_headers)
        
        # Set default parameters
        kwargs.setdefault('timeout', self.config.timeout)
        kwargs.setdefault('verify', self.config.verify_ssl)
        kwargs.setdefault('allow_redirects', self.config.follow_redirects)
        kwargs['headers'] = headers
        
        start_time = time.time()
        attempt = 0
        last_exception = None
        
        while attempt <= self.config.max_retries:
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = self.session.request(method, url, **kwargs)
                
                # Log successful request
                elapsed = time.time() - start_time
                logger.info(f"Request successful: {method} {url} -> {response.status_code} "
                           f"({elapsed:.2f}s, attempt {attempt + 1})")
                
                # Raise for HTTP error status codes
                response.raise_for_status()
                
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Request timeout for {url} (attempt {attempt + 1}): {e}")
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error for {url} (attempt {attempt + 1}): {e}")
                
            except requests.exceptions.HTTPError as e:
                last_exception = e
                if e.response.status_code in [429, 503, 504]:
                    # Retry on rate limiting or server errors
                    logger.warning(f"HTTP error {e.response.status_code} for {url} (attempt {attempt + 1})")
                else:
                    # Don't retry on client errors (4xx except 429)
                    logger.error(f"HTTP error {e.response.status_code} for {url}: {e}")
                    raise
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request error for {url} (attempt {attempt + 1}): {e}")
            
            attempt += 1
            
            # Wait before retry with exponential backoff
            if attempt <= self.config.max_retries:
                wait_time = self.config.backoff_factor * (2 ** (attempt - 1))
                logger.debug(f"Waiting {wait_time:.2f}s before retry")
                time.sleep(wait_time)
        
        # All retries exhausted
        elapsed = time.time() - start_time
        logger.error(f"Request failed after {self.config.max_retries + 1} attempts "
                    f"({elapsed:.2f}s): {method} {url}")
        
        if last_exception:
            raise last_exception
        else:
            raise requests.RequestException(f"Request failed after {self.config.max_retries + 1} attempts")
    
    def close(self) -> None:
        """Close the session and clean up resources."""
        if self.session:
            self.session.close()
            logger.info("HTTPClient session closed")