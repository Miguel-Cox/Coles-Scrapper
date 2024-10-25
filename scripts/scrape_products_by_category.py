import json
import logging
import os
import sys
from datetime import datetime
from glob import glob

import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from colesbot.scrapers.product_card_scraper import ScrapeProductCardsByCategoryCommand

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Constants
today = datetime.today().strftime("%Y%m%d")
DST_DIR = f"./data/raw/products-by-category/{today}"
DST_GLOB = f"./data/raw/products-by-category/*/*.json"
DST_FILENAME_TEMPLATE = os.path.join(DST_DIR, "{category}-products.json")
TARGET_CATEGORIES = [
    "fruit-vegetables",
    "dairy-eggs-fridge",
    "meat-seafood",
    "pantry",
    "household",
    "frozen",
    "health-beauty",
    "pet",
    "drinks",
    "deli",
    "baby",
    "liquor",
    "bakery",
]
MAX_PAGES = 300

# Ensure destination directory exists
os.makedirs(DST_DIR, exist_ok=True)


def dump_products(category, products):
    """Saves scraped products to a JSON file in a specified category."""
    try:
        products_file = DST_FILENAME_TEMPLATE.format(category=category)
        logging.info(f"Saving {len(products)} products to '{products_file}'")
        with open(products_file, "w") as dst:
            json.dump(products, dst, indent=4)
        logging.info(f"Products saved successfully for category '{category}'")
    except Exception as e:
        logging.error(f"Failed to save products for category '{category}': {e}")
        raise


def process_product_cards(products):
    """Processes the raw product data into a pandas DataFrame."""
    if not products:
        logging.warning("No products to process.")
        return pd.DataFrame()

    df = pd.DataFrame(products)
    df["product_id"] = df["url"].str.extract(r"product\/(.+)\-\d+$")
    df["size"] = df["name"].str.extract(r"\| (.+)$")
    df["price_aud"] = df["price"].str.extract(r"\$([\d,]+\.\d+)").astype(float)
    df["was_price_aud"] = (
        df["price_calc_method"].str.extract(r"Was \$([\d,]+\.\d+)").astype(float)
    )
    df["was_date"] = df["price_calc_method"].str.extract(
        r"Was \$[\d,]+\.\d+ on (\w{3} \d{4})"
    )
    df["unit_price_aud"] = (
        df["price_calc_method"]
        .str.replace(",", "")
        .str.extract(r"\$([\d,]+\.\d+) per")
        .astype(float)
    )
    df["unit"] = (
        df["price_calc_method"]
        .str.replace("Was", "")
        .str.extract(r"\$[\d,]+\.\d+ per (\w+)(?:\s*Was)?")
    )
    df.drop_duplicates(subset=["product_id"], keep="first", inplace=True)

    logging.info(f"Processed {len(df)} unique products.")
    return df


def update_product_cards_dataset(processed_products_df):
    """Updates the product dataset with new or changed product data."""
    try:
        processed_products_df.to_csv("data.csv", index=False)
        logging.info("Product dataset successfully saved to 'data.csv'.")
    except Exception as e:
        logging.error(f"Failed to update product dataset: {e}")
        raise


def scrape_products_for_categories():
    """Scrapes product data for all target categories and saves them."""
    scraper = ScrapeProductCardsByCategoryCommand()
    for category in TARGET_CATEGORIES:
        logging.info(f"Starting to scrape category: {category}")
        scraper.set_category(category)
        try:
            products = scraper.run(max_pages=MAX_PAGES)
            if products:
                dump_products(category, products)
            else:
                logging.warning(f"No products found for category '{category}'.")
                raise Exception("No products found")
        except Exception as e:
            logging.error(f"Error while scraping category '{category}': {e}")
            raise Exception("No products found")


def process_saved_product_data():
    """Processes all saved product JSON files into a single CSV."""
    try:
        src_glob = glob(DST_GLOB)
        if not src_glob:
            logging.warning("No product JSON files found to process.")
            return

        all_products = []
        for filepath in src_glob:
            try:
                with open(filepath, "r") as src:
                    logging.debug(f"Loading products from '{filepath}'")
                    products = json.load(src)
                    all_products.extend(products)
            except Exception as e:
                logging.error(f"Failed to load products from '{filepath}': {e}")

        if all_products:
            processed_products_df = process_product_cards(all_products)
            update_product_cards_dataset(processed_products_df)
        else:
            logging.warning("No products were found in any JSON files.")
    except Exception as e:
        logging.error(f"Error while processing saved product data: {e}")
        raise


if __name__ == "__main__":
    try:
        scrape_products_for_categories()
    except (Exception, KeyboardInterrupt):
        pass

    process_saved_product_data()
