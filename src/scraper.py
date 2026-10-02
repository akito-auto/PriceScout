import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")


import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")


def scrape_page(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    products = []

    for item in soup.select("article.product_pod"):
        title_link = item.select_one("h3 a")

        title = title_link["title"]
        price = item.select_one(".price_color").get_text(strip=True)
        availability = item.select_one(".availability").get_text(strip=True)
        product_url = urljoin(url, title_link["href"])

        products.append(
            {
                "title": title,
                "price": price,
                "availability": availability,
                "url": product_url,
            }
        )

    next_link = soup.select_one("li.next a")

    if next_link:
        next_url = urljoin(url, next_link["href"])
    else:
        next_url = None

    return products, next_url


def scrape_all_products():
    all_products = []
    current_url = START_URL
    page_number = 1

    while current_url:
        print(f"Scraping page {page_number}...")

        products, next_url = scrape_page(current_url)

        all_products.extend(products)

        current_url = next_url
        page_number += 1

    return all_products


if __name__ == "__main__":
    products = scrape_all_products()

    print()
    print(f"Total products: {len(products)}")

    for product in products[:5]:
        print(product)