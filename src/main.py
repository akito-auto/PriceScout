from datetime import datetime
from pathlib import Path

import pandas as pd

from scraper import scrape_all_products
from analyzer import (
    create_clearance_report,
    compare_snapshots,
    load_latest_snapshots,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent

SNAPSHOTS_DIR = PROJECT_ROOT / "data" / "snapshots"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"


def save_csv(df, directory, filename):
    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / filename

    df.to_csv(
        file_path,
        index=False,
        encoding="utf-8-sig",
    )

    return file_path


def main():
    print("Starting PriceScout...")
    print()

    products = scrape_all_products()

    print()
    print(f"Total products: {len(products)}")

    current_df = pd.DataFrame(products)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    # 1. Save full snapshot
    snapshot_path = save_csv(
        current_df,
        SNAPSHOTS_DIR,
        f"products_{timestamp}.csv",
    )

    print(f"Snapshot saved: {snapshot_path}")

    # 2. Create clearance report
    clearance_df = create_clearance_report(current_df)

    clearance_path = save_csv(
        clearance_df,
        REPORTS_DIR,
        f"clearance_{timestamp}.csv",
    )

    print(
        f"Clearance products: {len(clearance_df)} "
        f"-> {clearance_path}"
    )

    # 3. Compare latest two snapshots
    previous_df, latest_df = load_latest_snapshots(
        SNAPSHOTS_DIR
    )

    if previous_df is None:
        print()
        print("No previous snapshot yet.")
        print("Run PriceScout again later to detect changes.")
        return

    new_products, price_changes = compare_snapshots(
        previous_df,
        latest_df,
    )

    new_products_path = save_csv(
        new_products,
        REPORTS_DIR,
        f"new_products_{timestamp}.csv",
    )

    price_changes_path = save_csv(
        price_changes,
        REPORTS_DIR,
        f"price_changes_{timestamp}.csv",
    )

    print()
    print(f"New products: {len(new_products)}")
    print(f"Price changes: {len(price_changes)}")

    print(f"New products report: {new_products_path}")
    print(f"Price changes report: {price_changes_path}")


if __name__ == "__main__":
    main()