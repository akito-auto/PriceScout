from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
START_URL = urljoin(BASE_URL, "catalogue/page-1.html")


def scrape_page(url, session=None):
    client = session if session is not None else requests
    response = client.get(url, timeout=15)
    response.raise_for_status()
    response.encoding = "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")
    products = []

    items = soup.select("article.product_pod")
    if not items:
        raise ValueError(f"No products found on catalogue page: {url}")

    for item in items:
        title_link = item.select_one("h3 a")
        price_element = item.select_one(".price_color")
        availability_element = item.select_one(".availability")
        if (
            title_link is None
            or not title_link.get("title", "").strip()
            or not title_link.get("href", "").strip()
            or price_element is None
            or not price_element.get_text(strip=True)
            or availability_element is None
            or not availability_element.get_text(strip=True)
        ):
            raise ValueError(f"Missing product fields on catalogue page: {url}")

        title = title_link["title"]
        price = price_element.get_text(strip=True)
        availability = availability_element.get_text(strip=True)
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
        if not next_link.get("href", "").strip():
            raise ValueError(f"Missing next-page URL on catalogue page: {url}")
        next_url = urljoin(url, next_link["href"])
    else:
        next_url = None

    return products, next_url


def scrape_all_products():
    all_products = []
    current_url = START_URL
    page_number = 1
    visited_pages = set()
    product_urls = set()

    with requests.Session() as session:
        while current_url:
            if current_url in visited_pages:
                raise ValueError(f"Pagination loop detected: {current_url}")
            visited_pages.add(current_url)
            print(f"Scraping page {page_number}...")

            products, next_url = scrape_page(current_url, session=session)
            for product in products:
                if product["url"] in product_urls:
                    raise ValueError(f"Duplicate product URL: {product['url']}")
                product_urls.add(product["url"])

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
