"""
Script to scrape all products for given categories on the Coles website.
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List

import pandas as pd
import pytz

from src.fetcher import ColesPageFetcher
from src.models import ProductTile
from src.scrapers import ColesProductTileScraper

logger = logging.getLogger(__name__)

LOCAL_TZ = pytz.timezone("Australia/Sydney")
DURATION_5_MINS = 300


@dataclass
class BrowseQuery:
    category: str
    page: int = 1

    @property
    def url(self) -> str:
        return f"https://www.coles.com.au/browse/{self.category}?page={self.page}"


def extract_products_from_browse(fetcher: ColesPageFetcher, query: BrowseQuery):
    response = fetcher.get(url=query.url)
    products = ColesProductTileScraper(response.content).get_all_products()
    logger.info(
        "Extracted %d products (Category %s, Pg. %d)",
        len(products),
        query.category,
        query.page,
    )
    return products


def update_csv_with_archive(
    new_df: pd.DataFrame, target_path: str, archive_path: str
) -> None:
    """
    Appends new_df to an existing CSV file at target_path, deduplicates rows (keeping only the latest
    record based on the 'timestamp' column), and saves dropped duplicate rows to archive_path.
    """
    if os.path.exists(target_path):
        df_existing = pd.read_csv(target_path)
        df_combined = pd.concat([df_existing, new_df], ignore_index=True)
    else:
        df_combined = new_df.copy()

    df_combined["timestamp_parsed"] = pd.to_datetime(
        df_combined["timestamp"], errors="coerce"
    )
    df_combined.sort_values("timestamp_parsed", ascending=False, inplace=True)
    dup_mask = df_combined.duplicated(subset=["url"], keep="first")

    # Latest prices and product info to save
    df_final = df_combined[~dup_mask].copy()
    df_final.drop(columns=["timestamp_parsed"], inplace=True)

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    df_final.to_csv(target_path, index=False)
    logger.info("Saved %d deduplicated rows to %s", len(df_final), target_path)

    # Stale prices and product info to archive
    df_dropped = df_combined[dup_mask].copy()
    if not df_dropped.empty:
        df_dropped.drop(columns=["timestamp_parsed"], inplace=True)
        os.makedirs(os.path.dirname(archive_path), exist_ok=True)
        if os.path.exists(archive_path):
            df_archive = pd.read_csv(archive_path)
            df_archive = pd.concat([df_archive, df_dropped], ignore_index=True)
        else:
            df_archive = df_dropped
        df_archive.to_csv(archive_path, index=False)
        logger.info("Archived %d duplicate rows to %s", len(df_dropped), archive_path)


def dump_products(products: List[ProductTile], category: str) -> None:
    """
    Converts the products list to a DataFrame, adds category, date, and timestamp columns,
    and saves to data/raw/products.csv. If the CSV already exists, the new data is appended,
    and duplicate rows are removed (keeping only the latest record based on the timestamp).
    """
    if not products:
        logger.info("No products to save for category '%s'.", category)
        return

    df_new = pd.DataFrame(products)
    now = datetime.now(tz=LOCAL_TZ)
    df_new["category"] = category
    df_new["date"] = now.strftime("%Y-%m-%d")
    df_new["timestamp"] = now.isoformat()

    target_file = os.path.join("data", "raw", "products.csv")
    archive_file = os.path.join("data", "archive", "products_dropped.csv")

    update_csv_with_archive(df_new, target_file, archive_file)
    logger.info("Processed %d new rows for category '%s'.", len(df_new), category)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,  # Set to INFO or WARNING in production.
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    categories = [
        "fruit-vegetables",
        "dairy-eggs-fridge",
        "pantry",
        "meat-seafood",
        "bakery",
        "frozen",
        "household",
        "health-beauty",
    ]
    headers = {
        "cookie": None,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }
    fetcher = ColesPageFetcher(headers=headers)

    for category in categories:
        query = BrowseQuery(category=category, page=1)
        products = []
        while True:
            try:
                browse_results = extract_products_from_browse(fetcher, query)
            except Exception as e:
                browse_results = []
                logger.error(
                    "Error extracting products on page %d for category '%s': %s",
                    query.page,
                    category,
                    e,
                )

            if browse_results:
                products.extend(browse_results)
                query.page += 1
            else:
                break

        dump_products(products, category)

        if category == categories[-1]:
            logger.info("Sleeping for %d seconds...", DURATION_5_MINS)
            time.sleep(DURATION_5_MINS)
