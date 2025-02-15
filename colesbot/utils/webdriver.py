import os

import undetected_chromedriver as uc
from dotenv import find_dotenv, load_dotenv
from seleniumwire.undetected_chromedriver.v2 import Chrome, ChromeOptions


def initialize_driver(executable_path=None, headless=False, implicit_wait: int = None):
    if executable_path is None:
        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)
        try:
            executable_path = os.environ["CHROMEDRIVER_PATH"]
        except KeyError as e:
            raise KeyError("Cannot find .env file with `CHROMEDRIVER_PATH`") from e
    options = uc.ChromeOptions()
    options.add_argument("--log-level=3")
    if headless:
        options.add_argument("--headless")

    driver = uc.Chrome(options=options, driver_executable_path=executable_path)
    if implicit_wait and isinstance(implicit_wait, (int, float)):
        driver.implicitly_wait(implicit_wait)

    return driver


def init_seleniumwire_webdriver():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    return Chrome(options=chrome_options)
