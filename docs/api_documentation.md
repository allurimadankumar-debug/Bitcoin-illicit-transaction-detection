# API Documentation

Base URL in development: `http://127.0.0.1:8000`

Interactive Swagger UI: `http://127.0.0.1:8000/docs`
OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

All application routes are prefixed with `/api`. JSON is the default format. Errors use a consistent shape:

```json
{
  "error": "HTTPException",
  "detail": "Transaction not found in the loaded dataset",
  "status_code": 404
}
```

Validation failures return status `422` with `error: "ValidationError"` and a list of `{ location, message }` items. Unexpected failures return `500` with a generic detail; stack traces are never sent to clients.

## Conventions

### Transaction identifiers

`transaction_id` accepts either:

- a real Bitcoin txid: exactly 64 hexadecimal characters, or
- an opaque dataset identifier such as `DEMO00000001` or a numeric Elliptic ID.

IDs are normalized before lookup. Long identifiers are redacted in server logs. When `MASK_IDS_BY_DEFAULT=true`, list/detail responses can return masked forms; full IDs remain available to the prediction pipeline.

### Labels and predictions

| Field | Meaning |
| --- | --- |
| `ground_truth_label` | Dataset label: `illicit` (class 1), `licit` (class 2), or `unknown` |
| `predicted_class` | Model output: `illicit`, `licit`, or `unknown` (no model) |
| `risk_score` | Probability of the illicit class, or `null` when unavailable |
| `confidence` | `max(p, 1-p)` when a model exists, otherwise `0.0` |
| `is_synthetic_data` | The loaded dataset is the generated demo |
| `is_synthetic_model_data` | The saved model was trained on synthetic data |

Every prediction response includes:

```text
Model prediction is not proof of criminal activity
```

---

## 1. Health and status

### `GET /api/health`

Returns service health, version, configured source, dataset realism, and model availability.

```bash
curl http://127.0.0.1:8000/api/health
```

```json
{
  "status": "ok",
  "version": "1.0.0",
  "dataset_source": "demo",
  "is_synthetic": true,
  "model_trained": true,
  "timestamp": "2026-01-01T00:00:00Z"
}
```

`dataset_source` reflects the configured mode (`auto`, `elliptic`, `demo`); `is_synthetic` reports what was actually loaded.

---

## 2. Dashboard

### `GET /api/dashboard/summary`

Aggregate KPIs for the Overview page.

```bash
curl http://127.0.0.1:8000/api/dashboard/summary
```

```json
{
  "total_transactions": 360,
  "labeled_transactions": 250,
  "illicit_transactions": 40,
  "licit_transactions": 210,
  "unknown_transactions": 110,
  "high_risk_transactions": 38,
  "dataset_source": "demo_synthetic",
  "is_synthetic": true,
  "model_trained": true,
  "model_name": "random_forest",
  "best_pr_auc": 0.82,
  "best_recall": 0.79,
  "best_f1": 0.77,
  "test_metrics": { "pr_auc": 0.81, "recall": 0.78 },
  "prediction_history_count": 5,
  "last_trained_at": "2026-01-01T00:00:00Z",
  "note": "DEMO MODE: synthetic data. Not real blockchain records."
}
```

Fields may be `null` when no model is trained. `note` states synthetic-data warnings where applicable.

---

## 3. Transactions

### `GET /api/transactions`

Paginated, filterable list.

| Query | Default | Allowed values / meaning |
| --- | --- | --- |
| `search` | none | Matches ID, time step, or status text |
| `label` | `all` | `all`, `licit`, `illicit`, `unknown`, `predicted_licit`, `predicted_illicit` |
| `risk` | `all` | `all`, `high-risk`, `elevated`, `low-risk`, `unrated` |
| `sort_by` | `time_step` | `transaction_id`, `risk_score`, `time_step`, `illicit_count` |
| `order` | `desc` | `asc`, `desc` |
| `page` | `1` | ≥ 1 |
| `page_size` | `12` | 1–200 |
| `mask` | server default | `true`/`false` override ID masking |

```bash
curl "http://127.0.0.1:8000/api/transactions?label=illicit&page=1&page_size=5"
```

```json
{
  "items": [
    {
      "transaction_id": "DEMO00000001",
      "masked_transaction_id": "DEMO00…0001",
      "time_step": 7,
      "ground_truth_label": "illicit",
      "predicted_class": "illicit",
      "risk_score": 0.91,
      "status": "high-risk",
      "is_synthetic": true,
      "in_degree": 2,
      "out_degree": 3
    }
  ],
  "total": 40,
  "page": 1,
  "page_size": 5,
  "total_pages": 8
}
```

### `GET /api/transactions/{tx_id}`

