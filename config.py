import os
import argparse
import logging
from typing import Dict

DEFAULT_PRODUCTS_FILE = "products.txt"
DEFAULT_PRICE_HISTORY_FILE = "price_history.csv"
DEFAULT_REPORT_FILE = "PRICES.md"
DEFAULT_MAX_HISTORY = 50
DEFAULT_MAX_ENTRIES_PER_PRODUCT = 20
DEFAULT_REQUEST_TIMEOUT = 20
DEFAULT_MAX_WORKERS = 4
DEFAULT_REQUEST_DELAY = 1.5
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 2

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.de/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

SOURCES: Dict[str, Dict] = {
    "Idealo": {
        "base_url": "https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={}",
        "selectors": [
            ".sr-resultItem__price",
            ".offerList-item-price",
            '[data-testid="product-price"]',
            ".price",
            ".oopStage-price",
            ".productOffers-list-itemInformerPriceButton",
        ],
    },
    "Billiger": {
        "base_url": "https://www.billiger.de/suche/{}",
        "selectors": [
            ".product-price",
            ".price",
            '[data-testid="product-price"]',
            ".offer-price",
            ".item-price",
        ],
    },
}


def parse_args():
    parser = argparse.ArgumentParser(description="Price Bot - Automated price tracker for idealo.de and billiger.de")
    parser.add_argument("--products", default=os.getenv("PRODUCTS_FILE", DEFAULT_PRODUCTS_FILE),
                        help=f"Products file (default: {DEFAULT_PRODUCTS_FILE})")
    parser.add_argument("--history", default=os.getenv("PRICE_HISTORY_FILE", DEFAULT_PRICE_HISTORY_FILE),
                        help=f"Price history CSV file (default: {DEFAULT_PRICE_HISTORY_FILE})")
    parser.add_argument("--report", default=os.getenv("REPORT_FILE", DEFAULT_REPORT_FILE),
                        help=f"Report output file (default: {DEFAULT_REPORT_FILE})")
    parser.add_argument("--max-history", type=int,
                        default=int(os.getenv("MAX_HISTORY", str(DEFAULT_MAX_HISTORY))),
                        help=f"Max history entries per product (default: {DEFAULT_MAX_HISTORY})")
    parser.add_argument("--max-workers", type=int,
                        default=int(os.getenv("MAX_WORKERS", str(DEFAULT_MAX_WORKERS))),
                        help=f"Max parallel workers (default: {DEFAULT_MAX_WORKERS})")
    parser.add_argument("--request-delay", type=float,
                        default=float(os.getenv("REQUEST_DELAY", str(DEFAULT_REQUEST_DELAY))),
                        help=f"Delay between source requests in seconds (default: {DEFAULT_REQUEST_DELAY})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run without saving data")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"),
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level (default: INFO)")
    return parser.parse_args()


def setup_logging(level: str):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(levelname)s %(message)s",
    )
