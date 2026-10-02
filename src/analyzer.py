from decimal import Decimal
from pathlib import Path

import pandas as pd


def price_ends_in_one(price_text):
    clean_price = price_text.replace("£", "").strip()
    price = Decimal(clean_price)

    price_in_cents = int(price * 100)

    return price_in_cents % 10 == 1


def create_clearance_report(df):
    clearance = df[df["price"].apply(price_ends_in_one)].copy()

    return clearance


def compare_snapshots(previous_df, current_df):
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
    )

    price_changes = merged[
        merged["price"] != merged["old_price"]
    ].copy()

    return new_products, price_changes


def load_latest_snapshots(snapshot_dir):
    snapshot_dir = Path(snapshot_dir)

    files = sorted(snapshot_dir.glob("products_*.csv"))

    if len(files) < 2:
        return None, None

    previous_file = files[-2]
    current_file = files[-1]

    previous_df = pd.read_csv(previous_file)
    current_df = pd.read_csv(current_file)

    return previous_df, current_df