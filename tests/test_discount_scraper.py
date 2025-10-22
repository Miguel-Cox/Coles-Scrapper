#!/usr/bin/env python3
"""
Quick test script for the discount scraper functionality.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.fetcher import ColesPageFetcher
from scripts.scrape_discounts import SpecialsQuery, extract_discount_products

def test_discount_scraper():
    """Test the discount scraper with a single page"""
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }
    
    fetcher = ColesPageFetcher(headers=headers)
    
    # Test half-price specials first
    print("Testing half-price specials...")
    query = SpecialsQuery(filter_type="halfprice", page=1)
    print(f"URL: {query.url}")
    
    try:
        products = extract_discount_products(fetcher, query)
        
        print(f"\nFound {len(products)} discount products")
        
        # Show details of first few products
        for i, product in enumerate(products[:3]):  # Show first 3 products
            print(f"\n--- Product {i+1} ---")
            print(f"Name: {product.name}")
            print(f"Price: {product.price}")
            print(f"Was Price: {product.was_price}")
            print(f"Special Type: {product.special_type}")
            print(f"Discount %: {product.discount_percentage}")
            print(f"On Special: {product.is_on_special}")
            print(f"URL: {product.url}")
            
        return len(products) > 0
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = test_discount_scraper()
    if success:
        print("\n✅ Test passed! Discount scraper is working.")
    else:
        print("\n❌ Test failed. Check the error messages above.")