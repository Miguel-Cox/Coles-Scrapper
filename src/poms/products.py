"""
Page Object Mode for Coles category browsing pages.
"""

from typing import List

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.models import ProductTile
from src.scrapers import ColesProductTileScraper

from .base import BasePage


class ProductsPageLocators:
    """
    A class for Products page locators. All Products page
    locators should come here.
    """

    PRODUCT_CARD = (By.XPATH, '//*[@data-testid="product-tile"]')
    # # Unused locators retained for future use.
    # PRODUCT_NAME = (By.CLASS_NAME, "product__title")
    # PRODUCT_URL = (By.CLASS_NAME, "product__link")
    # PRODUCT_PRICE = (By.CLASS_NAME, "price")
    # PRODUCT_PRICE_CALC_METHOD = (By.CLASS_NAME, "price__calculation_method")
    # PRODUCT_PRICE_CALC_DESC = (By.CLASS_NAME, "price__calculation_method__description")
    # PRODUCT_IMAGE = (By.TAG_NAME, "img")


class ProductsPage(BasePage):
    """
    Page Object Model for Coles category browsing pages.

    Represents pages listing multiple products for a given category, with URLs like:
    - `https://www.coles.com.au/browse/<category>`
    - `https://www.coles.com.au/browse/<category>?page=<page_number>`

    Example:
    - `https://www.coles.com.au/browse/pantry`
    - `https://www.coles.com.au/browse/pantry?page=2`
    """

    scraper_cls = ColesProductTileScraper

    def __init__(self, driver, category, page=1):
        super().__init__(driver=driver)
        self.url = self._build_url(category, page)

    @staticmethod
    def _build_url(category: str, page: int = 1) -> str:
        url = f"https://www.coles.com.au/browse/{category}"
        if page > 1:
            url += f"?page={page}"
        return url

    def list_products(self) -> List[ProductTile]:
        if self.wait_for_element_visibility(ProductsPageLocators.PRODUCT_CARD):
            scraper = self.scraper_cls(html_content=self.driver.page_source)
            products = scraper.get_all_products()
        else:
            products = []
        return products
