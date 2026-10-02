import pandas as pd
import pytest
import requests

import main


PRODUCT = {
    "title": "Café", "price": "£10.81", "availability": "In stock",
    "url": "https://example.com/a",
}


def test_main_creates_snapshots_and_reports_on_consecutive_runs(tmp_path, monkeypatch, capsys):
    snapshots = tmp_path / "snapshots"
    reports = tmp_path / "reports"
    monkeypatch.setattr(main, "SNAPSHOTS_DIR", snapshots)
    monkeypatch.setattr(main, "REPORTS_DIR", reports)
    monkeypatch.setattr(main, "scrape_all_products", lambda: [PRODUCT.copy()])
    clock = Mock()
    clock.now.side_effect = [
        datetime(2026, 1, 1, 12, 0, 0, 1),
        datetime(2026, 1, 1, 12, 0, 0, 2),
    ]
    monkeypatch.setattr(main, "datetime", clock)
    main.main()
    assert "No previous snapshot yet" in capsys.readouterr().out
    assert len(list(snapshots.glob("products_*.csv"))) == 1
    assert len(list(reports.glob("*.csv"))) == 1

    monkeypatch.setattr(main, "scrape_all_products", lambda: [
        {**PRODUCT, "price": "£10.91"}, {**PRODUCT, "url": "https://example.com/b"},
    ])
    main.main()
    assert sorted(path.name for path in snapshots.glob("products_*.csv")) == [
        "products_2026-01-01_12-00-00_000001.csv",
        "products_2026-01-01_12-00-00_000002.csv",
    ]
    new = pd.read_csv(next(reports.glob("new_products_*.csv")))
    changes = pd.read_csv(next(reports.glob("price_changes_*.csv")))
    assert list(new["url"]) == ["https://example.com/b"]
    assert list(changes["old_price"]) == ["£10.81"]
    assert list(changes["price"]) == ["£10.91"]


@pytest.mark.parametrize("products", [[], [{**PRODUCT, "price": "invalid"}]])
def test_main_does_not_save_invalid_scrapes(tmp_path, monkeypatch, products):
    monkeypatch.setattr(main, "SNAPSHOTS_DIR", tmp_path / "snapshots")
    monkeypatch.setattr(main, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(main, "scrape_all_products", lambda: products)
    with pytest.raises(ValueError):
        main.main()
    assert not list(tmp_path.rglob("*.csv"))


def test_failed_scrape_does_not_save_partial_snapshot(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "SNAPSHOTS_DIR", tmp_path / "snapshots")
    monkeypatch.setattr(main, "REPORTS_DIR", tmp_path / "reports")

    def scrape():
        raise requests.Timeout("second page failed")

    monkeypatch.setattr(main, "scrape_all_products", scrape)
    with pytest.raises(requests.Timeout):
        main.main()
    assert not list(tmp_path.rglob("*.csv"))


def test_failed_csv_write_preserves_existing_file_and_cleans_temp(tmp_path, monkeypatch):
    target = tmp_path / "products.csv"
    target.write_text("existing snapshot", encoding="utf-8")

    def fail(self, path, **kwargs):
        path.write_text("partial write", encoding="utf-8")
        raise OSError("disk full")

    monkeypatch.setattr(pd.DataFrame, "to_csv", fail)
    with pytest.raises(OSError, match="disk full"):
        main.save_csv(pd.DataFrame([PRODUCT]), tmp_path, target.name)
    assert target.read_text(encoding="utf-8") == "existing snapshot"
    assert list(tmp_path.iterdir()) == [target]


def test_csv_is_excel_ready_and_round_trips_unicode(tmp_path):
    target = main.save_csv(pd.DataFrame([PRODUCT]), tmp_path / "nested", "products.csv")
    assert target.read_bytes().startswith(b"\xef\xbb\xbf")
    assert pd.read_csv(target).iloc[0].to_dict() == PRODUCT
from datetime import datetime
from unittest.mock import Mock

