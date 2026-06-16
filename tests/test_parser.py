import pytest
from parser import parse_price


class TestParsePrice:
    def test_german_format(self):
        assert parse_price("1.299,00") == 1299.00
        assert parse_price("299,99") == 299.99
        assert parse_price("1.000,50") == 1000.50

    def test_english_format(self):
        assert parse_price("1,299.00") == 1299.00
        assert parse_price("299.99") == 299.99
        assert parse_price("1,000.50") == 1000.50

    def test_with_euro_symbol(self):
        assert parse_price("€1.299,00") == 1299.00
        assert parse_price("299,99 €") == 299.99
        assert parse_price("€ 1.000,50") == 1000.50

    def test_with_eur_text(self):
        assert parse_price("1.299,00 EUR") == 1299.00
        assert parse_price("EUR 299,99") == 299.99

    def test_whitespace_normalization(self):
        assert parse_price("1 299,00") == 1299.00
        assert parse_price("  299,99  ") == 299.99

    def test_none_or_empty(self):
        assert parse_price(None) is None
        assert parse_price("") is None
        assert parse_price("   ") is None

    def test_no_price_in_text(self):
        assert parse_price("No price available") is None
        assert parse_price("Out of stock") is None

    def test_integer_price(self):
        assert parse_price("1299") == 1299.0

    def test_decimal_with_trailing_zeros(self):
        assert parse_price("1.200,00") == 1200.00
        assert parse_price("0,99") == 0.99
