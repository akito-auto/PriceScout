import pandas as pd
import pytest

from analyzer import (
    compare_snapshots,
    create_clearance_report,
    load_latest_snapshots,
    price_ends_in_one,
)


def snapshot(price="£10.81", url="https://example.com/a", title="Book A"):
    return pd.DataFrame([
        {"title": title, "price": price, "availability": "In stock", "url": url}
    ])


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


@pytest.mark.parametrize("price, expected", [
    ("£10.81", True), (" £4.91 ", True), ("0.01", True),
    ("£10.80", False), ("£11", False), ("£1.10", False),
])
def test_price_rule_uses_last_penny_digit(price, expected):
    assert price_ends_in_one(price) is expected


@pytest.mark.parametrize("price", [
    "", "£", "£1.011", "£-1.01", "NaN", "Infinity", "££1.01", None, 1.01,
])
def test_invalid_prices_are_rejected(price):
    with pytest.raises(ValueError, match="Invalid GBP price"):
        price_ends_in_one(price)


def test_comparison_uses_numeric_prices_and_does_not_mutate_inputs():
    previous = snapshot("£10.8")
    current = snapshot("10.80", title="Changed title")
    original_previous = previous.copy(deep=True)
    original_current = current.copy(deep=True)
    new, changed = compare_snapshots(previous, current)
    assert new.empty
    assert changed.empty
    pd.testing.assert_frame_equal(previous, original_previous)
    pd.testing.assert_frame_equal(current, original_current)


def test_empty_snapshots_keep_report_columns():
    empty = snapshot().iloc[:0]
    new, changed = compare_snapshots(empty, snapshot())
    assert len(new) == 1
    assert changed.empty
    assert "old_price" in changed.columns
    new, changed = compare_snapshots(snapshot(), empty)
    assert new.empty and changed.empty
    assert list(create_clearance_report(empty).columns) == list(empty.columns)


@pytest.mark.parametrize("invalid, message", [
    (snapshot().drop(columns="price"), "missing columns"),
    (pd.concat([snapshot(), snapshot()]), "duplicate product URLs"),
    (snapshot(url=""), "invalid product URLs"),
    (snapshot(url=None), "invalid product URLs"),
    (snapshot(price="bad"), "Invalid GBP price"),
])
def test_invalid_snapshots_fail_clearly(invalid, message):
    with pytest.raises(ValueError, match=message):
        compare_snapshots(invalid, snapshot())
    with pytest.raises(ValueError, match=message):
        compare_snapshots(snapshot(), invalid)


def test_load_latest_snapshots_uses_timestamp_order_and_preserves_text(tmp_path):
    snapshot("£1.00", title="NA").to_csv(tmp_path / "products_2026-01-01_00-00-00.csv", index=False)
    # Write out of order; both legacy and microsecond timestamps are supported.
    snapshot("£3.00").to_csv(tmp_path / "products_2026-01-03_00-00-00_000001.csv", index=False)
    snapshot("£2.00", title="NA").to_csv(tmp_path / "products_2026-01-02_00-00-00.csv", index=False)
    snapshot("£99.00").to_csv(tmp_path / "clearance_2026-01-04.csv", index=False)
    previous, current = load_latest_snapshots(tmp_path)
    assert previous.iloc[0]["price"] == "£2.00"
    assert previous.iloc[0]["title"] == "NA"
    assert current.iloc[0]["price"] == "£3.00"


def test_load_latest_snapshots_requires_two_files(tmp_path):
    assert load_latest_snapshots(tmp_path / "missing") == (None, None)
    snapshot().to_csv(tmp_path / "products_2026-01-01.csv", index=False)
    assert load_latest_snapshots(tmp_path) == (None, None)


def test_load_latest_snapshots_rejects_corrupt_data(tmp_path):
    snapshot().to_csv(tmp_path / "products_2026-01-01.csv", index=False)
    snapshot(price="broken").to_csv(tmp_path / "products_2026-01-02.csv", index=False)
    with pytest.raises(ValueError, match="Invalid GBP price"):
        load_latest_snapshots(tmp_path)