Full detail: dataset source, truth/prediction separation, finite feature values, graph features, relationships, heuristic indicators, and warning.

```bash
curl http://127.0.0.1:8000/api/transactions/DEMO00000001
```

Returns `404` when the ID is absent from the loaded dataset.

### `GET /api/transactions/{tx_id}/graph`

Bounded neighborhood subgraph.

| Query | Default | Range |
| --- | --- | --- |
| `depth` | `1` | 1–3 |
| `limit` | `30` | 5–80 |

```bash
curl "http://127.0.0.1:8000/api/transactions/DEMO00000001/graph?depth=2&limit=30"
```

```json
{
  "center": "DEMO00000001",
  "nodes": [
    {
      "id": "DEMO00000001",
      "label": "illicit",
      "color": "#f43f5e",
      "risk_score": 0.91,
      "time_step": 7,
      "size": 12
    }
  ],
  "edges": [{ "source": "DEMO00000001", "target": "DEMO00000002" }],
  "depth": 2,
  "truncated": false,
  "total_neighbors": 5,
  "is_synthetic": true,
  "note": null
}
```

Node labels include `illicit`, `licit`, `unknown`, and `high-risk-prediction`. The response is bounded so the full graph is never rendered at once.

### `GET /api/transactions/{tx_id}/explanation`

Feature attribution for a stored or freshly generated prediction.

```bash
curl http://127.0.0.1:8000/api/transactions/DEMO00000001/explanation
```

```json
{
  "transaction_id": "DEMO00000001",
  "items": [
    {
      "feature": "feature_005",
      "value": 2.1,
      "impact": 0.31,
      "direction": "increases_risk"
    }
  ],
  "method": "shap_tree",
  "note": "SHAP values describe model behaviour.",
  "warning": "Explanations describe model behaviour, not proof of criminal intent.",
  "is_synthetic": true
}
```

When no model is trained, `items` is empty and `method`/`note` explain that no explanation is available.

---

## 4. Predictions

### `POST /api/predict`

Single transaction.

```bash
curl -X POST http://127.0.0.1:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"transaction_id":"DEMO00000001","threshold":0.5}'
```

```json
{
  "transaction_id": "DEMO00000001",
  "predicted_class": "illicit",
  "risk_score": 0.9123,
  "confidence": 0.9123,
  "model_name": "random_forest",
  "explanation": [
    { "feature": "feature_005", "value": 2.1, "impact": 0.31, "direction": "increases_risk" }
  ],
  "warning": "Model prediction is not proof of criminal activity",
  "ground_truth_label": "illicit",
  "explanation_method": "shap_tree",
  "explanation_note": null,
  "model_source": "demo_synthetic",
  "calibration": "sigmoid (3-fold, fitted on train+validation)",
  "note": null,
  "is_synthetic_data": true,
  "is_synthetic_model_data": true,
  "related_count": 5
}
```

Without a trained model:

```json
{
  "transaction_id": "DEMO00000001",
  "predicted_class": "unknown",
  "risk_score": null,
  "confidence": 0.0,
  "model_name": "untrained",
  "warning": "Model prediction is not proof of criminal activity",
  "ground_truth_label": "unknown",
  "note": "No trained model found. Run backend/ml/train.py --source demo or elliptic."
}
```

Returns `404` for a valid ID not present in the dataset, `422` for malformed IDs/thresholds.

### `POST /api/predict/batch`

Up to 5,000 IDs, optionally with inline CSV content.

```bash
curl -X POST http://127.0.0.1:8000/api/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"transaction_ids":["DEMO00000001","DEMO00000002"],"threshold":0.5}'
```

```json
{
  "results": [],
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "errors": [],
  "warning": "Model prediction is not proof of criminal activity"
}
```

CSV mode uses `csv_content`; the first column is parsed, an optional header such as `tx_id` is detected, and per-row invalid IDs are reported in `errors` instead of failing the whole batch.

### `POST /api/predict/batch/upload`

Multipart CSV file upload.

```bash
curl -X POST http://127.0.0.1:8000/api/predict/batch/upload \
  -F "file=@ids.csv" \
  -F "threshold=0.5"
```

Only `.csv` files are accepted (otherwise `400`).

---

## 5. Models and analytics

### `GET /api/models/metrics`

```bash
curl http://127.0.0.1:8000/api/models/metrics
```

