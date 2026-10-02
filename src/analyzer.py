from decimal import Decimal
from pathlib import Path
import re

import pandas as pd


def parse_price(price_text):
    """Parse non-negative GBP amounts without silently truncating fractions."""
    if not isinstance(price_text, str) or not re.fullmatch(
        r"£?\d+(?:\.\d{1,2})?", price_text.strip()
    ):
        raise ValueError(f"Invalid GBP price: {price_text!r}")
    return Decimal(price_text.strip().removeprefix("£"))


def validate_snapshot(df):
    required = {"title", "price", "availability", "url"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Snapshot is missing columns: {', '.join(sorted(missing))}")
    if not df["url"].map(lambda url: isinstance(url, str) and bool(url.strip())).all():
        raise ValueError("Snapshot contains empty or invalid product URLs")
    if df["url"].duplicated().any():
        raise ValueError("Snapshot contains duplicate product URLs")
    df["price"].map(parse_price)


def price_ends_in_one(price_text):
    price = parse_price(price_text)

    price_in_cents = int(price * 100)

    return price_in_cents % 10 == 1


def create_clearance_report(df):
    validate_snapshot(df)
    mask = df["price"].apply(price_ends_in_one).astype(bool)
    clearance = df.loc[mask].copy()

    return clearance


def compare_snapshots(previous_df, current_df):
    validate_snapshot(previous_df)
    validate_snapshot(current_df)
    previous_urls = set(previous_df["url"])

    new_products = current_df[
        ~current_df["url"].isin(previous_urls)
    ].copy()

    previous_prices = previous_df[
        ["url", "price"]
    ].rename(columns={"price": "old_price"})

    merged = current_df.merge(
        previous_prices,
        on="url",
        how="inner",
        validate="one_to_one",
    )

    price_changes = merged[
        merged["price"].map(parse_price) != merged["old_price"].map(parse_price)
    ].copy()

    return new_products, price_changes


def load_latest_snapshots(snapshot_dir):
    snapshot_dir = Path(snapshot_dir)

    files = sorted(snapshot_dir.glob("products_*.csv"))

    if len(files) < 2:
        return None, None

    previous_file = files[-2]
    current_file = files[-1]

    # Preserve literal text such as a book titled "NA" when reading CSVs.
    previous_df = pd.read_csv(previous_file, dtype=str, keep_default_na=False)
    current_df = pd.read_csv(current_file, dtype=str, keep_default_na=False)
    validate_snapshot(previous_df)
    validate_snapshot(current_df)

    return previous_df, current_df
