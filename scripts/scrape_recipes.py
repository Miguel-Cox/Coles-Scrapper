"""
Script to scrape recipes from the Coles website and extract product information.
"""

import logging
import os
import sys
import time
import json
import gzip
from datetime import datetime
from typing import List, Optional, Dict

import pandas as pd
import pytz
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.webdriver_utils import init_seleniumwire_webdriver

logger = logging.getLogger(__name__)

LOCAL_TZ = pytz.timezone("Australia/Sydney")


def extract_recipe_data(driver, recipe_url: str) -> Optional[Dict]:
    """
    Visit a recipe page and capture the products API request.
    
    :param driver: Selenium WebDriver instance
    :param recipe_url: URL of the recipe to scrape
    :return: Dictionary with recipeId and totalSavings, or None if not found
    """
    try:
        logger.info(f"Visiting recipe: {recipe_url}")
        
        # Clear previous requests
        del driver.requests
        
        # Visit the recipe page
        driver.get(recipe_url)
        
        # Wait for page to load and API calls to complete
        time.sleep(5)
        
        logger.info(f"Total requests captured: {len(driver.requests)}")
        
        # First, log ALL requests to see what's being captured
        logger.info("=== ALL CAPTURED REQUESTS ===")
        for i, request in enumerate(driver.requests[:20], 1):  # Show first 20
            logger.info(f"{i}. {request.url}")
        
        if len(driver.requests) > 20:
            logger.info(f"... and {len(driver.requests) - 20} more requests")
        
        # Look for the products API request: /api/bff/recipes/{id}/products
        for request in driver.requests:
            if request.response:
                try:
                    # Look for the specific BFF recipes products endpoint
                    if '/api/bff/recipes/' in request.url and '/products' in request.url:
                        
                        logger.info(f"✓ Found products API request: {request.url}")
                        
                        # Get response body and handle gzip compression
                        response_body = request.response.body
                        
                        # Check if response is gzip compressed
                        if response_body[:2] == b'\x1f\x8b':  # gzip magic number
                            response_body = gzip.decompress(response_body)
                        
                        # Decode to string and parse JSON
                        response_text = response_body.decode('utf-8')
                        response_data = json.loads(response_text)
                        
                        logger.info(f"Response keys: {list(response_data.keys())}")
                        
                        # Extract recipeId and totalSavings
                        recipe_id = response_data.get('recipeId')
                        total_savings = response_data.get('totalSavings')
                        
                        logger.info(f"✓ Found recipe data - ID: {recipe_id}, Savings: {total_savings}")
                        return {
                            'recipe_url': recipe_url,
                            'recipe_id': recipe_id,
                            'total_savings': total_savings
                        }
                except Exception as e:
                    logger.warning(f"✗ Error parsing request {request.url}: {e}")
                    continue
        
        logger.warning(f"No products API request found for {recipe_url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting recipe data from {recipe_url}: {e}")
        return None


def get_recipe_links(driver, category_url: str) -> List[str]:
    """
    Get all recipe links from the category page.
    
    :param driver: Selenium WebDriver instance
    :param category_url: URL of the recipe category page
    :return: List of recipe URLs
    """
    try:
        logger.info(f"Loading category page: {category_url}")
        driver.get(category_url)
        
        # Wait for recipe cards to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/recipes/']"))
        )
        
        # Find all recipe links
        recipe_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/recipes/']")
        
        # Extract unique URLs
        recipe_urls = set()
        for element in recipe_elements:
            href = element.get_attribute('href')
            if href and '/recipes/' in href and '/category/' not in href:
                recipe_urls.add(href)
        
        logger.info(f"Found {len(recipe_urls)} unique recipes")
        return list(recipe_urls)
        
    except Exception as e:
        logger.error(f"Error getting recipe links: {e}")
        return []


def save_recipes_data(recipes_data: List[Dict]) -> None:
    """
    Save recipe data to CSV file.
    
    :param recipes_data: List of dictionaries containing recipe data
    """
    if not recipes_data:
        logger.info("No recipe data to save.")
        return
    
    df = pd.DataFrame(recipes_data)
    
    # Add scraping metadata
    now = datetime.now(tz=LOCAL_TZ)
    df['scrape_date'] = now.strftime("%Y-%m-%d")
    df['scrape_timestamp'] = now.isoformat()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join("data", "recipes")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to CSV
    output_path = os.path.join(output_dir, "recipes.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} recipes to {output_path}")


def scrape_dinner_recipes():
    """
    Main function to scrape dinner recipes from Coles website.
    """
    category_url = "https://www.coles.com.au/recipes-inspiration/category/meal/dinner"
    
    driver = None
    try:
        # Initialize Selenium Wire driver
        logger.info("Initializing driver...")
        driver = init_seleniumwire_webdriver()
        
        # Get all recipe links from the category page
        recipe_urls = get_recipe_links(driver, category_url)
        
        if not recipe_urls:
            logger.warning("No recipe URLs found. Exiting.")
            return
        
        # Limit to first 10 recipes for testing
        recipe_urls = recipe_urls[:10]
        logger.info(f"Processing first {len(recipe_urls)} recipes")
        
        # Extract data from each recipe
        recipes_data = []
        for i, recipe_url in enumerate(recipe_urls, 1):
            logger.info(f"Processing recipe {i}/{len(recipe_urls)}")
            
            recipe_data = extract_recipe_data(driver, recipe_url)
            if recipe_data:
                recipes_data.append(recipe_data)
            
            # Add delay between requests to be respectful
            if i < len(recipe_urls):
                time.sleep(2)
        
        # Save the collected data
        save_recipes_data(recipes_data)
        
        logger.info(f"Scraping complete. Collected {len(recipes_data)} recipes with product data.")
        
    except Exception as e:
        logger.error(f"An error occurred during scraping: {e}")
        raise
    finally:
        if driver:
            driver.quit()
            logger.info("Driver closed.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Silence seleniumwire logs of network requests
    logging.getLogger("seleniumwire.handler").setLevel(logging.WARNING)
    
    try:
        scrape_dinner_recipes()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
