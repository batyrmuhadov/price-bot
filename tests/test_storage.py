import tempfile
import os
import csv
import pytest

from storage import (
    load_products, load_sources, load_history, get_last_price,
    prices_differ, append_price_history, trim_csv,
)


class TestLoadSources:
    def test_load_valid_sources(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            f.write('[[sources]]\n')
            f.write('name = "TestSite"\n')
            f.write('base_url = "https://example.com/search?q={}"\n')
            f.write('selectors = [".price", ".cost"]\n')
            f.flush()
            path = f.name
        try:
            sources = load_sources(path)
            assert len(sources) == 1
            assert "TestSite" in sources
            assert sources["TestSite"]["base_url"] == "https://example.com/search?q={}"
            assert sources["TestSite"]["selectors"] == [".price", ".cost"]
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        assert load_sources("/nonexistent/sources.toml") == {}

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            f.write('')
            f.flush()
            path = f.name
        try:
            assert load_sources(path) == {}
        finally:
            os.unlink(path)


class TestLoadProducts:
    def test_load_valid_products(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            f.write('[[products]]\n')
            f.write('name = "Product A"\n')
            f.write('target_price = 100.0\n')
            f.write('\n')
            f.write('[[products]]\n')
            f.write('name = "Product B"\n')
            f.write('target_price = 200.50\n')
            f.write('\n')
            f.write('[[products]]\n')
            f.write('name = "Product D"\n')
            f.flush()
            path = f.name
        try:
            products = load_products(path)
            assert len(products) == 3
            assert products[0] == {"name": "Product A", "target_price": 100.0}
            assert products[1] == {"name": "Product B", "target_price": 200.50}
            assert products[2] == {"name": "Product D", "target_price": None}
        finally:
            os.unlink(path)

    def test_file_not_found(self):
        products = load_products("/nonexistent/path.toml")
        assert products == []


class TestLoadHistory:
    def test_load_empty_file(self):
        assert load_history("/nonexistent.csv") == []

    def test_load_with_data(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("Timestamp,Product,Price,Website\n")
            f.write("2024-01-01,A,10.00,Idealo\n")
            f.write("2024-01-02,B,20.00,Billiger\n")
            f.flush()
            path = f.name
        try:
            rows = load_history(path)
            assert len(rows) == 2
            assert rows[0] == ["2024-01-01", "A", "10.00", "Idealo"]
            assert rows[1] == ["2024-01-02", "B", "20.00", "Billiger"]
        finally:
            os.unlink(path)


class TestGetLastPrice:
    def test_finds_last_price(self):
        rows = [
            ["2024-01-01", "Product A", "100.00", "Idealo"],
            ["2024-01-02", "Product A", "95.00", "Idealo"],
            ["2024-01-03", "Product A", "90.00", "Billiger"],
        ]
        assert get_last_price(rows, "Product A", "Idealo") == 95.00

    def test_handles_cents_format(self):
        rows = [
            ["2024-01-01", "Product A", "159990", "Amazon"],
        ]
        assert get_last_price(rows, "Product A", "Amazon") == 1599.90

    def test_no_match_returns_none(self):
        rows = [
            ["2024-01-01", "Product A", "100.00", "Idealo"],
        ]
        assert get_last_price(rows, "Product B", "Idealo") is None
        assert get_last_price(rows, "Product A", "Billiger") is None


class TestPricesDiffer:
    def test_same_price(self):
        assert prices_differ(100.0, 100.0) is False
        assert prices_differ(None, None) is False

    def test_different_price(self):
        assert prices_differ(100.0, 110.0) is True
        assert prices_differ(100.0, None) is True
        assert prices_differ(None, 100.0) is True


class TestAppendPriceHistory:
    def test_appends_and_creates_header(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            path = f.name
        try:
            append_price_history(path, "2024-01-01", "Product A", 100.0, "Idealo")
            with open(path, "r", newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
            assert len(rows) == 2
            assert rows[0] == ["Timestamp", "Product", "Price", "Website"]
            assert rows[1][0] == "2024-01-01"
            assert rows[1][1] == "Product A"
            assert rows[1][2] == "100.00"
            assert rows[1][3] == "Idealo"
        finally:
            os.unlink(path)

    def test_appends_to_existing(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("Timestamp,Product,Price,Website\n")
            f.write("2024-01-01,A,10.00,Idealo\n")
            f.flush()
            path = f.name
        try:
            append_price_history(path, "2024-01-02", "B", 20.0, "Billiger")
            with open(path, "r", newline="") as f:
                rows = list(csv.reader(f))
            assert len(rows) == 3
            assert rows[2][1] == "B"
        finally:
            os.unlink(path)


class TestTrimCsv:
    def test_trim_per_product(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            f.write("Timestamp,Product,Price,Website\n")
            for i in range(10):
                f.write(f"2024-01-{i+1:02d},A,{10+i}.00,Idealo\n")
            for i in range(10):
                f.write(f"2024-01-{i+1:02d},B,{20+i}.00,Billiger\n")
            f.flush()
            path = f.name
        try:
            trim_csv(path, 3)
            rows = []
            with open(path, "r", newline="") as f:
                reader = csv.reader(f)
                header = next(reader)
                for row in reader:
                    rows.append(row)
            assert len(rows) == 6
            product_a = [r for r in rows if r[1] == "A"]
            product_b = [r for r in rows if r[1] == "B"]
            assert len(product_a) == 3
            assert len(product_b) == 3
            assert product_a[-1] == ["2024-01-10", "A", "19.00", "Idealo"]
        finally:
            os.unlink(path)
