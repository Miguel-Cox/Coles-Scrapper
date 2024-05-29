# Coles Scraper

Coles Scraper is web scraping tool designed to automate the extraction of product details from the [Coles](https://www.coles.com.au/) website. This project uses [Selenium](https://www.selenium.dev/) for browser automation, following the [Page Object Model](https://www.browserstack.com/guide/page-object-model-in-selenium#:~:text=Page%20Object%20Model%2C%20also%20known,application%20as%20a%20class%20file.) pattern to structure the code.

**Disclaimer**: This is a hobby project for my personal portfolio. Please scrape responsibly and adhere to website terms of service.

## Setup

1. Clone the repository:

    ```sh
    git clone https://github.com/abhinav-pandey29/coles-scraper.git
    cd coles-scraper
    ```

2. Create a virtual environment and activate it:

    ```sh
    python3 -m venv env
    env/Scripts/activate
    ```

3. Install the required dependencies:

    ```sh
    pip install -r requirements.txt
    ```

4. Download ChromeDriver:
    - Go to the [ChromeDriver download page](https://sites.google.com/a/chromium.org/chromedriver/downloads).
    - Download the version that matches your installed version of Google Chrome.
    - Extract the downloaded file and note the path to the `chromedriver` executable.

5. Create a `.env` file in the project root directory and add the path to `chromedriver`:

    ```sh
    echo "CHROMEDRIVER_PATH=/path/to/your/chromedriver" > .env
    ```

## Usage

### CategoriesPage

```python
from utils.webdriver import initialize_webdriver
from pages.categories import CategoriesPage

driver = intialize_webdriver()

categories_page = CategoriesPage(driver)
categories_page.open()
```

Result of `categories_page.list_categories()`

```json
[
    {
        "name": "Meat & Seafood",
        "url": "https://www.coles.com.au/browse/meat-seafood",
        "slug": "meat-seafood"
    },
    {
        "name": "Fruit & Vegetables",
        "url": "https://www.coles.com.au/browse/fruit-vegetables",
        "slug": "fruit-vegetables"
    },
    {
        "name": "Dairy, Eggs & Fridge",
        "url": "https://www.coles.com.au/browse/dairy-eggs-fridge",
        "slug": "dairy-eggs-fridge"
    },
    {
        "name": "Bakery",
        "url": "https://www.coles.com.au/browse/bakery",
        "slug": "bakery"
    }
]
```

### ProductsPage

```python
from utils.webdriver import initialize_webdriver
from pages.products import ProductsPage

driver = intialize_webdriver()

# Create an instance of ProductsPage for scraping fruits and vegetables category on page 3
products_page = ProductsPage(
    driver,
    category="fruits-vegetables",
    page=3,
    )
products_page.open()
```

Result of `products_page.list_products()`

```json
[
    {
        "name": "Coles Bananas | approx 170g",
        "url": "https://www.coles.com.au/product/coles-bananas-approx.-170g-409499",
        "price": "$0.68",
        "price_calc_method": "$4.00 per 1kg",
        "price_calc_desc": "Final price is based on weight",
        "image_url": "https://www.coles.com.au/_next/image?url=https%3A%2F%2Fproductimages.coles.com.au%2Fproductimages%2F4%2F409499.jpg&w=640&q=90"
    },
    {
        "name": "Coles Bananas Mini Pack | 750g",
        "url": "https://www.coles.com.au/product/coles-bananas-mini-pack-750g-2511791",
        "price": "$4.00",
        "price_calc_method": "$5.33 per 1kg",
        "price_calc_desc": null,
        "image_url": "https://www.coles.com.au/_next/image?url=https%3A%2F%2Fproductimages.coles.com.au%2Fproductimages%2F2%2F2511791.jpg&w=640&q=90"
    },
    {
        "name": "Coles Strawberries | 250g",
        "url": "https://www.coles.com.au/product/coles-strawberries-250g-5191256",
        "price": "$6.00",
        "price_calc_method": "$24.00 per 1kg",
        "price_calc_desc": null,
        "image_url": "https://www.coles.com.au/_next/image?url=https%3A%2F%2Fproductimages.coles.com.au%2Fproductimages%2F5%2F5191256.jpg&w=640&q=90"
    },
    {
        "name": "Coles Blueberries Prepacked | 125g",
        "url": "https://www.coles.com.au/product/coles-blueberries-prepacked-125g-5543535",
        "price": "$8.90",
        "price_calc_method": "$71.20 per 1kg",
        "price_calc_desc": null,
        "image_url": "https://www.coles.com.au/_next/image?url=https%3A%2F%2Fproductimages.coles.com.au%2Fproductimages%2F5%2F5543535.jpg&w=640&q=90"
    }
]
```

### Scripts

- [`scrape_categories.py`](scrape_categories.py): Script to scrape all available categories from the Coles website.
- [`scrape_products.py`](scrape_products.py): Script to scrape all available products for a user-specified `TARGET_CATEGORY` from the Coles website.