```json
{
  "available": true,
  "best_model": "random_forest",
  "models": {
    "logistic_regression": {
      "precision": 0.61,
      "recall": 0.63,
      "f1": 0.62,
      "roc_auc": 0.74,
      "pr_auc": 0.57,
      "balanced_accuracy": 0.69
    }
  },
  "test_metrics": {
    "precision": 0.8,
    "recall": 0.79,
    "f1": 0.77,
    "pr_auc": 0.82,
    "roc_auc": 0.9,
    "confusion_matrix": [[100, 12], [8, 30]]
  },
  "split": {
    "method": "chronological (train < validation < test)",
    "train_rows": 150,
    "validation_rows": 40,
    "test_rows": 60,
    "calibration": "sigmoid (3-fold, fitted on train+validation)"
  },
  "dataset": { "source": "demo_synthetic", "is_synthetic": true },
  "message": null
}
```

When no report exists, `available: false` and `message` instructs how to train.

### `POST /api/models/train?source=demo&model=random_forest`

Retrains the final model and refreshes cached scores.

| Query | Default | Behavior |
| --- | --- | --- |
| `source` | `demo` | `demo` uses synthetic data, `elliptic` requires real Kaggle CSVs, `auto` prefers real CSVs and falls back to demo |
| `model` | `auto` | `auto` selects by validation PR-AUC/recall/F1; `random_forest`, `logistic_regression`, `hist_gradient_boosting`, or `xgboost` explicitly deploys that trained candidate |

```bash
curl -X POST "http://127.0.0.1:8000/api/models/train?source=demo&model=random_forest"
```

The response includes `selection_rule`, so an explicit Random Forest deployment is distinguishable from automatic selection. Dataset and training errors return `400` with a readable `detail`.

This is a research utility, not a job queue. Training may take several seconds on large datasets.

### `GET /api/analytics/temporal`

| Query | Default | Allowed |
| --- | --- | --- |
| `metric` | `illicit_count` | `illicit_count`, `illicit_rate`, `volume` |

```json
{
  "points": [
    {
      "time_step": 1,
      "total": 12,
      "illicit": 2,
      "licit": 7,
      "unknown": 3,
      "illicit_rate": 0.25
    }
  ],
  "metric": "illicit_count",
  "is_synthetic": true
}
```

### `GET /api/analytics/risk-distribution?bins=10`

Bins must be 2–50.

```json
{
  "bins": 10,
  "buckets": [{ "bucket": "0.0-0.1", "count": 120 }],
  "unrated": 110,
  "is_synthetic": true
}
```

---

## 6. Settings

### `GET /api/settings`

```json
{
  "explorer_base_url": "https://blockstream.info/tx",
  "enable_live_lookup": false,
  "mask_ids_by_default": false,
  "dataset_source": "auto",
  "version": "1.0.0",
  "keys_required": [],
  "overrides": {
    "mask_ids_by_default": false,
    "explorer_base_url": "https://blockstream.info/tx",
    "enable_live_lookup": false,
    "table_page_size": 12,
    "high_risk_threshold": 0.65
  },
  "note": "Preferences only. Private keys, seed phrases and API secrets are never requested, stored or returned by this application."
}
```

### `POST /api/settings`

Only whitelisted keys are persisted: `mask_ids_by_default`, `explorer_base_url`, `enable_live_lookup`, `table_page_size`, `high_risk_threshold`. Unknown keys are silently ignored; secrets are never accepted. Non-local explorer base URLs must use HTTPS (otherwise `422`).

```bash
curl -X POST http://127.0.0.1:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"mask_ids_by_default":true,"table_page_size":20}'
```

Returns the updated settings object.

---

## 7. Privacy and Web3

### `GET /api/blockchain/explorer-url?tx_id=...`

Builds a public explorer link after validating a Bitcoin txid or dataset ID.

```json
{
  "transaction_id": "DEMO00000001",
  "url": "https://blockstream.info/tx/DEMO00000001"
}
```

This is a URL builder only; it does not make an external request.

### `GET /api/blockchain/lookup/{tx_id}`

Opt-in live explorer lookup. With the default `ENABLE_LIVE_LOOKUP=false`:

```json
{
  "transaction_id": "DEMO00000001",
  "enabled": false,
  "is_live_blockchain_data": false,
  "found": false,
  "data": null,
  "message": "Live lookup is disabled. Set ENABLE_LIVE_LOOKUP=true to query a public explorer.",
  "explorer_url": "https://blockstream.info/tx/DEMO00000001"
}
```

When enabled, only real 64-hex Bitcoin txids are queried. Elliptic/demo identifiers are never treated as live blockchain data. Timeouts and network errors are returned as structured responses rather than crashes.

---

## 8. Root and documentation routes

| Route | Purpose |
| --- | --- |
| `GET /` | Service name, docs link, health link, academic warning |
| `GET /docs` | Swagger UI |
| `GET /redoc` | ReDoc |
| `GET /openapi.json` | Machine-readable schema |

When `frontend/dist/` exists, `/` serves the compiled dashboard and API/docs routes remain under `/api`, `/docs`, and `/openapi.json`.
