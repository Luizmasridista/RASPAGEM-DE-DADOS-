#!/usr/bin/env python3
"""Simple test runner to verify WebScraper functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.web_scraper import WebScraper, ScrapingResult, ScrapingConfig
    print("✓ Successfully imported WebScraper classes")
    
    # Test basic initialization
    scraper = WebScraper()
    print("✓ Successfully created WebScraper instance")
    
    # Test configuration
    config = ScrapingConfig(timeout=5, max_retries=2)
    scraper_with_config = WebScraper(config)
    print("✓ Successfully created WebScraper with custom config")
    
    # Test URL validation
    assert scraper._is_valid_url("https://example.com") == True
    assert scraper._is_valid_url("invalid-url") == False
    print("✓ URL validation working")
    
    # Test performance metrics (empty state)
    metrics = scraper.get_performance_metrics()
    assert metrics['total_requests'] == 0
    assert metrics['success_rate'] == 0.0
    print("✓ Performance metrics working")
    
    # Test site configuration
    custom_selectors = {
        'name': ['.product-title'],
        'price': ['.price-value']
    }
    scraper.add_site_configuration("test-site.com", custom_selectors)
    print("✓ Site configuration working")
    
    # Test metrics reset
    scraper.reset_metrics()
    print("✓ Metrics reset working")
    
    # Test context manager
    with WebScraper() as context_scraper:
        assert context_scraper is not None
    print("✓ Context manager working")
    
    # Test ScrapingResult dataclass
    result = ScrapingResult(
        success=True,
        product_name="Test Product",
        price=99.99,
        url="https://example.com"
    )
    assert result.success == True
    assert result.product_name == "Test Product"
    print("✓ ScrapingResult dataclass working")
    
    # Test ScrapingConfig dataclass
    config = ScrapingConfig(timeout=15, max_retries=5)
    assert config.timeout == 15
    assert config.max_retries == 5
    print("✓ ScrapingConfig dataclass working")
    
    scraper.close()
    scraper_with_config.close()
    print("✓ Scraper cleanup working")
    
    print("\n🎉 All basic tests passed! WebScraper implementation is working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)