import datetime
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from config import (
    SOURCES, parse_args, setup_logging,
    DEFAULT_MAX_RETRIES, DEFAULT_RETRY_BACKOFF, DEFAULT_REQUEST_TIMEOUT,
)
from fetcher import create_session
from parser import get_price
from storage import (
    load_products, load_history, get_last_price,
    prices_differ, append_price_history, trim_csv,
)
from reporter import generate_readme

logger = logging.getLogger(__name__)


def check_price(product, session, history_rows, args):
    name = product["name"]
    target_price = product.get("target_price")
    logger.info("Checking %s...", name)
    source_names = list(SOURCES.keys())
    results = {}
    with ThreadPoolExecutor(max_workers=len(source_names)) as executor:
        future_to_source = {
            executor.submit(get_price, session, name, source_name,
                            DEFAULT_MAX_RETRIES, DEFAULT_REQUEST_TIMEOUT,
                            DEFAULT_RETRY_BACKOFF): source_name
            for source_name in source_names
        }
        for future in as_completed(future_to_source):
            source_name = future_to_source[future]
            try:
                price, url = future.result()
                results[source_name] = (price, url)
            except Exception as e:
                logger.warning("%s error: %s", source_name, e)
                results[source_name] = (None, "")
    for source_name, (price, url) in results.items():
        if price is not None:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info("%s on %s: €%.2f", name, source_name, price)
            last_price = get_last_price(history_rows, name, source_name)
            if prices_differ(price, last_price):
                if not args.dry_run:
                    append_price_history(args.history, current_time, name, price, source_name)
                    logger.info("Saved data from %s", source_name)
                else:
                    logger.info("DRY-RUN: would save €%.2f from %s", price, source_name)
            else:
                logger.info("Price unchanged (€%.2f). Skipping.", price)
            if target_price is not None and price <= target_price:
                logger.info("TARGET MET! %s at €%.2f (target: €%.2f)", name, price, target_price)
            else:
                logger.debug("Price still high or no target set.")
        else:
            logger.warning("Could not find price on %s", source_name)


def process_products(products, session, history_rows, args):
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = [executor.submit(check_price, item, session, history_rows, args) for item in products]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error("Product check error: %s", e)


def main():
    args = parse_args()
    setup_logging(args.log_level)
    logger.info("Starting Price Bot")
    if args.dry_run:
        logger.info("DRY-RUN mode: no data will be saved")
    products = load_products(args.products)
    if not products:
        logger.warning("No products to track. Exiting.")
        return
    history_rows = load_history(args.history)
    session = create_session()
    process_products(products, session, history_rows, args)
    session.close()
    print("-" * 30)
    if not args.dry_run:
        trim_csv(args.history, args.max_history)
        generate_readme(args.history, args.report)
    else:
        logger.info("DRY-RUN: skipping trim and report generation")


if __name__ == "__main__":
    main()
