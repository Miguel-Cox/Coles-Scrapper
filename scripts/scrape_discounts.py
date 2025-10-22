"""
Script to scrape discounted/special offer products from the Coles website.
"""

import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import pandas as pd
import pytz

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.fetcher import ColesPageFetcher
from src.models import ProductTile
from src.scrapers import ColesProductTileScraper

logger = logging.getLogger(__name__)

LOCAL_TZ = pytz.timezone("Australia/Sydney")
DURATION_5_MINS = 300


@dataclass
class SpecialsQuery:
    """Query configuration for Coles specials pages."""
    base_url: str = "https://www.coles.com.au/on-special"
    pid: str = "offers_modular3_special"
    filter_type: Optional[str] = None  # e.g., 'halfprice', 'special'
    page: int = 1

    @property
    def url(self) -> str:
        url = f"{self.base_url}?pid={self.pid}"
        if self.filter_type:
            url += f"&filter_Special={self.filter_type}"
        url += f"&page={self.page}"
        return url


def extract_discount_products(fetcher: ColesPageFetcher, query: SpecialsQuery) -> List[ProductTile]:
    """
    Extract discount products from a Coles specials page.
    
    :param fetcher: ColesPageFetcher instance for making requests
    :param query: SpecialsQuery configuration
    :return: List of ProductTile objects
    """
    try:
        response = fetcher.get(url=query.url)
        products = ColesProductTileScraper(response.content).get_all_products()
        
        # Filter to only keep products that are actually on special
        discount_products = [p for p in products if p.is_on_special]
        
        logger.info(
            "Extracted %d discount products (Filter: %s, Page: %d)",
            len(discount_products),
            query.filter_type or "all",
            query.page,
        )
        return discount_products
        
    except Exception as e:
        logger.error(
            "Error extracting discount products (Filter: %s, Page: %d): %s",
            query.filter_type or "all",
            query.page,
            e
        )
        return []


def process_discount_data(products: List[ProductTile]) -> pd.DataFrame:
    """
    Process discount product data to match scrape_products format.
    
    :param products: List of ProductTile objects
    :return: Processed DataFrame
    """
    if not products:
        return pd.DataFrame()
    
    df = pd.DataFrame([product.dict() for product in products])
    
    # Prepend base URL for product and image URLs
    df["url"] = "https://www.coles.com.au" + df["url"]
    df["image_url"] = "https://www.coles.com.au" + df["image_url"]
    
    # Extract fields using regex (same as scrape_products)
    df["product_id"] = df["url"].str.extract(r"product\/(.+)\-\d+$")[0]
    df["size"] = df["name"].str.extract(r"\| (.+)$")[0]
    df["price_aud"] = df["price"].str.extract(r"\$([\d,]+\.\d+)")[0].str.replace(",", "", regex=False).astype(float)
    df["was_price_aud"] = (
        df["price_calc_method"].str.extract(r"Was \$([\d,]+\.\d+)")[0].str.replace(",", "", regex=False).astype(float)
    )
    df["was_date"] = df["price_calc_method"].str.extract(
        r"Was \$[\d,]+\.\d+ on (\w{3} \d{4})"
    )[0]
    df["unit_price_aud"] = (
        df["price_calc_method"]
        .str.replace(",", "", regex=False)
        .str.extract(r"\$([\d,]+\.\d+) per")[0]
        .astype(float)
    )
    df["unit"] = (
        df["price_calc_method"]
        .str.replace("Was", "", regex=False)
        .str.extract(r"\$[\d,]+\.\d+ per (\w+)(?:\s*Was)?")[0]
    )
    
    # Filter: Keep only products where current price is lower than previous price
    df = df[(df["price_aud"] < df["was_price_aud"]) & df["was_price_aud"].notna()].copy()
    
    # Remove duplicate products
    df.drop_duplicates(subset=["product_id"], keep="first", inplace=True)
    
    # Rename columns to match scrape_products format
    df = df.rename(
        columns={
            "name": "product_name",
            "url": "product_url",
            "price": "display_price",
            "price_calc_method": "pricing_details",
            "image_url": "product_image_url",
            "price_aud": "current_price_aud",
            "was_price_aud": "previous_price_aud",
            "was_date": "previous_price_date",
            "unit": "unit_of_measure",
        }
    )
    
    # Add category as "discount" to match products format
    df["category"] = "discount"
    
    # Reorder columns to match scrape_products format exactly
    cols_order = [
        "product_id",
        "product_name",
        "category",
        "size",
        "product_url",
        "product_image_url",
        "display_price",
        "current_price_aud",
        "unit_price_aud",
        "unit_of_measure",
        "previous_price_aud",
        "pricing_details",
        "previous_price_date",
    ]
    
    # Keep only the columns that exist
    cols_order = [col for col in cols_order if col in df.columns]
    df = df[cols_order]
    
    return df


