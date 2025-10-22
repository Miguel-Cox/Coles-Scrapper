"""
Scraper classes for extracting data from the Coles website.
"""

from typing import List

from bs4.element import Tag

from src import models
from src.common import HtmlScraper


class ColesProductTileScraper(HtmlScraper):
    """
    Scraper for extracting product details from **category browsing pages** on the Coles website.

    This scraper looks for and extracts data from each "product tile" found on pages such as:
        - https://www.coles.com.au/browse/fruit-vegetables
        - https://www.coles.com.au/browse/fruit-vegetables?page=4

    Typical usage example:
    >>> html_content = ...  # obtain the page's HTML via your fetching logic

    >>> tile_scraper = ColesProductTileScraper(html_content)
    >>> product_tiles = tile_scraper.get_all_products()

    >>> # Each 'ProductTile' contains fields like 'name', 'url', 'price', etc.
    >>> for tile in product_tiles:
    ...     print(tile.dict())

    Example Output:
    ```
    {
        "name": "Coles Cheese Shredded Tasty Light | 700g",
        "url": "/product/coles-cheese-shredded-tasty-light-700g-8145346",
        "price": "$9.50",
        "price_calc_method": "$13.57 per 1kg",
        "image_url": "/_next/image?url=https%3A%2F%2Fproductimages.coles.com.au%2Fproductimages%2F8%2F8145346.jpg&w=640&q=90",
    }
    ```
    """

    def get_all_products(self) -> List[models.ProductTile]:
        """
        Retrieves all product data from the HTML content.

        :return: A list of ProductTile instances with product details.
        """
        data = []
        product_tiles = self.find_all_product_tiles()
        for tile in product_tiles:
            try:
                product = self.extract_product_from_tile(tile)
                data.append(product)
            except Exception as e:
                self.logger.warning(f"Failed to extract product from tile: {e}")
        return data

    def find_all_product_tiles(self) -> List[Tag]:
        """
        Finds all product tiles in the HTML content.

        :return: A list of BeautifulSoup Tag objects representing product tiles.
        """
        try:
            return self.soup.find_all("section", attrs={"data-testid": "product-tile"})
        except Exception as e:
            self.logger.error(f"Error finding product tiles: {e}")
            return []

    def extract_product_from_tile(self, tile: Tag) -> models.ProductTile:
        """
        Extracts product details from a single product tile.

        :param tile: The BeautifulSoup Tag object representing a product tile.
        :return: An instance of ProductTile with the product's details.
        """
        product_data = {
            "name": self.get_text_content(tile, "h2", class_="product__title"),
            "price": self.get_text_content(tile, "span", class_="price__value"),
            "price_calc_method": self.get_text_content(
                tile, "div", class_="price__calculation_method"
            ),
            "url": self.get_attribute(tile, "a", attr="href", class_="product__link"),
            "image_url": self.get_attribute(tile, "img", attr="src"),
        }
        
        # Extract discount information
        discount_info = self.extract_discount_info(tile)
        product_data.update(discount_info)
        
        return models.ProductTile(**product_data)
    
    def extract_discount_info(self, tile: Tag) -> dict:
        """
        Extracts discount-related information from a product tile.
        
        :param tile: The BeautifulSoup Tag object representing a product tile.
        :return: Dictionary with discount information.
        """
        discount_info = {
            "was_price": None,
            "discount_percentage": None,
            "special_type": None,
            "is_on_special": False
        }
        
        # Look for "was" price indicators
        price_calc = self.get_text_content(tile, "div", class_="price__calculation_method")
        if price_calc and "was" in price_calc.lower():
            discount_info["is_on_special"] = True
            # Extract was price using regex
            import re
            was_match = re.search(r"was \$([\d,]+\.\d+)", price_calc, re.IGNORECASE)
            if was_match:
                discount_info["was_price"] = f"${was_match.group(1)}"
        
        # Look for special badges/labels
        special_labels = [
            ("span", {"class": "special-badge"}),
            ("div", {"class": "special-label"}),
            ("span", {"class": "badge"}),
            ("div", {"class": "promotion-badge"}),
            ("span", {"data-testid": "special-badge"})
        ]
        
        for tag_name, attrs in special_labels:
            special_text = self.get_text_content(tile, tag_name, **attrs)
            if special_text:
                discount_info["special_type"] = special_text
                discount_info["is_on_special"] = True
                break
        
        # Look for percentage discounts in text content
        tile_text = tile.get_text(separator=" ").lower()
        discount_patterns = [
            r"half price",
            r"(\d+)%\s*off",
            r"save\s*(\d+)%",
            r"(\d+)%\s*discount"
        ]
        
        import re
        for pattern in discount_patterns:
            match = re.search(pattern, tile_text)
            if match:
                discount_info["is_on_special"] = True
                if "half price" in pattern:
                    discount_info["discount_percentage"] = "50%"
                    discount_info["special_type"] = "Half Price"
                elif match.groups():
                    discount_info["discount_percentage"] = f"{match.group(1)}%"
                break
        
        # Calculate percentage if we have current and was price
        if discount_info["was_price"] and not discount_info["discount_percentage"]:
            try:
                current_price = self.get_text_content(tile, "span", class_="price__value")
                if current_price and discount_info["was_price"]:
                    current = float(current_price.replace("$", "").replace(",", ""))
                    was = float(discount_info["was_price"].replace("$", "").replace(",", ""))
                    if was > 0:
                        percentage = ((was - current) / was) * 100
                        discount_info["discount_percentage"] = f"{percentage:.0f}%"
                        if percentage >= 49 and percentage <= 51:  # Approximately half price
                            discount_info["special_type"] = "Half Price"
            except (ValueError, TypeError):
                pass  # Skip calculation if prices can't be parsed
        
        return discount_info


