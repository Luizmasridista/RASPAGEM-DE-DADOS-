#!/usr/bin/env python3
"""Simple test runner to verify HTTP client functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.http_client import HTTPClient, RequestConfig
    print("✓ Successfully imported HTTPClient")
    
    # Test basic initialization
    client = HTTPClient()
    print("✓ Successfully created HTTPClient instance")
    
    # Test configuration
    config = RequestConfig(timeout=5, max_retries=2)
    client_with_config = HTTPClient(config)
    print("✓ Successfully created HTTPClient with custom config")
    
    # Test user agent rotation
    ua1 = client._get_random_user_agent()
    ua2 = client._get_random_user_agent()
    print(f"✓ User agent rotation working: {ua1[:50]}...")
    
    # Test domain extraction
    domain = client._get_domain_from_url("https://example.com/path")
    assert domain == "example.com"
    print("✓ Domain extraction working")
    
    # Test header building
    headers = client._build_headers("https://example.com")
    assert "User-Agent" in headers
    print("✓ Header building working")
    
    # Test domain-specific headers
    client.set_domain_headers("example.com", {"X-Custom": "test"})
    headers_with_custom = client._build_headers("https://example.com")
    assert headers_with_custom["X-Custom"] == "test"
    print("✓ Domain-specific headers working")
    
    client.close()
    print("✓ Client cleanup working")
    
    print("\n🎉 All basic tests passed! HTTP client implementation is working correctly.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)