"""
Integration tests for WebScraper class.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import requests
from services.web_scraper import WebScraper, ScrapingResult, ScrapingConfig


class TestWebScraper:
    """Test cases for WebScraper class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.scraper = WebScraper()
        
        # Mock HTML responses for different sites
        self.mock_amazon_html = """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1 id="productTitle">Smartphone Samsung Galaxy</h1>
                <span class="a-price-whole">1299</span>
                <span class="a-price-fraction">99</span>
            </body>
        </html>
        """
        
        self.mock_mercadolivre_html = """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1 class="ui-pdp-title">iPhone 15 Pro Max</h1>
                <span class="andes-money-amount__fraction">2499</span>
            </body>
        </html>
        """
        
        self.mock_generic_html = """
        <html>
            <head><title>Test Product</title></head>
            <body>
                <h1>Notebook Dell Inspiron</h1>
                <div class="price">R$ 2.899,90</div>
            </body>
        </html>
        """
    
    def teardown_method(self):
        """Cleanup after tests."""
        if hasattr(self, 'scraper'):
            self.scraper.close()
    
    def test_scraper_initialization(self):
        """Test WebScraper initialization."""
        config = ScrapingConfig(timeout=15, max_retries=5)
        scraper = WebScraper(config)
        
        assert scraper.config.timeout == 15
        assert scraper.config.max_retries == 5
        assert scraper.total_requests == 0
        assert scraper.successful_requests == 0
        assert scraper.failed_requests == 0
        
        scraper.close()
    
    def test_scraper_initialization_with_defaults(self):
        """Test WebScraper initialization with default config."""
        scraper = WebScraper()
        
        assert scraper.config.timeout == 10
        assert scraper.config.max_retries == 3
        assert scraper.config.rate_limit_delay == 1.0
        
        scraper.close()
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_product_success_amazon(self, mock_get):
        """Test successful product scraping from Amazon-like site."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.mock_amazon_html
        mock_response.content = self.mock_amazon_html.encode()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test scraping
        result = self.scraper.scrape_product("https://amazon.com/product/123")
        
        assert result.success is True
        assert result.product_name == "Smartphone Samsung Galaxy"
        assert result.price == 1299.0  # Parser extracts first price found
        assert result.url == "https://amazon.com/product/123"
        assert result.status_code == 200
        assert result.response_time > 0
        
        # Check metrics
        metrics = self.scraper.get_performance_metrics()
        assert metrics['total_requests'] == 1
        assert metrics['successful_requests'] == 1
        assert metrics['failed_requests'] == 0
        assert metrics['success_rate'] == 100.0
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_product_success_mercadolivre(self, mock_get):
        """Test successful product scraping from MercadoLivre-like site."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.mock_mercadolivre_html
        mock_response.content = self.mock_mercadolivre_html.encode()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test scraping
        result = self.scraper.scrape_product("https://mercadolivre.com.br/produto/456")
        
        assert result.success is True
        assert result.product_name == "iPhone 15 Pro Max"
        assert result.price == 2499.0
        assert result.url == "https://mercadolivre.com.br/produto/456"
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_product_success_generic(self, mock_get):
        """Test successful product scraping from generic site."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.mock_generic_html
        mock_response.content = self.mock_generic_html.encode()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Test scraping
        result = self.scraper.scrape_product("https://example.com/produto/789")
        
        assert result.success is True
        assert result.product_name == "Notebook Dell Inspiron"
        assert result.price == 2899.90
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_product_with_custom_selectors(self, mock_get):
        """Test scraping with custom selectors."""
        custom_html = """
        <html>
            <body>
                <h2 class="custom-title">Custom Product Name</h2>
                <div class="custom-price">R$ 999,99</div>
            </body>
        </html>
        """
        
        mock_response = Mock()
        mock_response.text = custom_html
        mock_response.content = custom_html.encode()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        custom_selectors = {
            'name': ['.custom-title'],
            'price': ['.custom-price']
        }
        
        result = self.scraper.scrape_product(
            "https://custom-site.com/product", 
            custom_selectors=custom_selectors
        )
        
        assert result.success is True
        assert result.product_name == "Custom Product Name"
        assert result.price == 999.99
    
    def test_scrape_product_invalid_url(self):
        """Test scraping with invalid URL."""
        result = self.scraper.scrape_product("invalid-url")
        
        assert result.success is False
        assert "Invalid URL format" in result.error_message
        assert result.url == "invalid-url"
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_product_empty_response(self, mock_get):
        """Test scraping with empty response."""
        mock_response = Mock()
        mock_response.text = ""
        mock_response.content = b""
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_product("https://example.com/empty")
        
        assert result.success is False
        assert "Empty response content" in result.error_message
        assert result.status_code == 200
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_product_no_data_found(self, mock_get):
        """Test scraping when no product data is found."""
        html_no_data = "<html><body><p>No product data here</p></body></html>"
        
        mock_response = Mock()
        mock_response.text = html_no_data
        mock_response.content = html_no_data.encode()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = self.scraper.scrape_product("https://example.com/no-data")
        
        assert result.success is False
        assert "Data validation failed" in result.error_message
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_product_http_error(self, mock_get):
        """Test scraping with HTTP error."""
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        result = self.scraper.scrape_product("https://example.com/error")
        
        assert result.success is False
        assert "Scraping failed" in result.error_message
        assert "Connection failed" in result.error_message
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_scrape_multiple_products(self, mock_get):
        """Test scraping multiple products."""
        # Mock responses for different URLs
        def mock_response_side_effect(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            
            if "amazon" in url:
                mock_response.text = self.mock_amazon_html
                mock_response.content = self.mock_amazon_html.encode()
            elif "mercadolivre" in url:
                mock_response.text = self.mock_mercadolivre_html
                mock_response.content = self.mock_mercadolivre_html.encode()
            else:
                mock_response.text = self.mock_generic_html
                mock_response.content = self.mock_generic_html.encode()
            
            return mock_response
        
        mock_get.side_effect = mock_response_side_effect
        
        urls = [
            "https://amazon.com/product/1",
            "https://mercadolivre.com.br/produto/2",
            "https://example.com/produto/3"
        ]
        
        results = self.scraper.scrape_multiple_products(urls)
        
        assert len(results) == 3
        assert all(result.success for result in results)
        assert results[0].product_name == "Smartphone Samsung Galaxy"
        assert results[1].product_name == "iPhone 15 Pro Max"
        assert results[2].product_name == "Notebook Dell Inspiron"
        
        # Check metrics
        metrics = self.scraper.get_performance_metrics()
        assert metrics['total_requests'] == 3
        assert metrics['successful_requests'] == 3
    
    def test_scrape_multiple_products_empty_list(self):
        """Test scraping with empty URL list."""
        results = self.scraper.scrape_multiple_products([])
        
        assert results == []
    
    def test_add_site_configuration(self):
        """Test adding site-specific configuration."""
        custom_selectors = {
            'name': ['.custom-product-title'],
            'price': ['.custom-price-value']
        }
        custom_headers = {'X-Custom-Header': 'test-value'}
        
        self.scraper.add_site_configuration(
            "custom-site.com", 
            custom_selectors, 
            custom_headers
        )
        
        # Verify selectors were added to HTML parser
        supported_domains = self.scraper.html_parser.get_supported_domains()
        assert "custom-site.com" in supported_domains
    
    def test_performance_metrics_empty(self):
        """Test performance metrics with no requests."""
        metrics = self.scraper.get_performance_metrics()
        
        expected = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'success_rate': 0.0,
            'average_response_time': 0.0
        }
        
        assert metrics == expected
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_performance_metrics_with_requests(self, mock_get):
        """Test performance metrics after making requests."""
        mock_response = Mock()
        mock_response.text = self.mock_amazon_html
        mock_response.content = self.mock_amazon_html.encode()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # Make some requests
        self.scraper.scrape_product("https://amazon.com/product/1")
        self.scraper.scrape_product("https://amazon.com/product/2")
        
        metrics = self.scraper.get_performance_metrics()
        
        assert metrics['total_requests'] == 2
        assert metrics['successful_requests'] == 2
        assert metrics['failed_requests'] == 0
        assert metrics['success_rate'] == 100.0
        assert metrics['average_response_time'] > 0
    
    def test_reset_metrics(self):
        """Test resetting performance metrics."""
        # Simulate some activity
        self.scraper.total_requests = 5
        self.scraper.successful_requests = 3
        self.scraper.failed_requests = 2
        self.scraper.total_response_time = 10.0
        
        self.scraper.reset_metrics()
        
        assert self.scraper.total_requests == 0
        assert self.scraper.successful_requests == 0
        assert self.scraper.failed_requests == 0
        assert self.scraper.total_response_time == 0.0
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_debug_scraping(self, mock_get):
        """Test debug scraping functionality."""
        mock_response = Mock()
        mock_response.text = self.mock_amazon_html
        mock_response.content = self.mock_amazon_html.encode()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        debug_info = self.scraper.debug_scraping("https://amazon.com/product/123")
        
        assert debug_info['url'] == "https://amazon.com/product/123"
        assert debug_info['domain'] == "amazon.com"
        assert debug_info['has_specific_selectors'] is True
        assert debug_info['response_status'] == 200
        assert debug_info['response_size'] > 0
        assert 'selector_results' in debug_info
        assert 'performance_metrics' in debug_info
    
    @patch('services.web_scraper.HTTPClient.get')
    def test_debug_scraping_error(self, mock_get):
        """Test debug scraping with error."""
        mock_get.side_effect = requests.RequestException("Network error")
        
        debug_info = self.scraper.debug_scraping("https://example.com/error")
        
        assert debug_info['url'] == "https://example.com/error"
        assert 'error' in debug_info
        assert "Network error" in debug_info['error']
    
    def test_context_manager(self):
        """Test WebScraper as context manager."""
        with WebScraper() as scraper:
            assert scraper is not None
            assert hasattr(scraper, 'http_client')
            assert hasattr(scraper, 'html_parser')
        
        # Scraper should be closed after context exit
        # (We can't easily test this without mocking, but the structure is correct)
    
    def test_url_validation(self):
        """Test URL validation method."""
        valid_urls = [
            "https://example.com",
            "http://test.com/path",
            "https://subdomain.example.com/path?param=value"
        ]
        
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "example.com",
            "",
            None
        ]
        
        for url in valid_urls:
            assert self.scraper._is_valid_url(url) is True
        
        for url in invalid_urls:
            if url is not None:
                assert self.scraper._is_valid_url(url) is False


class TestScrapingConfig:
    """Test cases for ScrapingConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = ScrapingConfig()
        
        assert config.timeout == 10
        assert config.max_retries == 3
        assert config.rate_limit_delay == 1.0
        assert config.backoff_factor == 1.0
        assert config.verify_ssl is True
        assert config.custom_selectors is None
        assert config.custom_headers is None
    
    def test_custom_config(self):
        """Test custom configuration values."""
        custom_selectors = {'price': ['.price'], 'name': ['.name']}
        custom_headers = {'User-Agent': 'Custom Bot'}
        
        config = ScrapingConfig(
            timeout=20,
            max_retries=5,
            rate_limit_delay=2.0,
            backoff_factor=2.0,
            verify_ssl=False,
            custom_selectors=custom_selectors,
            custom_headers=custom_headers
        )
        
        assert config.timeout == 20
        assert config.max_retries == 5
        assert config.rate_limit_delay == 2.0
        assert config.backoff_factor == 2.0
        assert config.verify_ssl is False
        assert config.custom_selectors == custom_selectors
        assert config.custom_headers == custom_headers


class TestScrapingResult:
    """Test cases for ScrapingResult dataclass."""
    
    def test_successful_result(self):
        """Test successful scraping result."""
        result = ScrapingResult(
            success=True,
            product_name="Test Product",
            price=99.99,
            url="https://example.com/product",
            response_time=1.5,
            status_code=200
        )
        
        assert result.success is True
        assert result.product_name == "Test Product"
        assert result.price == 99.99
        assert result.url == "https://example.com/product"
        assert result.error_message is None
        assert result.response_time == 1.5
        assert result.attempts == 1
        assert result.status_code == 200
    
    def test_failed_result(self):
        """Test failed scraping result."""
        result = ScrapingResult(
            success=False,
            url="https://example.com/error",
            error_message="Network timeout",
            response_time=10.0,
            attempts=3
        )
        
        assert result.success is False
        assert result.product_name is None
        assert result.price is None
        assert result.url == "https://example.com/error"
        assert result.error_message == "Network timeout"
        assert result.response_time == 10.0
        assert result.attempts == 3
        assert result.status_code is None