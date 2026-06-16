import datetime
import logging
import urllib.parse

from storage import load_history

logger = logging.getLogger(__name__)


def generate_readme(history_file: str, report_file: str, max_entries: int = 20):
    rows = load_history(history_file)
    if not rows:
        logger.info("No history data to generate report.")
        return
    products_data = {}
    for row in rows:
        product = row[1]
        products_data.setdefault(product, []).append(row)
    content_parts = ["# Price Tracker\n",
                     "Automated price tracking for products on idealo.de and billiger.de.\n",
                     "## Latest Prices\n"]
    for product, entries in products_data.items():
        content_parts.append(f"### {product}\n")
        content_parts.append("| Timestamp | Price (€) | Source |")
        content_parts.append("|-----------|-----------|--------|")
        latest = entries[-max_entries:]
        for entry in reversed(latest):
            timestamp, _, price, website = entry
            price_display = f"{float(price) / 100:.2f}" if isinstance(price, str) and price.isdigit() else price
            search_name = urllib.parse.quote_plus(product)
            idealo_url = f"https://www.idealo.de/preisvergleich/MainSearchProductCategory.html?q={search_name}"
            billiger_url = f"https://www.billiger.de/suche/{search_name}"
            source_link = idealo_url if website == "Idealo" else billiger_url
            content_parts.append(f"| {timestamp} | {price_display} | [{website}]({source_link}) |")
        content_parts.append("")
    content_parts.append(f"*Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(content_parts))
    logger.info("Report generated: %s", report_file)
