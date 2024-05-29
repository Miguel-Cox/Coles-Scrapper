"""
Script to scrape all available categories on the Coles website.
"""

import os
import json

from utils.webdriver import initialize_driver
from pages.categories import CategoriesPage

DEST_DIR = "./data/raw"


def dump_categories(categories):
    os.makedirs(DEST_DIR, exist_ok=True)
    categories_file = os.path.join(DEST_DIR, "product-categories.json")
    with open(categories_file, "w") as dst:
        json.dump(categories, dst)


if __name__ == "__main__":

    driver = initialize_driver()
    driver.implicitly_wait(15)

    page = CategoriesPage(driver=driver)
    page.open()

    found_categories = page.list_categories()
    if found_categories:
        dump_categories(found_categories)

    driver.quit()
