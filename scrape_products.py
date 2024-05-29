"""
Script to scrape all products for given categories on the Coles website.
"""

import os
import json

from utils.webdriver import initialize_driver
from pages.products import ProductsPage

DEST_DIR = "./data/raw"

# modify this to scrape products from other categories
TARGET_CATEGORY = "fruit-vegetables"


def dump_products(category, products):
    os.makedirs(DEST_DIR, exist_ok=True)
    products_file = os.path.join(DEST_DIR, f"{category}-products.json")
    with open(products_file, "w") as dst:
        json.dump(products, dst)


if __name__ == "__main__":

    driver = initialize_driver()
    driver.implicitly_wait(15)

    page_num = 1
    products = []
    while True:
        page = ProductsPage(driver=driver, category=TARGET_CATEGORY, page=page_num)
        page.open()

        found_products = page.list_products()
        print(
            f"({TARGET_CATEGORY}) {len(found_products)} products found on page {page_num}"
        )

        if found_products:
            products.extend(found_products)
            page_num += 1
        else:
            break

    if products:
        dump_products(TARGET_CATEGORY, products=products)

    driver.quit()
