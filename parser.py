import logging
import re
import urllib.parse
from typing import Optional, Tuple

from bs4 import BeautifulSoup

from config import SOURCES
from fetcher import fetch_with_retry

logger = logging.getLogger(__name__)


def parse_price(text: Optional[str]) -> Optional[float]:
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    cleaned = text.replace("€", "").replace("EUR", "").strip()
    match = re.search(r"[\d.,]+", cleaned)
    if not match:
        return None
    num_str = match.group(0)
    has_dot = "." in num_str
    has_comma = "," in num_str
    if has_dot and has_comma:
        last_dot = num_str.rfind(".")
        last_comma = num_str.rfind(",")
        if last_comma > last_dot:
            num_str = num_str.replace(".", "").replace(",", ".")
        else:
            num_str = num_str.replace(",", "")
    elif has_comma:
        num_str = num_str.replace(",", ".")
    try:
        return float(num_str)
    except ValueError:
        return None


def find_first_price(soup: BeautifulSoup, selectors) -> Optional[float]:
    for sel in selectors:
        elem = soup.select_one(sel)
        if elem:
            price = parse_price(elem.get_text())
            if price:
                return price
    return None


def get_price(session, product_name: str, source_name: str,
              max_retries: int = 3, timeout: int = 20,
              retry_backoff: int = 2) -> Tuple[Optional[float], str]:
    source = SOURCES[source_name]
    query = urllib.parse.quote_plus(product_name)
    url = source["base_url"].format(query)
    logger.info("Searching %s.de...", source_name.lower())
    response = fetch_with_retry(session, url, max_retries, timeout, retry_backoff)
    if not response:
        return None, url
    soup = BeautifulSoup(response.content, "html.parser")
    price = find_first_price(soup, source["selectors"])
    if price:
        return price, url
    for elem in soup.find_all(string=lambda t: t and "€" in t):
        price = parse_price(elem)
        if price:
            return price, url
    return None, url
