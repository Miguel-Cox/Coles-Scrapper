"""
Script to scrape all products for given categories on the Coles website.
"""

import json
import os

from src.fetcher import ColesPageFetcher
from src.scrapers import ColesProductTileScraper

DEST_DIR = "./data/raw"

# modify this to scrape products from other categories
TARGET_CATEGORY = "fruit-vegetables"


def dump_products(category, products):
    os.makedirs(DEST_DIR, exist_ok=True)
    products_file = os.path.join(DEST_DIR, f"{category}-products.json")
    with open(products_file, "w") as dst:
        products_json = [product.dict() for product in products]
        json.dump(products_json, dst)


if __name__ == "__main__":

    fetcher = ColesPageFetcher()

    category, page_num = TARGET_CATEGORY, 1
    products = []
    while True:
        url = f"https://www.coles.com.au/browse/{category}?page={page_num}"

        try:
            response = fetcher.get(url)
            scraper = ColesProductTileScraper(response.content)
            found_products = scraper.get_all_products()
        except Exception as e:
            print(
                "Error extracting products on page %d for category '%s': %s",
                page_num,
                category,
                e,
            )
            found_products = []

        print(f"({category}) {len(found_products)} products found on page {page_num}")

        if found_products:
            products.extend(found_products)
            page_num += 1
        else:
            break

    if products:
        dump_products(category, products=products)
