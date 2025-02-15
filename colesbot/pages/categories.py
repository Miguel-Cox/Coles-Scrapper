"""Categories page of the Coles website"""

from selenium.webdriver.common.by import By
from colesbot.pages.base import BasePage


class CategoriesPageLocators:
    """
    A class for Categories page locators. All Categories page
    locators should come here.
    """

    CATEGORY_CARD = (By.XPATH, '//*[@data-testid="category-card"]')


class CategoriesPage(BasePage):
    """Categories page action methods come here"""

    url = "https://www.coles.com.au/browse"

    def list_categories(self):
        cards = self.find_elements(CategoriesPageLocators.CATEGORY_CARD)
        categories = [
            {
                "name": card.text,
                "url": card.get_attribute("href"),
                "slug": card.get_attribute("href").split("/")[-1],
            }
            for card in cards
        ]
        return categories
