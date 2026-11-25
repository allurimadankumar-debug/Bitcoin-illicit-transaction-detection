#!/usr/bin/env python3
"""Generate the deterministic synthetic demo dataset used when Elliptic CSVs are absent.

The output files are explicitly labelled synthetic. They are not real Bitcoin
transactions and must never be presented as such.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.config import get_settings  # noqa: E402
from ml.dataset import generate_demo_dataset  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: DATA_DIR/processed/demo, usually data/processed/demo)",
    )
    parser.add_argument("--transactions", type=int, default=None)
    parser.add_argument("--time-steps", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--force", action="store_true", help="Regenerate existing files")
    args = parser.parse_args()

    settings = get_settings()
    output = Path(args.output) if args.output else settings.demo_data_path
    if not output.is_absolute():
        output = PROJECT_ROOT / output

    dataset = generate_demo_dataset(
        output.resolve(),
        n_transactions=args.transactions or settings.demo_transactions,
        n_time_steps=args.time_steps or settings.demo_time_steps,
        seed=settings.random_state if args.seed is None else args.seed,
        force=args.force,
    )

    print(f"Generated synthetic dataset in: {output.resolve()}")
    print(f"Transactions: {dataset.size} | source: {dataset.source}")
    print("WARNING: DEMO identifiers are simulated; these are not real blockchain records.")


if __name__ == "__main__":
    main()
