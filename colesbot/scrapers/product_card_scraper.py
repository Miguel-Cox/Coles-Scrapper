import logging
import time

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.exceptions import HTTPError

from colesbot.utils.cookies import CookieManager


class ProductCard:

    def __init__(self, card: Tag):
        self.card = card

    def to_dict(self):
        return {
            "name": self.title,
            "url": self.url,
            "price": self.price,
            "price_calc_method": self.price_calc_method,
            "price_calc_desc": self.price_calc_desc,
            "image_url": self.image_url,
        }

    @property
    def title(self):
        return self._get_text("h2", class_="product__title")

    @property
    def url(self):
        return self._get_attr("a", class_="product__link", attr="href")

    @property
    def price(self):
        return self._get_text("span", class_="price__value")

    @property
    def price_calc_method(self):
        return self._get_text("div", class_="price__calculation_method")

    @property
    def price_calc_desc(self):
        return self._get_text("div", class_="price__calculation_method__description")

    @property
    def image_url(self):
        return self._get_attr("img", attr="src")

    def _get_text(self, *args, **kwargs):
        element = self.card.find(*args, **kwargs)
        return element.text if element else None

    def _get_attr(self, *args, **kwargs):
        if "attr" not in kwargs:
            raise ValueError("`attr` kwarg is required.")
        attr = kwargs.pop("attr")
        element = self.card.find(*args, **kwargs)
        return element.attrs.get(attr) if element else None


class ScrapeProductCardsByCategoryCommand:

    SLEEP_SECS_S = 3.5
    SLEEP_SECS_M = 10
    SLEEP_SECS_L = 30

    def __init__(self):
        self.headers = None
        self.category = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cm = CookieManager()

    def set_category(self, category):
        self.category = category
        return self.category

    def run(self, max_pages: int = 10):
        if self.headers is None:
            self.refresh_headers()

        page_num = 1
        self.products = []
        while page_num <= max_pages:
            try:
                page_html = self.get_page(page_num)
                products = self.extract_products(page_html)
            except ValueError as e:
                time.sleep(self.SLEEP_SECS_L)
                self.refresh_headers()
                time.sleep(self.SLEEP_SECS_M)
                continue
            except HTTPError:
                time.sleep(self.SLEEP_SECS_M)
                page_num += 1
                continue

            if products:
                self.logger.info(
                    f"({self.category}) {len(products)} products found on page {page_num}"
                )
                self.products.extend(products)
                page_num += 1
                time.sleep(self.SLEEP_SECS_S)
            else:
                break

        return self.products

    def get_page(self, page_num: int = 1):
        url = f"https://www.coles.com.au/browse/{self.category}"
        if page_num > 1:
            url += f"?page={page_num}"

        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()

        if ("Incapsula" in str(resp.content)) or (
            "Pardon Our Interruption" in str(resp.content)
        ):
            self.logger.warning("Request blocked by bot detection measures.")
            raise ValueError("Bot detected!")

        return resp.content

    def extract_products(self, html):
        soup = BeautifulSoup(html, "html.parser")
        card_elements = soup.find_all("section", attrs={"data-testid": "product-tile"})
        return [ProductCard(card).to_dict() for card in card_elements]

    def refresh_headers(self):
        self.logger.info("Refreshing cookies...")
        cookie = self.cm.get_cookie()
        self.headers = {
            "cookie": cookie,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        }
        return self.headers
