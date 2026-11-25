#!/usr/bin/env python3
"""Download the public Elliptic data set from Kaggle into data/raw/.

Credentials are read by Kaggle from ``~/.kaggle/kaggle.json`` (recommended on a
local machine) or from ``KAGGLE_USERNAME`` / ``KAGGLE_KEY`` environment
variables. This script never copies credentials into the project and never
writes them to the database or API responses.

Usage:
    python scripts/download_kaggle.py
    python scripts/download_kaggle.py --dataset ellipticdataset/elliptic-data-set --force
"""
from __future__ import annotations

import argparse
import shutil
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FILES = (
    "elliptic_txs_features.csv",
    "elliptic_txs_classes.csv",
    "elliptic_txs_edgelist.csv",
)


def extract_archives(root: Path) -> None:
    """Extract downloaded zips in place, guarding against path traversal."""
    for archive in list(root.rglob("*.zip")):
        destination = archive.parent / archive.stem
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as zip_file:
            for member in zip_file.namelist():
                target = (destination / member).resolve()
                if not str(target).startswith(str(destination.resolve())):
                    raise RuntimeError(f"Unsafe path in archive: {member}")
                zip_file.extract(member, destination)
        archive.unlink()


def promote_files(root: Path, force: bool) -> None:
    """Ensure the three expected CSVs exist at the top level of data/raw/."""
    for expected in EXPECTED_FILES:
        target = root / expected
        if target.exists() and not force:
            print(f"Kept existing {target.relative_to(PROJECT_ROOT)}")
            continue
        matches = [path for path in root.rglob(expected) if path != target]
        if not matches:
            raise RuntimeError(
                f"Could not find {expected} after extraction. "
                "Check the Kaggle dataset contents or download it manually."
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(matches[0], target)
        print(f"Copied {matches[0].relative_to(PROJECT_ROOT)} -> {target.relative_to(PROJECT_ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        default="ellipticdataset/elliptic-data-set",
        help="Kaggle dataset slug (default: ellipticdataset/elliptic-data-set)",
    )
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / "data" / "raw"),
        help="Destination directory (default: data/raw)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing raw CSVs with the downloaded copies",
    )
    args = parser.parse_args()

    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.mkdir(parents=True, exist_ok=True)

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:  # pragma: no cover - depends on local setup
        raise SystemExit(
            "The 'kaggle' package is required. Install it with:\n"
            "    python -m pip install kaggle\n"
            "Then configure ~/.kaggle/kaggle.json or KAGGLE_USERNAME/KAGGLE_KEY.\n"
            "See docs/KAGGLE_SETUP.md for details."
        ) from exc

    print(f"Downloading Kaggle dataset '{args.dataset}' into {output}")
    api = KaggleApi()
    api.authenticate()
    api.dataset_download_files(args.dataset, path=str(output), unzip=False, force=args.force, quiet=False)

    extract_archives(output)
    promote_files(output, args.force)

    print("\nDownload complete. Next steps:")
    print("  python backend/ml/train.py --source elliptic")
    print("  uvicorn app.main:app --app-dir backend --reload")
    print("\nAcademic use only. This dataset is historical and anonymized; it is not live blockchain data.")


if __name__ == "__main__":
    main()
