# Kaggle Elliptic Data Set Setup

The application runs immediately in **synthetic demo mode**. These steps are only needed to use the real, historical Elliptic data set.

> The Elliptic data set is anonymized research data. It is not live blockchain data and must not be used to accuse or identify individuals. Follow the Kaggle dataset terms and cite the original publication in any report.

## 1. Prerequisites

1. A Kaggle account.
2. Accept the dataset rules on the Kaggle page (search for **Elliptic Data Set**; the common API slug is `ellipticdataset/elliptic-data-set`). Verify the slug on Kaggle before downloading, because mirrors may differ.
3. Python 3.10+.

## 2. Kaggle credentials

### Option A — credentials file (recommended locally)

1. Open Kaggle → Account → **Create New API Token**. This downloads `kaggle.json`.
2. Place it at:

   | OS | Path |
   | --- | --- |
   | macOS/Linux | `~/.kaggle/kaggle.json` |
   | Windows | `C:\Users\<you>\.kaggle\kaggle.json` |

3. Restrict permissions on macOS/Linux:

   ```bash
   chmod 600 ~/.kaggle/kaggle.json
   ```

### Option B — environment variables

```bash
# PowerShell
$env:KAGGLE_USERNAME="your-username"
$env:KAGGLE_KEY="your-key"

# macOS/Linux
export KAGGLE_USERNAME="your-username"
export KAGGLE_KEY="your-key"
```

**Never** put Kaggle credentials in `.env`, `docker-compose.yml`, source code, Git, the SQLite database, or API responses. The `.gitignore` already blocks `kaggle.json`-style secrets and `.env`.

## 3. Install and run the downloader

```bash
python -m pip install kaggle
python scripts/download_kaggle.py
```

The script:

- downloads the dataset archive into `data/raw/`,
- safely extracts nested zip files,
- finds and promotes the expected CSVs to `data/raw/`,
- never overwrites existing files unless `--force` is passed.

To use a different mirror or force a refresh:

```bash
python scripts/download_kaggle.py \
  --dataset ellipticdataset/elliptic-data-set \
  --force
```

## 4. Manual download alternative

If the API is unavailable:

1. Download the files from the Kaggle dataset page.
2. Extract any `.zip` archives.
3. Copy these three files into `data/raw/`:

   ```text
   data/raw/elliptic_txs_features.csv
   data/raw/elliptic_txs_classes.csv
   data/raw/elliptic_txs_edgelist.csv
   ```

The loader tolerates headers such as `txId,txTime,feature_1,...`, `txId,class`, and `txId1,txId2`, but the official headerless files work as-is.

Expected shape:

| File | Content |
| --- | --- |
| `elliptic_txs_features.csv` | ID, time step, 164 numeric features (166 columns total) |
| `elliptic_txs_classes.csv` | ID, class (`1` illicit, `2` licit, `unknown`) |
| `elliptic_txs_edgelist.csv` | Source ID, destination ID |

Large raw CSVs are git-ignored. Do not commit them.

## 5. Configure and train

```bash
copy .env.example .env          # Windows
cp .env.example .env            # macOS/Linux
```

Set:

```env
DATASET_SOURCE=elliptic
AUTO_TRAIN_DEMO=false
```

Then train:

```bash
python backend/ml/train.py --source elliptic --model random_forest
```

`--model random_forest` deploys the Random Forest candidate explicitly. Omit it to select automatically by validation PR-AUC.

Successful training writes:

```text
models/model_bundle.joblib
models/model_metrics.json
models/feature_importance.json
reports/model_comparison.png
reports/confusion_matrix.png
reports/precision_recall.png
```

Start the app and confirm:

```bash
python -m uvicorn app.main:app --app-dir backend --reload
curl http://127.0.0.1:8000/api/health
```

`is_synthetic` must be `false` and the synthetic-data banner must disappear from the dashboard.

## 6. Troubleshooting

| Problem | Resolution |
| --- | --- |
| Kaggle `401 Unauthorized` | Confirm username/key or refresh `kaggle.json`; accept dataset rules. |
| Kaggle `403 Forbidden` | Dataset rules were not accepted, or the slug is wrong. Check the Kaggle page. |
| `Could not find the features CSV` | Confirm exact filenames in `data/raw/` or run the downloader with `--force`. |
| Feature-dimension error | You may have downloaded a different dataset; the expected feature file has 166 columns. |
| Header confusion | The loader auto-detects headers; do not edit the raw files unless necessary. |
| App still shows demo data | Set `DATASET_SOURCE=elliptic`, restart the backend, and check `/api/health`. |
| No model trained | Run `python backend/ml/train.py --source elliptic`; auto-training only applies to demo data. |
| Slow training | Use fewer candidate models or a larger machine; XGBoost is optional. |

## 7. Docker

Mounted volumes keep downloaded data available to containers:

```yaml
volumes:
  - ./data:/app/data
  - ./models:/app/models
  - ./reports:/app/reports
```

Download the data on the host first, set `DATASET_SOURCE=elliptic` in `.env` or Compose, then run `docker compose up --build`.
