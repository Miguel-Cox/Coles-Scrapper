import random
import time
from typing import Optional

import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from utils.webdriver import init_seleniumwire_webdriver


class CookieManager:
    """Cookie Manager class for Coles Scraper."""

    REFRESH_URLS = [
        "https://www.coles.com.au/browse/fruit-vegetables",
        "https://www.coles.com.au/browse/frozen",
        "https://www.coles.com.au/browse/dairy-eggs-fridge",
        "https://www.coles.com.au/browse/household",
    ]

    def __init__(self, refresh_url: Optional[str] = None):
        self.refresh_url = refresh_url or random.choice(self.REFRESH_URLS)
        self.cookie = None

    def get_cookie(self):
        self.refresh_cookie()
        return self.cookie

    def refresh_cookie(self):
        driver = init_seleniumwire_webdriver()
        driver.request_interceptor = self._cookie_interceptor
        try:
            self.load_refresh_url(driver)  # First call to prompt cookie creation
            time.sleep(5)
            self.load_refresh_url(driver)  # Second call to capture the cookie
            time.sleep(5)
        except Exception as e:
            print(f"Error while refreshing cookie: {e}")
        finally:
            driver.quit()

    def _cookie_interceptor(self, request):
        if request.url.startswith(self.refresh_url):
            if "cookie" in request.headers:
                self.cookie = request.headers["cookie"]
                print("Cookie refreshed successfully.")

    def load_refresh_url(self, driver):
        driver.get(self.refresh_url)
        category_visible_ec = EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#coles-targeting-header-container")
        )
        WebDriverWait(driver, 30).until(category_visible_ec)
