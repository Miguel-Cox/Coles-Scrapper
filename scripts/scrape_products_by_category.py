import json
import os
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup


today = datetime.strftime(datetime.today(), "%Y%m%d")
DST_DIR = f"./data/raw/products-by-category/{today}"
DST_FILENAME_TEMPLATE = DST_DIR + "/{category}-products.json"
TARGET_CATEGORIES = [
    "fruit-vegetables",
    "dairy-eggs-fridge",
    "meat-seafood",
    "pantry",
    "household",
    "frozen",
    "health-beauty",
    "pet",
    "drinks",
    "deli",
    "baby",
    "liquor",
    "bakery",
]
MAX_PAGES = 300
SHORT_SLEEP_SECONDS = 3.5
MID_SLEEP_SECONDS = 10
LONG_SLEEP_SECONDS = 30


class _ProductCard:

    def __init__(self, card):
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


def refresh_headers():
    return {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "cookie": "visid_incap_2800108=e73PYei0RJGQXq5Vh+8R1KqlX2YAAAAAQUIPAAAAAADxo87wUDxalU5rQe1dAY8Q; ld_user=67edf4e5-d3ab-4cf8-b0c8-7c92ba112ab3; visitorId=5d26124b-b52c-4d4a-85e6-741dd3b5e47d; ai_user=lIr2U2pQD6FG1Y6lbWPJlt|2024-06-04T23:39:26.413Z; ORA_FPC=id=e356c497-367a-4400-8f8c-60ed6b5d3a5c; s_ecid=MCMID|03046338313294408994491125262632549756; dsch-visitorid=df500a73-6978-4cb1-8304-7ac78bf66420; _ga=GA1.1.680926352.1717544371; WTPERSIST=; BVBRANDID=d070da31-e752-4dec-8b32-14206376ab7b; da_lid=B080BCC79F6EEA11DBA9BB99F9B1AD2A81|0|0|0; _gcl_au=1.1.437141541.1725909899; _fbp=fb.2.1728522858882.291546507273648950; analyticsIsLoggedIn=false; kndctr_0B3D037254C7DE490A4C98A6_AdobeOrg_identity=CiYwMzA0NjMzODMxMzI5NDQwODk5NDQ5MTEyNTI2MjYzMjU0OTc1NlIRCMX0_Kz-MRgBKgRBVVMzMAPwAZ75hYmqMg==; nlbi_2800108_2670698=uJcHPtTxFjiOCyMQjQyMFgAAAAAFq8jUEizDPq5slpSpugpD; incap_ses_808_2800108=hl9lF/gxuhzHmmdl3Zc2CwaDE2cAAAAAvxUDeItRRytAZyFkeBLYig==; sessionId=098a4d32-0906-4ac4-9e63-fed02029f5fd; dsch-sessionid=fac089cd-d852-4e87-82d8-614867ee6921; at_check=true; reese84=3:lThBBXlI02gNLUwyVknebg==:DBeWnrOdbNjoIKJhLulzrQMhDNuDRhA3PkpOBRV93jmLSEft0sfFXE59ZM8mu1mYwnSBzBHx+z0/UHrnVo9TaJAATygkfqoeVOSbAWzYGkH6wo0awvog+Z5b5gCm5GMf+dOCT7L0cw1Hf3525kPxv08wDyy5gQtmtuls0UKaHLgaU1ylhq9Zb+6v9dhATjS1/uShZ0OKqaIERd+27BkBAV+k9lHappHLMBayKNsLbBuDqojeDCnTh7vU6/tpmtoV8VFalZrdOd6pNIa7e8g37EoxjdpSjNP6+nd0oboShWWoX4bMsVoEwEV4DRoCauMazLiUiywnQyx5g/aIF0aOJMrixkgKWFMZF/vVE8avDUWoaEsOymoHkIqbykgCoNh5nZPmIUYXVWbFTXO99d7QwLBRzVD4ocneQlYvEp++jfSj0JZuIsReYXQHhHuhd0iiICcoQqA9fi9gM9xvGGoc6g==:X3o0xH+VNtzJ+ufTqwm+ulrEDfOZ5eCpnXU0zV+OyuY=; s_ips=754; kndctr_0B3D037254C7DE490A4C98A6_AdobeOrg_cluster=aus3; AMCVS_0B3D037254C7DE490A4C98A6%40AdobeOrg=1; gpv_page=cusp%3Abrowse%3Aproduct-categories; s_cc=true; AMCV_0B3D037254C7DE490A4C98A6%40AdobeOrg=179643557%7CMCIDTS%7C20015%7CMCMID%7C03046338313294408994491125262632549756%7CMCAAMLH-1729936793%7C8%7CMCAAMB-1729936793%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1729339193s%7CNONE%7CMCAID%7CNONE%7CMCSYNCSOP%7C411-20023%7CvVersion%7C5.5.0; BVBRANDSID=04f23d7f-f33f-42a1-9679-73ec2fcbc9a4; ad-memory-token=RQuq8FzS0WQTnwNlxJo15iPyZjwKmgEKDBIKCggzMDIyMTY3UAoMEgoKCDI5OTkzMjdQCgwSCgoIMzAyMzIwNlAKDBIKCggyOTk3OTQ0UAoMEgoKCDI5OTkyNThQCgwSCgoIMjk5OTMxNlAKDBIKCggyOTk3OTk5UAoMEgoKCDI5OTkyMTRQCgwSCgoIMzUzODU5MFAKDBIKCggzMDExNTU3UBIMCJqHzrgGENzMhr4BGgIIAiIA; nlbi_2800108_2147483392=486QQzIoEmR6mBDOjQyMFgAAAABxTbS+LrY5ombUSE8vpY+J; mbox=PC#f46f1a1d06de4b21ad03bc1412216354.36_0#1792576935|session#51b13252ab8347ebbb341ca67b01a4e9#1729333996; fs_lua=1.1729332135583; fs_uid=#o-210D95-na1#4e0419bc-e517-4c3d-85a7-11d92ea443d5:0e419551-1ad3-4922-85a7-836d62d0a0e7:1729331982911::2#1dbf2fc5#/1760058894; _ga_C8RCBCKHNM=GS1.1.1729332020.12.1.1729332154.28.0.0; s_tp=17686; s_ppv=cusp%253Abrowse%253Aproduct-categories%2C4%2C4%2C4%2C754%2C23%2C1",
    }


