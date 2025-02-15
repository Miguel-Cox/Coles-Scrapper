"""Products page of the Coles website"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup, element
from colesbot.pages.base import BasePage


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

    def __init__(self, driver, category, page=1):
        super().__init__(driver=driver)
        self.url = f"https://www.coles.com.au/browse/{category}"
        if page > 1:
            self.url += f"?page={page}"

    def list_products(self):
        if not self._are_product_cards_visible():
            return []
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        cards = soup.find_all("section", attrs={"data-testid": "product-tile"})
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
        name_element = card.find("h2", class_="product__title")
        url_element = card.find("a", class_="product__link")
        price_element = card.find("span", class_="price__value")
        price_calc_method_element = card.find("div", class_="price__calculation_method")
        price_calc_desc_element = card.find(
            "div", class_="price__calculation_method__description"
        )
        image_element = card.find("img")

        product = {
            "name": name_element.text if name_element else None,
            "url": url_element.attrs["href"] if url_element else None,
            "price": price_element.text if price_element else None,
            "price_calc_method": (
                price_calc_method_element.text if price_calc_method_element else None
            ),
            "price_calc_desc": (
                price_calc_desc_element.text if price_calc_desc_element else None
            ),
            "image_url": image_element.attrs["src"] if image_element else None,
        }

        return product