def save_discount_products(products: List[ProductTile], filter_type: Optional[str] = None) -> None:
    """
    Process and save discount product data in the same format as scrape_products.
    
    :param products: List of ProductTile objects to save
    :param filter_type: Type of special filter used (e.g., 'halfprice')
    """
    if not products:
        logger.info("No discount products to save for filter '%s'.", filter_type or "all")
        return

    df_processed = process_discount_data(products)
    
    if df_processed.empty:
        logger.info("No products with valid discounts (current < previous price) for filter '%s'.", filter_type or "all")
        return
    
    now = datetime.now(tz=LOCAL_TZ)
    df_processed["scrape_date"] = now.strftime("%Y-%m-%d")
    df_processed["scrape_timestamp"] = now.isoformat()

    # Create output directory if it doesn't exist
    output_dir = os.path.join("data", "discounts")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to timestamped file
    timestamp_str = now.strftime("%Y%m%d_%H%M%S")
    filename = f"discounts_{filter_type or 'all'}_{timestamp_str}.csv"
    output_path = os.path.join(output_dir, filename)
    
    df_processed.to_csv(output_path, index=False)
    logger.info("Saved %d discount products to %s", len(df_processed), output_path)
    
    # Also save to latest file for easy access
    latest_filename = f"discounts_{filter_type or 'all'}_latest.csv"
    latest_path = os.path.join(output_dir, latest_filename)
    df_processed.to_csv(latest_path, index=False)
    logger.info("Also saved to %s", latest_path)


def scrape_all_discount_types(fetcher: ColesPageFetcher):
    """
    Scrape all types of discount products available on Coles.
    
    :param fetcher: ColesPageFetcher instance
    """
    # Different special filter types to try
    filter_types = [
        None,  # All specials
        "halfprice",  # Half price specials
        "special",  # General specials
    ]
    
    for filter_type in filter_types:
        logger.info("Starting to scrape discount type: %s", filter_type or "all_specials")
        
        query = SpecialsQuery(filter_type=filter_type, page=1)
        all_products = []
        
        # Paginate through all pages
        while True:
            products = extract_discount_products(fetcher, query)
            
            if products:
                all_products.extend(products)
                query.page += 1
                # Small delay between pages
                time.sleep(2)
            else:
                break
        
        # Save all products for this filter type
        save_discount_products(all_products, filter_type)
        
        # Delay between different filter types to be respectful
        if filter_type != filter_types[-1]:  # Not the last filter
            logger.info("Sleeping for %d seconds before next filter type...", DURATION_5_MINS)
            time.sleep(DURATION_5_MINS)


def analyze_discount_data(filter_type: Optional[str] = None):
    """
    Analyze the scraped discount data and show summary statistics.
    
    :param filter_type: Type of discount filter to analyze
    """
    filename = f"discounts_{filter_type or 'all'}_latest.csv"
    data_path = os.path.join("data", "discounts", filename)
    
    if not os.path.exists(data_path):
        logger.warning("No discount data found at %s", data_path)
        return
    
    df = pd.read_csv(data_path)
    
    logger.info("=== DISCOUNT ANALYSIS for %s ===", filter_type or "ALL SPECIALS")
    logger.info("Total discount products found: %d", len(df))
    
    if 'previous_price_aud' in df.columns and 'current_price_aud' in df.columns:
        df['savings_aud'] = df['previous_price_aud'] - df['current_price_aud']
        df['savings_pct'] = ((df['previous_price_aud'] - df['current_price_aud']) / df['previous_price_aud'] * 100)
        logger.info("Average savings: $%.2f (%.1f%%)", df['savings_aud'].mean(), df['savings_pct'].mean())
        logger.info("Total potential savings: $%.2f", df['savings_aud'].sum())
    
    # Show some example products
    logger.info("Example discount products:")
    for i, (_, row) in enumerate(df.head(5).iterrows()):
        logger.info("  %d. %s - $%.2f (Was: $%.2f, Save: $%.2f)", 
                   i+1, row['product_name'], 
                   row.get('current_price_aud', 0), 
                   row.get('previous_price_aud', 0),
                   row.get('previous_price_aud', 0) - row.get('current_price_aud', 0))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Silence seleniumwire logs of network requests
    logging.getLogger("seleniumwire.handler").setLevel(logging.WARNING)

    headers = {
        "cookie": None,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
    }
    
    try:
        fetcher = ColesPageFetcher(headers=headers)
        
        # Scrape all discount types
        scrape_all_discount_types(fetcher)
        
        # Analyze the results
        logger.info("\n" + "="*50)
        logger.info("ANALYSIS COMPLETE - Showing Results")
        logger.info("="*50)
        
        for filter_type in [None, "halfprice", "special"]:
            analyze_discount_data(filter_type)
            logger.info("")
            
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error("An error occurred: %s", e)
        raise