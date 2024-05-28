import os
from dotenv import load_dotenv, find_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService


def initialize_driver(executable_path=None, headless=False):
    if executable_path is None:
        dotenv_path = find_dotenv()
        load_dotenv(dotenv_path)
        try:
            executable_path = os.environ["CHROMEDRIVER_PATH"]
        except KeyError as e:
            raise KeyError("Cannot find .env file with `CHROMEDRIVER_PATH`") from e

    service = ChromeService(executable_path=executable_path)
    service.start()
    options = webdriver.ChromeOptions()
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    if headless:
        options.add_argument("--headless")

    driver = webdriver.Remote(service.service_url, options=options)

    return driver, service
