from unittest.mock import Mock

import pytest
import requests

import scraper


def catalogue(href="book_1/index.html", next_href=None):
    html = f'''<article class="product_pod">
        <h3><a href="{href}" title="Full café title">Truncated title</a></h3>
        <p class="price_color">£10.81</p>
        <p class="availability">\n In stock \n</p>
    </article>'''
    if next_href is not None:
        html += f'<li class="next"><a href="{next_href}">next</a></li>'
    return html


def response(html, status=200):
    result = requests.Response()
    result.status_code = status
    result.url = scraper.START_URL
    result._content = html.encode("utf-8")
    return result


def test_scrape_page_parses_full_title_encoding_and_relative_links():
    session = Mock()
    session.get.return_value = response(catalogue(next_href="page-2.html"))
    products, next_url = scraper.scrape_page(scraper.START_URL, session=session)
    assert products == [{
        "title": "Full café title", "price": "£10.81", "availability": "In stock",
        "url": "https://books.toscrape.com/catalogue/book_1/index.html",
    }]
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"
    session.get.assert_called_once_with(scraper.START_URL, timeout=15)


def test_scrape_page_without_next_link(monkeypatch):
    monkeypatch.setattr(scraper.requests, "get", lambda *args, **kwargs: response(catalogue()))
    assert scraper.scrape_page(scraper.START_URL)[1] is None


@pytest.mark.parametrize("html, message", [
    ("<html>Unavailable</html>", "No products found"),
    (catalogue().replace('title="Full café title"', ""), "Missing product fields"),
    (catalogue(href=""), "Missing product fields"),
    (catalogue().replace('class="price_color"', 'class="other"'), "Missing product fields"),
    (catalogue().replace('class="availability"', 'class="other"'), "Missing product fields"),
    (catalogue(next_href=""), "Missing next-page URL"),
])
def test_bad_catalogue_pages_fail_with_url_context(html, message):
    session = Mock()
    session.get.return_value = response(html)
    with pytest.raises(ValueError, match=message) as error:
        scraper.scrape_page(scraper.START_URL, session=session)
    assert scraper.START_URL in str(error.value)


def test_http_errors_are_not_parsed_as_products():
    session = Mock()
    session.get.return_value = response(catalogue(), status=503)
    with pytest.raises(requests.HTTPError):
        scraper.scrape_page(scraper.START_URL, session=session)


def test_scrape_all_follows_pagination_and_reuses_session(monkeypatch):
    calls = []

    def get(session, url, **kwargs):
        calls.append((session, url))
        if url == scraper.START_URL:
            return response(catalogue(next_href="page-2.html"))
        return response(catalogue(href="book_2/index.html"))

    monkeypatch.setattr(requests.Session, "get", get)
    products = scraper.scrape_all_products()
    assert len(products) == 2
    assert [url for _, url in calls] == [scraper.START_URL, "https://books.toscrape.com/catalogue/page-2.html"]
    assert calls[0][0] is calls[1][0]


@pytest.mark.parametrize("next_href, message", [
    ("page-1.html", "Pagination loop"), ("page-2.html", "Duplicate product URL"),
])
def test_scrape_all_rejects_loops_and_duplicates(monkeypatch, next_href, message):
    monkeypatch.setattr(requests.Session, "get", lambda *args, **kwargs: response(catalogue(next_href=next_href)))
    with pytest.raises(ValueError, match=message):
        scraper.scrape_all_products()


def test_network_timeout_aborts_the_crawl(monkeypatch):
    def get(session, url, **kwargs):
        if url == scraper.START_URL:
            return response(catalogue(next_href="page-2.html"))
        raise requests.Timeout("timed out")

    monkeypatch.setattr(requests.Session, "get", get)
    with pytest.raises(requests.Timeout):
        scraper.scrape_all_products()
