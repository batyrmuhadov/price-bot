import csv
import logging
import os
import tempfile
import shutil
from typing import List, Optional, Dict

try:
    import tomllib
except ImportError:
    import tomli as tomllib

logger = logging.getLogger(__name__)


def load_products(filepath: str) -> List[Dict]:
    products = []
    if not os.path.exists(filepath):
        logger.warning("Products file '%s' not found.", filepath)
        return products
    with open(filepath, "rb") as f:
        data = tomllib.load(f)
    for entry in data.get("products", []):
        products.append({
            "name": entry["name"],
            "target_price": entry.get("target_price"),
        })
    return products


def load_history(filepath: str) -> List[List[str]]:
    if not os.path.exists(filepath):
        return []
    rows = []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if row:
                rows.append(row)
    return rows


def get_last_price(rows: List[List[str]], product_name: str, website: str) -> Optional[float]:
    for row in reversed(rows):
        _, p_name, price_str, source = row
        if p_name == product_name and source == website:
            try:
                if price_str.isdigit():
                    return float(price_str) / 100
                return float(price_str)
            except ValueError:
                continue
    return None


def prices_differ(p1: Optional[float], p2: Optional[float]) -> bool:
    if p1 is None and p2 is None:
        return False
    if p1 is None or p2 is None:
        return True
    return abs(p1 - p2) > 0.001


def append_price_history(filepath: str, timestamp: str,
                         product_name: str, price: float, website: str):
    is_new_file = not os.path.exists(filepath)
    with open(filepath, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(["Timestamp", "Product", "Price", "Website"])
        writer.writerow([timestamp, product_name, f"{price:.2f}", website])


def trim_csv(filepath: str, max_entries: int):
    if not os.path.exists(filepath):
        return
    rows = []
    header = None
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if row:
                rows.append(row)
    if len(rows) <= max_entries:
        logger.info("History has %d entries (<= %d). No trimming needed.", len(rows), max_entries)
        return
    products_data = {}
    for row in rows:
        product = row[1]
        products_data.setdefault(product, []).append(row)
    trimmed = []
    for product, entries in products_data.items():
        trimmed.extend(entries[-max_entries:])
    order = {id(r): i for i, r in enumerate(rows)}
    trimmed.sort(key=lambda r: order[id(r)])
    if trimmed == rows:
        logger.info("Trimmed history to last %d entries per product.", max_entries)
        return
    fd, tmp_path = tempfile.mkstemp(suffix=".csv", dir=os.path.dirname(filepath) or ".")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if header:
                writer.writerow(header)
            writer.writerows(trimmed)
        shutil.move(tmp_path, filepath)
        logger.info("Trimmed history to last %d entries per product.", max_entries)
    except Exception:
        os.unlink(tmp_path)
        raise
