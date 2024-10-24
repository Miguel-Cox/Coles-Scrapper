import logging
import time

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag


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

    def __init__(self, category):
        self.driver = None
        self.headers = None
        self.cookies = None
        self.category = category
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self, max_pages: int = 10):
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
        # TODO: Logic to refresh headers
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "cookie": "visid_incap_2800108=e73PYei0RJGQXq5Vh+8R1KqlX2YAAAAAQUIPAAAAAADxo87wUDxalU5rQe1dAY8Q; ld_user=67edf4e5-d3ab-4cf8-b0c8-7c92ba112ab3; visitorId=5d26124b-b52c-4d4a-85e6-741dd3b5e47d; ai_user=lIr2U2pQD6FG1Y6lbWPJlt|2024-06-04T23:39:26.413Z; ORA_FPC=id=e356c497-367a-4400-8f8c-60ed6b5d3a5c; s_ecid=MCMID|03046338313294408994491125262632549756; dsch-visitorid=df500a73-6978-4cb1-8304-7ac78bf66420; _ga=GA1.1.680926352.1717544371; WTPERSIST=; BVBRANDID=d070da31-e752-4dec-8b32-14206376ab7b; da_lid=B080BCC79F6EEA11DBA9BB99F9B1AD2A81|0|0|0; _gcl_au=1.1.437141541.1725909899; _fbp=fb.2.1728522858882.291546507273648950; analyticsIsLoggedIn=false; _tracking_consent=%7B%22con%22%3A%7B%22CMP%22%3A%7B%22a%22%3A%22%22%2C%22m%22%3A%22%22%2C%22p%22%3A%22%22%2C%22s%22%3A%22%22%7D%7D%2C%22v%22%3A%222.1%22%2C%22region%22%3A%22AUNSW%22%2C%22reg%22%3A%22%22%2C%22purposes%22%3A%7B%22a%22%3Atrue%2C%22p%22%3Atrue%2C%22m%22%3Atrue%2C%22t%22%3Atrue%7D%2C%22display_banner%22%3Afalse%2C%22sale_of_data_region%22%3Afalse%7D; _shopify_y=81971ba2-0900-436e-a49a-6700fc9a832d; _orig_referrer=https%3A%2F%2Fwww.coles.com.au%2F; _landing_page=%2F; _ga_LST4E6STH8=GS1.1.1729581436.1.1.1729581511.0.0.0; nlbi_2800108_2670698=dHcJGdLBSUmgx8LwjQyMFgAAAADBvjidUvBljL+glJBPI0xp; incap_ses_808_2800108=HBHeAxeU3Vv/Vedo3Zc2C8tpGWcAAAAA0KXdD/8quI4+0otJmZj9wQ==; sessionId=a253b1b2-4af4-4927-aaf2-cc1e3f3b48a9; at_check=true; kndctr_0B3D037254C7DE490A4C98A6_AdobeOrg_identity=CiYwMzA0NjMzODMxMzI5NDQwODk5NDQ5MTEyNTI2MjYzMjU0OTc1NlIRCMX0_Kz-MRgBKgRBVVMzMAPwAbu8ldqrMg==; kndctr_0B3D037254C7DE490A4C98A6_AdobeOrg_cluster=aus3; s_ips=754; AMCVS_0B3D037254C7DE490A4C98A6%40AdobeOrg=1; AMCV_0B3D037254C7DE490A4C98A6%40AdobeOrg=179643557%7CMCIDTS%7C20019%7CMCMID%7C03046338313294408994491125262632549756%7CMCAAMLH-1730323544%7C8%7CMCAAMB-1730323544%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1729725944s%7CNONE%7CMCAID%7CNONE%7CMCSYNCSOP%7C411-20023%7CvVersion%7C5.5.0; s_cc=true; dsch-sessionid=26b87b51-af91-4930-a2f1-907469da1b1d; s_sq=%5B%5BB%5D%5D; s_tp=16915; ad-memory-token=MhHKIxGz%2BjKpb%2BAiACdYVmq7pKAKDhIMCKTh5bgGEJLkuP8BGgIIAiIA; mbox=PC#f46f1a1d06de4b21ad03bc1412216354.36_0#1792965292|session#44d39dd00e3b477a9819366132d7b9f1#1729722352; fs_uid=#o-210D95-na1#4e0419bc-e517-4c3d-85a7-11d92ea443d5:334fcb02-751c-46d6-8a15-ff2eced2771d:1729718737098::3#1dbf2fc5#/1760058930; s_ppv=cusp%253Abrowse%253Aproduct-categories%2C4%2C4%2C4%2C754%2C22%2C1; _ga_C8RCBCKHNM=GS1.1.1729718743.16.1.1729720496.60.0.0; fs_lua=1.1729720494573; nlbi_2800108_2147483392=UvOsEhUSTBw52R6ejQyMFgAAAADnoAPFKEvjlis1RGLWfWz8; reese84=3:bfCHUMtuIcu+TAtiN5H1qg==:CoBjx+7aUGeApbaCZPj3FSnukcUuVkG5SfOcTW50iKUh7ZGamSMN7EceEvEsfeeygWUiPAaYZ5R8qfoN6n5EGdjQkfPQYEka3350iGtR/VDCzlouKo2vP6jA71QadCTVNm2QgqpYTl2Hg9gODLrCmdF+6TodxrYeUqXoMm4jUAwlxGv4KjMR2Ce7v42glhhM93zXQzXIW/mkAgWmFjVXXMAFS0Vpz77lupLYkDZSSjy7db7YFJH6G1kMc/3twB3LZAlNzUS47xpEdVwNUNL2fa+CChQdHC/hW8NuY0SSMgkTG2A1QLBLQyy5LF3sYNTuFYO+hGKvhRY5k6PRJ7AjwueaWrQhsKKjYgbzkPwfEtFwkUe4k2MjirMXSZoLpiqfcDW42aWsXo9xqbZHW2iuF0v7+blas7u365k8VxSNhXptRcVvqh65KA/cHJPSqRNbBrfYr0cd+TNhHAujhc15xw==:oNuZL2JsIQi/sH2iXx5p/ETs0XVZ2K5fIx0yZ7iq/2s=",
        }
        return self.headers