def dump_products(category, products):
    os.makedirs(DST_DIR, exist_ok=True)
    products_file = DST_FILENAME_TEMPLATE.format(category=category)
    print(f"Saving {len(products)} products in '{products_file}'")
    with open(products_file, "w") as dst:
        json.dump(products, dst)


def get_products_from_category_page(category, page_num, headers):
    if page_num == 1:
        page_url = f"https://www.coles.com.au/browse/{category}"
    else:
        page_url = f"https://www.coles.com.au/browse/{category}?page={page_num}"
    resp = requests.get(page_url, headers=headers)

    if ("Incapsula" in str(resp.content)) or (
        "Pardon Our Interruption" in str(resp.content)
    ):
        print("Request blocked by bot detection measures.")
        raise ValueError("Bot detected!")

    soup = BeautifulSoup(resp.content, "html.parser")
    cards = soup.find_all("section", attrs={"data-testid": "product-tile"})
    products = [_ProductCard(card).to_dict() for card in cards]
    print(f"({category}) {len(products)} products found on page {page_num}")
    return products


def main():
    headers = refresh_headers()
    for category in TARGET_CATEGORIES:
        page_num = 1
        all_products = []
        while page_num <= MAX_PAGES:
            try:
                page_products = get_products_from_category_page(
                    category, page_num, headers=headers
                )
            except ValueError as e:
                print("Refreshing cookies...")
                time.sleep(LONG_SLEEP_SECONDS)
                headers = refresh_headers()
                time.sleep(MID_SLEEP_SECONDS)
                continue

            if not page_products:
                break

            all_products.extend(page_products)
            page_num += 1
            time.sleep(SHORT_SLEEP_SECONDS)

        if all_products:
            dump_products(category, products=all_products)


if __name__ == "__main__":
    main()
