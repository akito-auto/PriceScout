# PriceScout

PriceScout is a small Python web-scraping and product monitoring project.

It crawls an online catalogue, stores timestamped product snapshots, detects products matching a price rule, and compares consecutive runs to identify new products and price changes.

The project uses [Books to Scrape](https://books.toscrape.com/) as a safe public scraping sandbox.

## Features

- Automatically follows pagination until no pages remain
- Collects:
  - product title
  - price
  - availability
  - product URL
- Saves timestamped CSV snapshots
- Detects prices ending in `1`
- Detects newly added products
- Detects price changes between runs
- Exports reports as UTF-8 CSV files
- Includes automated tests

## Project Structure

```text
PriceScout/
├── data/
│   ├── reports/
│   └── snapshots/
├── src/
│   ├── analyzer.py
│   ├── main.py
│   └── scraper.py
├── tests/
│   └── test_analyzer.py
├── .gitignore
├── README.md
└── requirements.txt

Installation
Create a virtual environment:
python -m venv .venv

Activate it on Windows:
.venv\Scripts\activate

Install dependencies:
pip install -r requirements.txt

Usage
Run PriceScout:
python src/main.py

Example output:
Starting PriceScout...

Scraping page 1...
...
Scraping page 50...

Total products: 1000
Clearance products: 102
New products: 0
Price changes: 0

Generated files are stored in:
data/snapshots/
data/reports/

Reports
PriceScout can generate:
- Full product snapshots
- Clearance-price reports
- Newly added product reports
- Price-change reports
Testing
Run:
pytest -q

Example:
1 passed

Tech Stack
- Python
- Requests
- BeautifulSoup
- Pandas
- Pytest
Purpose
This project demonstrates a reusable approach to:
- product monitoring
- web scraping
- daily catalogue snapshots
- detecting newly listed products
- detecting price changes
- generating CSV/Excel-ready reports