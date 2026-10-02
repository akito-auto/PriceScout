from pathlib import Path
import sys

import pandas as pd


sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

from analyzer import create_clearance_report, compare_snapshots


def test_reports_detect_changes():
    previous_df = pd.DataFrame(
        [
            {
                "title": "Book A",
                "price": "£10.80",
                "availability": "In stock",
                "url": "https://example.com/a",
            },
            {
                "title": "Book B",
                "price": "£5.00",
                "availability": "In stock",
                "url": "https://example.com/b",
            },
        ]
    )

    current_df = pd.DataFrame(
        [
            {
                "title": "Book A",
                "price": "£10.81",
                "availability": "In stock",
                "url": "https://example.com/a",
            },
            {
                "title": "Book B",
                "price": "£5.00",
                "availability": "In stock",
                "url": "https://example.com/b",
            },
            {
                "title": "Book C",
                "price": "£4.91",
                "availability": "In stock",
                "url": "https://example.com/c",
            },
        ]
    )

    clearance = create_clearance_report(current_df)

    new_products, price_changes = compare_snapshots(
        previous_df,
        current_df,
    )

    assert set(clearance["url"]) == {
        "https://example.com/a",
        "https://example.com/c",
    }

    assert list(new_products["url"]) == [
        "https://example.com/c",
    ]

    assert list(price_changes["url"]) == [
        "https://example.com/a",
    ]

    assert price_changes.iloc[0]["old_price"] == "£10.80"
    assert price_changes.iloc[0]["price"] == "£10.81"