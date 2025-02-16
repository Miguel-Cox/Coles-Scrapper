"""Products page of the Coles website"""

from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from colesbot.pages.base import BasePage
from src.models import ProductTile
from src.scrapers import ColesProductTileScraper


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
    """Products page action methods come here"""

    scraper_cls = ColesProductTileScraper

    def __init__(self, driver, category, page=1):
        super().__init__(driver=driver)
        self.url = f"https://www.coles.com.au/browse/{category}"
        if page > 1:
            self.url += f"?page={page}"

    def list_products(self) -> List[ProductTile]:
        if not self._are_product_cards_visible():
            products = []
        scraper = self.scraper_cls(html_content=self.driver.page_source)
        products = scraper.get_all_products()
        return products

    def _are_product_cards_visible(self, timeout=30):
        try:
            card_visible_ec = EC.visibility_of_element_located(
                ProductsPageLocators.PRODUCT_CARD
            )
            WebDriverWait(self.driver, timeout).until(card_visible_ec)
            return True
        except TimeoutException:
            return False
