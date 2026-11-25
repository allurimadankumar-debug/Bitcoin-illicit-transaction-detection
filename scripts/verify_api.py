#!/usr/bin/env python3
"""Smoke-check the required API endpoints against a running backend."""
from __future__ import annotations

import argparse
import sys

import httpx

CHECKS: list[tuple[str, str, str]] = [
    ("health", "GET", "/api/health"),
    ("dashboard summary", "GET", "/api/dashboard/summary"),
    ("transactions", "GET", "/api/transactions?page=1&page_size=5"),
    ("model metrics", "GET", "/api/models/metrics"),
    ("temporal analytics", "GET", "/api/analytics/temporal"),
    ("risk distribution", "GET", "/api/analytics/risk-distribution"),
    ("settings", "GET", "/api/settings"),
    ("openapi", "GET", "/openapi.json"),
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=60.0) as client:
            payloads: dict[str, dict] = {}
            for name, method, path in CHECKS:
                response = client.request(method, path)
                response.raise_for_status()
                payloads[name] = response.json()
                print(f"PASS {name:22} {method} {path} -> {response.status_code}")

            txs = payloads["transactions"]
            if not txs.get("items"):
                raise RuntimeError("No transactions loaded; cannot test detail endpoints")
            tx_id = txs["items"][0]["transaction_id"]

            detail_paths = [
                ("transaction detail", f"/api/transactions/{tx_id}"),
                ("transaction graph", f"/api/transactions/{tx_id}/graph?depth=1&limit=10"),
                ("transaction explanation", f"/api/transactions/{tx_id}/explanation"),
            ]
            for name, path in detail_paths:
                response = client.get(path)
                response.raise_for_status()
                print(f"PASS {name:22} GET {path} -> {response.status_code}")

            prediction = client.post("/api/predict", json={"transaction_id": tx_id})
            prediction.raise_for_status()
            result = prediction.json()
            warning = "Model prediction is not proof of criminal activity"
            if result.get("warning") != warning:
                raise RuntimeError(f"Prediction warning missing or changed: {result.get('warning')!r}")
            print(f"PASS {'single prediction':22} POST /api/predict -> {prediction.status_code}")

            batch = client.post(
                "/api/predict/batch",
                json={"transaction_ids": [tx_id], "threshold": 0.5},
            )
            batch.raise_for_status()
            if batch.json().get("warning") != warning:
                raise RuntimeError("Batch prediction warning missing or changed")
            print(f"PASS {'batch prediction':22} POST /api/predict/batch -> {batch.status_code}")

            health = payloads["health"]
            print(f"\nDataset source: {health.get('dataset_source')} | synthetic: {health.get('is_synthetic')}")
            print(f"Model trained: {health.get('model_trained')}")
            if health.get("is_synthetic"):
                print("Demo mode confirmed: UI and API label all records as synthetic.")
    except (httpx.HTTPError, RuntimeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
