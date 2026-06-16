# price-bot

A Python automation script that periodically scrapes prices for user-defined products from German price comparison websites (idealo.de and billiger.de), records them in a CSV file, and generates a markdown report.

## Features

- Track any product by name with a target price
- Scrapes prices from **idealo.de** and **billiger.de**
- Records price history in a CSV file with deduplication (only saves on price change)
- Generates a markdown report (`PRICES.md`) with the latest prices
- Runs on a cron schedule via GitHub Actions (every 8 hours)
- Dry-run mode for testing
- Configurable via CLI flags or environment variables

## Usage

```bash
# Install dependencies
pip install -r requirements.txt

# Run with defaults
python bot.py

# Dry run (no data saved)
python bot.py --dry-run

# Custom file paths
python bot.py --products my_products.txt --history my_history.csv --report PRICES.md

# Environment variables also work:
# PRODUCTS_FILE, PRICE_HISTORY_FILE, REPORT_FILE, MAX_HISTORY, etc.
```

## Configuration

Edit `products.txt` with one product per line:

```
Product Name|TargetPriceEUR
```

Lines starting with `#` are ignored. If no target price is set, the bot only records prices without alerting.

## CLI Options

| Flag | Env Var | Default | Description |
|------|---------|---------|-------------|
| `--products` | `PRODUCTS_FILE` | `products.txt` | Products input file |
| `--history` | `PRICE_HISTORY_FILE` | `price_history.csv` | Price history CSV file |
| `--report` | `REPORT_FILE` | `PRICES.md` | Generated report output |
| `--max-history` | `MAX_HISTORY` | `50` | Max entries per product in CSV |
| `--max-workers` | `MAX_WORKERS` | `4` | Parallel worker threads |
| `--request-delay` | `REQUEST_DELAY` | `1.5` | Delay between source requests (s) |
| `--dry-run` | - | `false` | Run without saving data |
| `--log-level` | `LOG_LEVEL` | `INFO` | Log level (DEBUG/INFO/WARNING/ERROR) |

## GitHub Actions

The bot runs automatically via the workflow in `.github/workflows/run_bot.yml`. It runs every 8 hours and can also be triggered manually from the Actions tab.
