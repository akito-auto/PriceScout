# PriceScout

PriceScout is a small Python web-scraping portfolio project. It crawls an online
catalogue, saves timestamped CSV snapshots, and compares consecutive runs to
identify new products and price changes.

It uses [Books to Scrape](https://books.toscrape.com/), a public scraping sandbox.

## Features

- Follows catalogue pagination and collects title, price, availability, and URL
- Saves full snapshots and reports as Excel-ready UTF-8 CSVs
- Reports prices whose final penny digit is `1` (for example, `£10.81`)
- Identifies new products by URL and compares prices numerically
- Rejects empty pages, missing product fields, pagination loops, and duplicate URLs
- Validates snapshot columns, URLs, and prices before analysis
- Reuses an HTTP session, checks HTTP status, and sets a 15-second request timeout
- Writes each CSV through a temporary file so a failed write cannot publish a partial CSV

The `clearance` report is just a demonstration of a price rule; it does not mean
the site labels those books as discounted.

## Project structure

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
│   ├── conftest.py
│   ├── test_analyzer.py
│   ├── test_main.py
│   └── test_scraper.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Installation

Use Python 3.11 or newer. Create and activate a virtual environment on Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux, activate with `source .venv/bin/activate` instead.

## Usage

```powershell
python src/main.py
```

Output files are stored relative to the project directory, regardless of the
terminal's current directory:

- `data/snapshots/products_<timestamp>.csv`: all products
- `data/reports/clearance_<timestamp>.csv`: products matching the price rule
- `data/reports/new_products_<timestamp>.csv`: URLs absent from the previous snapshot
- `data/reports/price_changes_<timestamp>.csv`: changed prices, including `old_price`

Timestamps include microseconds to keep runs started in the same second separate.
Existing snapshots with second-only timestamps remain supported. The first run
saves a snapshot and clearance report; later runs also produce comparison reports.
Reports with no matches still contain column headers.

A successful crawl of the sandbox normally contains 50 pages and 1,000 books.
Counts and matching prices can change if the sandbox data changes.

Network or parsing failures abort the crawl before any snapshot is saved. Expected
errors print a short message and return a nonzero exit code. Corrupt snapshots are
rejected rather than silently skipped; inspect or move the affected file before
retrying. Each CSV is written atomically, but all files from a run are not a single
transaction.

## Testing

```powershell
python -m pytest -q
```

Tests use local HTML and temporary CSVs; they do not need network access. They cover
pagination, parsing, HTTP failures and timeouts, invalid data, price rules,
snapshot selection, comparison reports, and failed file writes.

## Scope

The project deliberately uses three small modules with Requests, BeautifulSoup,
and Pandas. It targets this sandbox's HTML and GBP prices. Removed products and
availability changes are not reported. There is no scheduling or automatic retry;
rerun the command after a transient failure. Generated data is ignored by Git.