class ColesProductScraper(HtmlScraper):
    """
    Scraper for extracting detailed product information from **dedicated product pages** on the Coles website.

    This scraper looks for and extracts data from pages such as:
        - https://www.coles.com.au/product/appy-fizz-250ml-8060378

    Typical usage example:
    >>> html_content = ...  # obtain the page's HTML via your fetching logic

    >>> product_scraper = ColesProductScraper(html_content)
    >>> product = product_scraper.get_product()

    >>> # Each 'Product' contains fields like 'name', 'brand_name', 'brand_url', etc.
    >>> print(product.dict())

    Example Output:
    ```
    {
        "name": "Appy Fizz | 250mL",
        "brand_name": "Appy",
        "brand_url": "/brands/appy-4039743300",
        "categories": ["Home", "All categories", "Pantry", "International foods", "Indian"],
        "retail_limit": "Retail limit: 20",
        "promotional_limit": "Promotional limit: 12",
        "product_code": "Code: 8060378",
    }
    ```
    """

    def get_product(self) -> List[models.Product]:
        """
        Retrieves product data from the product pages HTML content.

        :return: A Product instance with product details.
        """
        product_data = {
            "name": self.get_text_content(self.soup, "h1", class_="product__title"),
            "brand_name": self.get_text_content(
                self.soup, "a", attrs={"data-testid": "brand-link"}
            ),
            "brand_url": self.get_attribute(
                self.soup, "a", attrs={"data-testid": "brand-link"}, attr="href"
            ),
            "categories": self.get_all_text_content(
                self.soup, "span", attrs={"itemprop": "name"}
            ),
            "retail_limit": self.get_text_content(
                self.soup, "p", attrs={"data-testid": "retail-limit"}
            ),
            "promotional_limit": self.get_text_content(
                self.soup, "p", attrs={"data-testid": "promotional-limit"}
            ),
            "product_code": self.get_text_content(
                self.soup, "p", attrs={"data-testid": "product-code"}
            ),
        }
        return models.Product(**product_data)
