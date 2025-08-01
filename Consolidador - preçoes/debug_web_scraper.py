#!/usr/bin/env python3
"""Debug script to find the issue in web_scraper.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Attempting to execute web_scraper.py line by line...")

try:
    # Read the file content
    with open('services/web_scraper.py', 'r') as f:
        content = f.read()
    
    print(f"File content length: {len(content)} characters")
    print("First 200 characters:")
    print(content[:200])
    print("...")
    
    # Try to compile the code
    print("Compiling code...")
    compiled_code = compile(content, 'services/web_scraper.py', 'exec')
    print("✓ Code compiled successfully")
    
    # Try to execute the code
    print("Executing code...")
    namespace = {}
    exec(compiled_code, namespace)
    print("✓ Code executed successfully")
    
    # Check what was defined
    print("Defined names:")
    for name in sorted(namespace.keys()):
        if not name.startswith('__'):
            print(f"  {name}: {type(namespace[name])}")
    
    # Check for our classes
    if 'WebScraper' in namespace:
        print(f"✓ WebScraper found: {namespace['WebScraper']}")
    else:
        print("❌ WebScraper not found")
        
    if 'ScrapingResult' in namespace:
        print(f"✓ ScrapingResult found: {namespace['ScrapingResult']}")
    else:
        print("❌ ScrapingResult not found")
        
    if 'ScrapingConfig' in namespace:
        print(f"✓ ScrapingConfig found: {namespace['ScrapingConfig']}")
    else:
        print("❌ ScrapingConfig not found")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("Debug completed.")