#!/usr/bin/env python3
"""Simple test to debug import issues."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing basic imports...")

try:
    import time
    import logging
    from typing import Dict, List, Optional, Tuple
    from dataclasses import dataclass
    from urllib.parse import urlparse
    print("✓ Basic imports successful")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")
    sys.exit(1)

try:
    from services.http_client import HTTPClient, RequestConfig
    from services.html_parser import HTMLParser
    print("✓ Service imports successful")
except Exception as e:
    print(f"❌ Service imports failed: {e}")
    sys.exit(1)

print("Now testing web_scraper import...")

try:
    # Try to import the module first
    import services.web_scraper as ws_module
    print(f"✓ Module imported: {ws_module}")
    print(f"Module attributes: {dir(ws_module)}")
    
    # Try to get the classes
    if hasattr(ws_module, 'WebScraper'):
        print(f"✓ WebScraper found: {ws_module.WebScraper}")
    else:
        print("❌ WebScraper not found in module")
    
    if hasattr(ws_module, 'ScrapingResult'):
        print(f"✓ ScrapingResult found: {ws_module.ScrapingResult}")
    else:
        print("❌ ScrapingResult not found in module")
        
    if hasattr(ws_module, 'ScrapingConfig'):
        print(f"✓ ScrapingConfig found: {ws_module.ScrapingConfig}")
    else:
        print("❌ ScrapingConfig not found in module")

except Exception as e:
    print(f"❌ Module import failed: {e}")
    import traceback
    traceback.print_exc()

print("Testing direct class import...")

try:
    from services.web_scraper import WebScraper, ScrapingResult, ScrapingConfig
    print("✓ Direct class import successful")
    print(f"WebScraper: {WebScraper}")
    print(f"ScrapingResult: {ScrapingResult}")
    print(f"ScrapingConfig: {ScrapingConfig}")
except Exception as e:
    print(f"❌ Direct class import failed: {e}")
    import traceback
    traceback.print_exc()

print("Test completed.")