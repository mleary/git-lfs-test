#!/usr/bin/env python3
"""Generate a large synthetic e-commerce transactions dataset for Git LFS testing.

Produces a CSV with ~1.5 million rows and multiple column types (numeric,
categorical, datetime, text).  The resulting file is typically 200-350 MB.

Usage:
    python generate_dataset.py [--rows N] [--output PATH]
"""

import argparse
import os
import pathlib
import time

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORIES = [
    "Electronics",
    "Clothing",
    "Home & Garden",
    "Sports & Outdoors",
    "Books",
    "Toys & Games",
    "Health & Beauty",
    "Automotive",
    "Grocery",
    "Pet Supplies",
    "Office Supplies",
    "Music & Movies",
    "Jewelry",
    "Baby Products",
    "Tools & Hardware",
]

PAYMENT_METHODS = ["Credit Card", "Debit Card", "PayPal", "Apple Pay", "Google Pay", "Gift Card", "Wire Transfer"]

REGIONS = [
    "Northeast",
    "Southeast",
    "Midwest",
    "Southwest",
    "West Coast",
    "Northwest",
    "Mid-Atlantic",
    "Great Plains",
]

STATUSES = ["Completed", "Pending", "Shipped", "Cancelled", "Returned", "Refunded"]

CITIES = [
    "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
    "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
    "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
    "Indianapolis", "San Francisco", "Seattle", "Denver", "Nashville",
    "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore",
    "Milwaukee", "Albuquerque", "Tucson", "Fresno", "Sacramento",
]


def generate_dataset(num_rows: int, seed: int = 42) -> pd.DataFrame:
    """Return a DataFrame with *num_rows* synthetic transaction records."""

    rng = np.random.default_rng(seed)

    # Dates spanning two years
    start_ts = pd.Timestamp("2024-01-01")
    end_ts = pd.Timestamp("2025-12-31")
    total_seconds = int((end_ts - start_ts).total_seconds())
    random_seconds = rng.integers(0, total_seconds, size=num_rows)
    dates = start_ts + pd.to_timedelta(random_seconds, unit="s")

    # Financial columns
    unit_prices = np.round(rng.exponential(scale=50, size=num_rows) + 0.99, 2)
    quantities = rng.integers(1, 21, size=num_rows)
    discounts = np.round(rng.choice([0, 0, 0, 0.05, 0.1, 0.15, 0.2, 0.25], size=num_rows), 2)
    subtotals = np.round(unit_prices * quantities * (1 - discounts), 2)
    tax_rates = rng.choice([0.0, 0.05, 0.06, 0.07, 0.075, 0.08, 0.0825, 0.1], size=num_rows)
    taxes = np.round(subtotals * tax_rates, 2)
    totals = np.round(subtotals + taxes, 2)

    # Build DataFrame
    df = pd.DataFrame(
        {
            "transaction_id": np.arange(1, num_rows + 1),
            "timestamp": dates,
            "customer_id": rng.integers(10000, 99999, size=num_rows),
            "category": rng.choice(CATEGORIES, size=num_rows),
            "product_id": rng.integers(100000, 999999, size=num_rows),
            "unit_price": unit_prices,
            "quantity": quantities,
            "discount": discounts,
            "subtotal": subtotals,
            "tax_rate": tax_rates,
            "tax": taxes,
            "total": totals,
            "payment_method": rng.choice(PAYMENT_METHODS, size=num_rows),
            "region": rng.choice(REGIONS, size=num_rows),
            "city": rng.choice(CITIES, size=num_rows),
            "status": rng.choice(STATUSES, size=num_rows, p=[0.60, 0.10, 0.12, 0.08, 0.06, 0.04]),
            "is_member": rng.choice([True, False], size=num_rows, p=[0.35, 0.65]),
            "rating": rng.choice([np.nan, 1, 2, 3, 4, 5], size=num_rows, p=[0.3, 0.03, 0.07, 0.15, 0.25, 0.20]),
        }
    )

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a large test dataset.")
    parser.add_argument("--rows", type=int, default=1_500_000, help="Number of rows (default: 1,500,000)")
    parser.add_argument("--output", type=str, default="data/transactions.csv", help="Output CSV path")
    args = parser.parse_args()

    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.rows:,} rows …")
    t0 = time.perf_counter()
    df = generate_dataset(args.rows)
    elapsed_gen = time.perf_counter() - t0
    print(f"  Generated in {elapsed_gen:.1f}s")

    print(f"Writing to {out_path} …")
    t1 = time.perf_counter()
    df.to_csv(out_path, index=False)
    elapsed_write = time.perf_counter() - t1
    print(f"  Written in {elapsed_write:.1f}s")

    size_mb = os.path.getsize(out_path) / (1024 * 1024)
    print(f"Done — {args.rows:,} rows, {len(df.columns)} columns, {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
