"""Products page of the Coles website"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from pages.base import BasePage


class ProductsPageLocators:
    """
    A class for Products page locators. All Products page
    locators should come here.
    """

    PRODUCT_CARD = (By.XPATH, '//*[@data-testid="product-tile"]')
    PRODUCT_NAME = (By.CLASS_NAME, "product__title")
    PRODUCT_URL = (By.CLASS_NAME, "product__link")
    PRODUCT_PRICE = (By.CLASS_NAME, "price")
    PRODUCT_PRICE_CALC_METHOD = (By.CLASS_NAME, "price__calculation_method")
    PRODUCT_PRICE_CALC_DESC = (By.CLASS_NAME, "price__calculation_method__description")
    PRODUCT_IMAGE = (By.TAG_NAME, "img")


class ProductsPage(BasePage):
    """Products page action methods come here"""

    def __init__(self, driver, category, page=1):
        super().__init__(driver=driver)
        self.url = f"https://www.coles.com.au/browse/{category}"
        if page > 1:
            self.url += f"?page={page}"

    def list_products(self):
        if not self._are_product_cards_visible():
            return []
        cards = self.find_elements(ProductsPageLocators.PRODUCT_CARD)
        products = [self.scrape_product_details(card) for card in cards]
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

    @staticmethod
    def scrape_product_details(card):
        product = {}
        key_loc_attr = [
            ("name", ProductsPageLocators.PRODUCT_NAME, "textContent"),
            ("url", ProductsPageLocators.PRODUCT_URL, "href"),
            ("price", ProductsPageLocators.PRODUCT_PRICE, "textContent"),
            (
                "price_calc_method",
                ProductsPageLocators.PRODUCT_PRICE_CALC_METHOD,
                "textContent",
            ),
            (
                "price_calc_desc",
                ProductsPageLocators.PRODUCT_PRICE_CALC_DESC,
                "textContent",
            ),
            ("image_url", ProductsPageLocators.PRODUCT_IMAGE, "src"),
        ]
        for key, locator, attr in key_loc_attr:
            try:
                elem = card.find_element(*locator)
            except NoSuchElementException:
                product[key] = None
            else:
                product[key] = elem.get_attribute(attr)

        return product
