#!/usr/bin/env python
"""
Quick test to verify discount scraper produces correct format.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from datetime import datetime
import pandas as pd
import pytz
from src.models import ProductTile
from scripts.scrape_discounts import process_discount_data

LOCAL_TZ = pytz.timezone("Australia/Sydney")

# Create sample discount products with proper data
sample_products = [
    ProductTile(
        name="Test Product 1 | 500g",
        url="/product/test-product-1-12345",
        price="$5.00",
        price_calc_method="$10.00 per kg Was $8.00 on Nov 2024",
        image_url="/images/test1.jpg",
        was_price="$8.00",
        is_on_special=True,
        special_type="Half Price"
    ),
    ProductTile(
        name="Test Product 2 | 1L",
        url="/product/test-product-2-67890",
        price="$12.50",
        price_calc_method="$12.50 per L Was $15.00 on Oct 2024",
        image_url="/images/test2.jpg",
        was_price="$15.00",
        is_on_special=True,
        special_type="Special"
    ),
    ProductTile(
        name="Test Product 3 | 2kg",
        url="/product/test-product-3-11111",
        price="$20.00",
        price_calc_method="$10.00 per kg",  # No was price - should be filtered out
        image_url="/images/test3.jpg",
        is_on_special=True,
        special_type="Down Down"
    ),
]

print("Processing sample discount products...")
df = process_discount_data(sample_products)

print(f"\nProcessed {len(df)} products (filtered products without valid discounts)")
print(f"\nColumns: {list(df.columns)}")
print("\nExpected columns:")
expected_cols = [
    "product_id", "product_name", "category", "size", 
    "product_url", "product_image_url", "display_price",
    "current_price_aud", "unit_price_aud", "unit_of_measure",
    "previous_price_aud", "pricing_details", "previous_price_date"
]
print(expected_cols)

print("\nSample data:")
print(df.to_string())

# Add timestamps as done in save function
now = datetime.now(tz=LOCAL_TZ)
df["scrape_date"] = now.strftime("%Y-%m-%d")
df["scrape_timestamp"] = now.isoformat()

print("\n\nFinal columns with timestamps:")
print(list(df.columns))

print("\n✓ Format verification complete!")
