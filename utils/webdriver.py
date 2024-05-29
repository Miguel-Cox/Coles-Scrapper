import os
from dotenv import load_dotenv, find_dotenv
import undetected_chromedriver as uc


def initialize_driver(executable_path=None, headless=False):
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

    return driver
