"""
Unit tests for HTML parser functionality.
"""

import pytest
from unittest.mock import Mock, patch
from services.html_parser import HTMLParser


class TestHTMLParser:
    """Test cases for HTMLParser class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HTMLParser()
    
    def test_init(self):
        """Test HTMLParser initialization."""
        assert self.parser is not None
        assert len(self.parser.site_selectors) > 0
        assert 'amazon.com' in self.parser.site_selectors
        assert 'mercadolivre.com.br' in self.parser.site_selectors
    
    def test_get_domain_from_url(self):
        """Test domain extraction from URLs."""
        test_cases = [
            ('https://www.amazon.com/product/123', 'www.amazon.com'),
            ('http://mercadolivre.com.br/item/456', 'mercadolivre.com.br'),
            ('https://americanas.com.br/produto/789', 'americanas.com.br'),
            ('invalid-url', ''),
            ('', ''),
        ]
        
        for url, expected_domain in test_cases:
            result = self.parser._get_domain_from_url(url)
            assert result == expected_domain
    
    def test_add_site_selectors(self):
        """Test adding custom site selectors."""
        custom_selectors = {
            'price': ['.custom-price', '#price-value'],
            'name': ['.custom-title', 'h1.product-name']
        }
        
        self.parser.add_site_selectors('example.com', custom_selectors)
        
        assert 'example.com' in self.parser.site_selectors
        assert self.parser.site_selectors['example.com'] == custom_selectors
    
    def test_get_selectors_for_url_exact_match(self):
        """Test selector retrieval for exact domain match."""
        url = 'https://www.amazon.com/product/123'
        selectors = self.parser._get_selectors_for_url(url)
        
        # Should get Amazon-specific selectors
        assert 'price' in selectors
        assert 'name' in selectors
        assert '.a-price-whole' in selectors['price']
        assert '#productTitle' in selectors['name']
    
    def test_get_selectors_for_url_partial_match(self):
        """Test selector retrieval for partial domain match."""
        url = 'https://produto.mercadolivre.com.br/item/123'
        selectors = self.parser._get_selectors_for_url(url)
        
        # Should get MercadoLivre-specific selectors
        assert 'price' in selectors
        assert 'name' in selectors
        assert '.andes-money-amount__fraction' in selectors['price']
    
    def test_get_selectors_for_url_generic_fallback(self):
        """Test selector retrieval falls back to generic selectors."""
        url = 'https://unknown-site.com/product/123'
        selectors = self.parser._get_selectors_for_url(url)
        
        # Should get generic selectors
        assert 'price' in selectors
        assert 'name' in selectors
        assert '[class*="price"]' in selectors['price']
        assert 'h1' in selectors['name']
    
    def test_get_selectors_for_url_custom_override(self):
        """Test custom selectors override defaults."""
        custom_selectors = {
            'price': ['.my-price'],
            'name': ['.my-title']
        }
        
        url = 'https://amazon.com/product/123'
        selectors = self.parser._get_selectors_for_url(url, custom_selectors)
        
        assert selectors == custom_selectors
    
    def test_extract_text_from_element(self):
        """Test text extraction from HTML elements."""
        from bs4 import BeautifulSoup
        
        # Test normal text extraction
        html = '<div>  Product Name  </div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        result = self.parser._extract_text_from_element(element)
        assert result == 'Product Name'
        
        # Test with nested elements
        html = '<div>Product <span>Name</span> Here</div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        result = self.parser._extract_text_from_element(element)
        assert result == 'Product Name Here'
        
        # Test with None element
        result = self.parser._extract_text_from_element(None)
        assert result == ''
    
    def test_parse_price_from_text_brazilian_format(self):
        """Test price parsing from Brazilian format text."""
        test_cases = [
            ('R$ 1.234,56', 1234.56),
            ('R$1.234,56', 1234.56),
            ('R$ 99,90', 99.90),
            ('R$15,00', 15.00),
            ('1.234,56', 1234.56),
            ('99,90', 99.90),
        ]
        
        for text, expected_price in test_cases:
            result = self.parser._parse_price_from_text(text)
            assert result == expected_price, f"Failed for text: '{text}'"
    
    def test_parse_price_from_text_us_format(self):
        """Test price parsing from US format text."""
        test_cases = [
            ('1234.56', 1234.56),
            ('99.90', 99.90),
            ('15', 15.0),
            ('1500', 1500.0),
        ]
        
        for text, expected_price in test_cases:
            result = self.parser._parse_price_from_text(text)
            assert result == expected_price, f"Failed for text: '{text}'"
    
    def test_parse_price_from_text_invalid(self):
        """Test price parsing with invalid text."""
        test_cases = [
            '',
            'No price here',
            'abc',
            'R$',
            None,
        ]
        
        for text in test_cases:
            result = self.parser._parse_price_from_text(text)
            assert result is None, f"Should return None for text: '{text}'"
    
    def test_extract_price_with_selectors_success(self):
        """Test successful price extraction with selectors."""
        html = '''
        <div class="price-container">
            <span class="price-value">R$ 199,90</span>
        </div>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.price-value', '.price']
        
        result = self.parser._extract_price_with_selectors(soup, selectors)
        assert result == 199.90
    
    def test_extract_price_with_selectors_fallback(self):
        """Test price extraction with selector fallback."""
        html = '''
        <div class="price-container">
            <span class="price">R$ 299,99</span>
        </div>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.price-value', '.price']  # First selector won't match
        
        result = self.parser._extract_price_with_selectors(soup, selectors)
        assert result == 299.99
    
    def test_extract_price_with_selectors_no_match(self):
        """Test price extraction when no selectors match."""
        html = '<div>No price here</div>'
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.price-value', '.price']
        
        result = self.parser._extract_price_with_selectors(soup, selectors)
        assert result is None
    
    def test_extract_name_with_selectors_success(self):
        """Test successful name extraction with selectors."""
        html = '''
        <div class="product-info">
            <h1 class="product-title">Amazing Product Name</h1>
        </div>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.product-title', 'h1']
        
        result = self.parser._extract_name_with_selectors(soup, selectors)
        assert result == 'Amazing Product Name'
    
    def test_extract_name_with_selectors_cleanup(self):
        """Test name extraction with text cleanup."""
        html = '''
        <h1 class="title">
            Product   Name   
            With   Extra   Spaces
        </h1>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.title']
        
        result = self.parser._extract_name_with_selectors(soup, selectors)
        assert result == 'Product Name With Extra Spaces'
    
    def test_extract_name_with_selectors_length_limit(self):
        """Test name extraction with length limiting."""
        long_name = 'A' * 250  # Very long name
        html = f'<h1 class="title">{long_name}</h1>'
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        selectors = ['.title']
        
        result = self.parser._extract_name_with_selectors(soup, selectors)
        assert len(result) <= 203  # 200 + "..."
        assert result.endswith('...')
    
    def test_parse_product_data_success(self):
        """Test successful product data parsing."""
        html = '''
        <html>
            <body>
                <h1 id="productTitle">Test Product</h1>
                <span class="a-price-whole">99</span>
                <span class="a-price-fraction">90</span>
            </body>
        </html>
        '''
        
        url = 'https://amazon.com/product/123'
        name, price = self.parser.parse_product_data(html, url)
        
        assert name == 'Test Product'
        assert price == 99.0  # Should extract the first price found
    
    def test_parse_product_data_custom_selectors(self):
        """Test product data parsing with custom selectors."""
        html = '''
        <html>
            <body>
                <h2 class="custom-title">Custom Product</h2>
                <div class="custom-price">R$ 149,99</div>
            </body>
        </html>
        '''
        
        custom_selectors = {
            'price': ['.custom-price'],
            'name': ['.custom-title']
        }
        
        url = 'https://example.com/product/123'
        name, price = self.parser.parse_product_data(html, url, custom_selectors)
        
        assert name == 'Custom Product'
        assert price == 149.99
    
    def test_parse_product_data_empty_html(self):
        """Test product data parsing with empty HTML."""
        test_cases = ['', None, '   ']
        
        for html in test_cases:
            url = 'https://example.com/product/123'
            name, price = self.parser.parse_product_data(html, url)
            
            assert name is None
            assert price is None
    
    def test_parse_product_data_invalid_html(self):
        """Test product data parsing with invalid HTML."""
        html = '<invalid>html<content>'
        url = 'https://example.com/product/123'
        
        # Should not crash, but may return None values
        name, price = self.parser.parse_product_data(html, url)
        # Results depend on BeautifulSoup's error handling
    
    def test_validate_extracted_data_valid(self):
        """Test validation of valid extracted data."""
        name = 'Valid Product Name'
        price = 99.99
        
        is_valid, errors = self.parser.validate_extracted_data(name, price)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_extracted_data_invalid_name(self):
        """Test validation with invalid product names."""
        test_cases = [
            (None, 99.99),
            ('', 99.99),
            ('  ', 99.99),
            ('AB', 99.99),  # Too short
        ]
        
        for name, price in test_cases:
            is_valid, errors = self.parser.validate_extracted_data(name, price)
            
            assert is_valid is False
            assert len(errors) > 0
            assert any('name' in error.lower() for error in errors)
    
    def test_validate_extracted_data_invalid_price(self):
        """Test validation with invalid prices."""
        test_cases = [
            ('Valid Name', None),
            ('Valid Name', 0),
            ('Valid Name', -10.50),
            ('Valid Name', 2000000),  # Too high
        ]
        
        for name, price in test_cases:
            is_valid, errors = self.parser.validate_extracted_data(name, price)
            
            assert is_valid is False
            assert len(errors) > 0
            assert any('price' in error.lower() for error in errors)
    
    def test_get_supported_domains(self):
        """Test getting list of supported domains."""
        domains = self.parser.get_supported_domains()
        
        assert isinstance(domains, list)
        assert len(domains) > 0
        assert 'amazon.com' in domains
        assert 'mercadolivre.com.br' in domains
    
    def test_debug_selectors(self):
        """Test debug functionality for selectors."""
        html = '''
        <html>
            <body>
                <h1 id="productTitle">Test Product</h1>
                <span class="a-price-whole">99</span>
                <div class="not-found">Other content</div>
            </body>
        </html>
        '''
        
        url = 'https://amazon.com/product/123'
        results = self.parser.debug_selectors(html, url)
        
        assert 'price' in results
        assert 'name' in results
        assert isinstance(results['price'], list)
        assert isinstance(results['name'], list)
        
        # Should find some matches
        price_results = results['price']
        name_results = results['name']
        
        # Check that we have results for selectors that should match
        price_found = any(r.get('found', 0) > 0 for r in price_results if 'error' not in r)
        name_found = any(r.get('found', 0) > 0 for r in name_results if 'error' not in r)
        
        assert price_found or name_found  # At least one should be found
    
    def test_debug_selectors_empty_html(self):
        """Test debug functionality with empty HTML."""
        html = ''
        url = 'https://example.com/product/123'
        
        results = self.parser.debug_selectors(html, url)
        assert results == {}


# Mock HTML responses for integration-like tests
MOCK_HTML_RESPONSES = {
    'amazon_success': '''
    <html>
        <head><title>Amazon Product</title></head>
        <body>
            <h1 id="productTitle">Amazon Echo Dot (4th Gen)</h1>
            <span class="a-price-whole">199</span>
            <span class="a-price-fraction">90</span>
        </body>
    </html>
    ''',
    
    'mercadolivre_success': '''
    <html>
        <head><title>MercadoLivre Product</title></head>
        <body>
            <h1 class="ui-pdp-title">Smartphone Samsung Galaxy</h1>
            <span class="andes-money-amount__fraction">899</span>
            <span class="andes-money-amount__cents">99</span>
        </body>
    </html>
    ''',
    
    'generic_success': '''
    <html>
        <head><title>Generic Store</title></head>
        <body>
            <h1>Generic Product Name</h1>
            <div class="price">R$ 49,90</div>
        </body>
    </html>
    ''',
    
    'no_price': '''
    <html>
        <body>
            <h1>Product Without Price</h1>
            <div>Some other content</div>
        </body>
    </html>
    ''',
    
    'no_name': '''
    <html>
        <body>
            <div class="price">R$ 99,99</div>
            <div>Some content without title</div>
        </body>
    </html>
    ''',
    
    'malformed': '''
    <html>
        <body>
            <h1>Broken Product
            <div class="price">R$ 
        </body>
    '''
}


class TestHTMLParserIntegration:
    """Integration-like tests with mock HTML responses."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HTMLParser()
    
    def test_parse_amazon_product(self):
        """Test parsing Amazon product page."""
        html = MOCK_HTML_RESPONSES['amazon_success']
        url = 'https://amazon.com/product/123'
        
        name, price = self.parser.parse_product_data(html, url)
        
        assert name == 'Amazon Echo Dot (4th Gen)'
        assert price == 199.0
    
    def test_parse_mercadolivre_product(self):
        """Test parsing MercadoLivre product page."""
        html = MOCK_HTML_RESPONSES['mercadolivre_success']
        url = 'https://mercadolivre.com.br/item/123'
        
        name, price = self.parser.parse_product_data(html, url)
        
        assert name == 'Smartphone Samsung Galaxy'
        assert price == 899.0
    
    def test_parse_generic_product(self):
        """Test parsing generic e-commerce product page."""
        html = MOCK_HTML_RESPONSES['generic_success']
        url = 'https://unknown-store.com/product/123'
        
        name, price = self.parser.parse_product_data(html, url)
        
        assert name == 'Generic Product Name'
        assert price == 49.90
    
    def test_parse_product_no_price(self):
        """Test parsing product page without price."""
        html = MOCK_HTML_RESPONSES['no_price']
        url = 'https://example.com/product/123'
        
        name, price = self.parser.parse_product_data(html, url)
        
        assert name == 'Product Without Price'
        assert price is None
    
    def test_parse_product_no_name(self):
        """Test parsing product page without name."""
        html = MOCK_HTML_RESPONSES['no_name']
        url = 'https://example.com/product/123'
        
        name, price = self.parser.parse_product_data(html, url)
        
        assert name is None
        assert price == 99.99
    
    def test_parse_malformed_html(self):
        """Test parsing malformed HTML."""
        html = MOCK_HTML_RESPONSES['malformed']
        url = 'https://example.com/product/123'
        
        # Should not crash
        name, price = self.parser.parse_product_data(html, url)
        
        # Results may vary, but should not raise exception
        assert isinstance(name, (str, type(None)))
        assert isinstance(price, (float, type(None)))


if __name__ == '__main__':
    pytest.main([__file__])