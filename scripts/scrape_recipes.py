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
    :return: Dictionary with recipe URL, total_savings, and full product JSON, or None if not found
    """
    try:
        logger.info(f"Visiting recipe: {recipe_url}")
        
        # Clear previous requests
        del driver.requests
        
        # Visit the recipe page
        driver.get(recipe_url)
        
        # Wait for the products API request to appear (max 2 seconds)
        max_wait = 2
        start_time = time.time()
        api_found = False
        
        while time.time() - start_time < max_wait:
            for request in driver.requests:
                if '/api/bff/recipes/' in request.url and '/products' in request.url:
                    api_found = True
                    break
            if api_found:
                break
            time.sleep(0.2)  # Check every 0.2 seconds
        
        elapsed = time.time() - start_time
        logger.info(f"API request captured in {elapsed:.2f} seconds")
        
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
                        
                        # Extract total_savings for sorting
                        total_savings = response_data.get('totalSavings', 0)
                        
                        logger.info(f"✓ Found recipe data - Savings: {total_savings}")
                        return {
                            'recipe_url': recipe_url,
                            'total_savings': total_savings,
                            'product_json': response_data  # Store complete JSON
                        }
                except Exception as e:
                    logger.warning(f"✗ Error parsing request {request.url}: {e}")
                    continue
        
        logger.warning(f"No products API request found for {recipe_url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting recipe data from {recipe_url}: {e}")
        return None


def get_recipe_links(driver, category_url: str, max_recipes: int = 500) -> List[str]:
    """
    Get all recipe links from the category page with pagination.
    
    :param driver: Selenium WebDriver instance
    :param category_url: URL of the recipe category page
    :param max_recipes: Maximum number of recipes to collect
    :return: List of recipe URLs
    """
    all_recipe_urls = set()
    page = 5
    
    try:
        while len(all_recipe_urls) < max_recipes:
            # Construct paginated URL
            if page == 1:
                page_url = category_url
            else:
                # Add page parameter to URL
                separator = '&' if '?' in category_url else '?'
                page_url = f"{category_url}{separator}page={page}"
            
            logger.info(f"Loading category page {page}: {page_url}")
            driver.get(page_url)
            
            # Wait for recipe cards to load
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/recipes/']"))
                )
            except:
                logger.info(f"No recipes found on page {page}. Reached end of pagination.")
                break
            
            # Find all recipe links on current page
            recipe_elements = driver.find_elements(By.CSS_SELECTOR, "a[href*='/recipes/']")
            
            # Extract unique URLs from current page
            page_recipe_urls = set()
            for element in recipe_elements:
                href = element.get_attribute('href')
                if href and '/recipes/' in href and '/category/' not in href:
                    page_recipe_urls.add(href)
            
            # If no new recipes found, we've reached the end
            if not page_recipe_urls:
                logger.info(f"No recipes found on page {page}. Stopping pagination.")
                break
            
            # Add new recipes to the set
            before_count = len(all_recipe_urls)
            all_recipe_urls.update(page_recipe_urls)
            new_recipes = len(all_recipe_urls) - before_count
            
            logger.info(f"Page {page}: Found {new_recipes} new recipes (Total: {len(all_recipe_urls)})")
            
            # If no new recipes were added, we've likely reached the end
            if new_recipes == 0:
                logger.info(f"No new recipes on page {page}. Stopping pagination.")
                break
            
            page += 1
            time.sleep(1)  # Be polite to the server
        
        logger.info(f"Found {len(all_recipe_urls)} unique recipes across {page} page(s)")
        return list(all_recipe_urls)
        
    except Exception as e:
        logger.error(f"Error getting recipe links: {e}")
        return list(all_recipe_urls) if all_recipe_urls else []


def keep_top_recipes(recipes_data: List[Dict], top_n: int = 20) -> List[Dict]:
    """
    Keep only the top N recipes with the highest total_savings.
    Inserts new recipes and maintains sorted order.
    
    :param recipes_data: List of dictionaries containing recipe data
    :param top_n: Number of top recipes to keep (default: 20)
    :return: Sorted list of top N recipes by total_savings
    """
    if not recipes_data:
        return []
    
    # Sort by total_savings in descending order
    sorted_recipes = sorted(
        recipes_data, 
        key=lambda x: x.get('total_savings', 0), 
        reverse=True
    )
    
    # Keep only top N
    top_recipes = sorted_recipes[:top_n]
    
    logger.info(f"Kept top {len(top_recipes)} recipes out of {len(recipes_data)}")
    if top_recipes:
        logger.info(f"Savings range: {top_recipes[0].get('total_savings')} to {top_recipes[-1].get('total_savings')}")
    
    return top_recipes


def save_recipes_data(recipes_data: List[Dict]) -> None:
    """
    Save recipe data to JSON file.
    Stores only top 20 recipes with highest total_savings.
    
    :param recipes_data: List of dictionaries containing recipe data
    """
    if not recipes_data:
        logger.info("No recipe data to save.")
        return
    
    # Keep only top 20 recipes
    top_recipes = keep_top_recipes(recipes_data, top_n=20)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join("data", "recipes")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to JSON file (preserves complete product_json structure)
    output_path = os.path.join(output_dir, "recipes.json")
    with open(output_path, 'w') as f:
        json.dump(top_recipes, f, indent=2)
    
    logger.info(f"Saved {len(top_recipes)} recipes to {output_path}")


def scrape_dinner_recipes():
    """
    Main function to scrape dinner recipes from Coles website.
    """
    category_url = "https://www.coles.com.au/recipes-inspiration/category/meal/dinner"
    max_recipes = 200
    
    driver = None
    try:
        # Initialize Selenium Wire driver
        logger.info("Initializing driver...")
        driver = init_seleniumwire_webdriver()
        
        # Get all recipe links from the category page with pagination
        recipe_urls = get_recipe_links(driver, category_url, max_recipes=max_recipes)
        
        if not recipe_urls:
            logger.warning("No recipe URLs found. Exiting.")
            return
        
        # Limit to max_recipes
        recipe_urls = recipe_urls[:max_recipes]
        logger.info(f"Processing {len(recipe_urls)} recipes")
        
        # Extract data from each recipe
        recipes_data = []
        for i, recipe_url in enumerate(recipe_urls, 1):
            logger.info(f"Processing recipe {i}/{len(recipe_urls)}")
            
            recipe_data = extract_recipe_data(driver, recipe_url)
            if recipe_data:
                recipes_data.append(recipe_data)
        
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
