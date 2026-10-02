from datetime import datetime
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

import pandas as pd
import requests

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

    # Publish only complete CSVs so a failed write cannot become a snapshot.
    with NamedTemporaryFile(dir=directory, suffix=".tmp", delete=False) as temp:
        temporary_path = Path(temp.name)
    try:
        df.to_csv(temporary_path, index=False, encoding="utf-8-sig")
        temporary_path.replace(file_path)
    finally:
        temporary_path.unlink(missing_ok=True)

    return file_path


def main():
    print("Starting PriceScout...")
    print()

    products = scrape_all_products()

    print()
    print(f"Total products: {len(products)}")

    current_df = pd.DataFrame(products)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")

    # Validate the full result before saving anything from this run.
    clearance_df = create_clearance_report(current_df)

    # 1. Save full snapshot
    snapshot_path = save_csv(
        current_df,
        SNAPSHOTS_DIR,
        f"products_{timestamp}.csv",
    )

    print(f"Snapshot saved: {snapshot_path}")

    # 2. Create clearance report
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
    try:
        main()
    except (requests.RequestException, OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"PriceScout failed: {exc}", file=sys.stderr)
        sys.exit(1)
