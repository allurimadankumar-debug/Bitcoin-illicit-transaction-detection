# Model Methodology

## 1. Objective and scope

The model estimates the probability that a transaction exhibits patterns associated with the illicit class in the Elliptic data set. It is a research classifier, not a forensic determination. Output probabilities are **model scores**, not evidence of criminal conduct.

Two data regimes exist:

| Source | Value | Description |
| --- | --- | --- |
| Elliptic Kaggle CSVs | `elliptic_kaggle` | Historical, anonymized research data; class `1` illicit, class `2` licit, `unknown` unlabeled |
| Generated demo | `demo_synthetic` | Deterministic simulator with `DEMO########` IDs; explicitly labelled synthetic throughout the UI and API |

The same pipeline is used for both so the interface and tests exercise realistic behavior. Demo results must never be reported as real-world performance.

## 2. Dataset handling

`backend/ml/dataset.py` performs:

- **Header detection** for headerless official files and common headered variants (`txId1,txId2`, `tx_id,class`, etc.).
- **Feature-matrix validation**: converts values to float, replaces infinities with NaN, checks a 166-column Elliptic-like layout, and raises a descriptive `DatasetFormatError` otherwise.
- **ID alignment** across features/classes/edges by string ID rather than row position when IDs are present.
- **Label mapping**: `1 → 1.0` illicit, `2 → 0.0` licit, anything unknown/missing → NaN.
- **Unknown handling**: unlabeled rows remain in the dataset for browsing and graph features but are excluded from supervised loss and evaluation.
- **Missing values**: left as NaN for the sklearn imputer; no silent zero-filling.
- **Clear errors**: missing raw CSVs point to `docs/KAGGLE_SETUP.md` or demo mode.

The official Elliptic feature file contains an ID column, a time-step column, and 164 anonymized numeric features. No raw CSVs are committed to the repository.

## 3. Features

### Base features

The 164 anonymized Elliptic-style numeric features are used as-is after imputation. They represent aggregated transaction/neighborhood behavior supplied by the dataset; their original semantics are not publicly interpretable.

### Graph-derived features

`backend/ml/graph_features.py` builds a directed `networkx.DiGraph` from the edge list. To avoid future-topology leakage, an edge is kept only when:

```text
source.time_step <= target.time_step
```

Derived features include in/out degree, unique neighbor counts, neighbor illicit/licit/unknown ratios computed from labels available in the graph, and local connectivity summaries. These are appended to the base matrix with explicit names such as `graph_out_count`.

Graph features are recomputed deterministically from the complete dataset before splitting. Label-based graph statistics are a known limitation: in a production deployment they would need to be computed from labels available at prediction time only. They are acceptable for this historical research setup and are disclosed here.

## 4. Temporal split

Rows are ordered by `time_step` and partitioned into contiguous periods:

```text
train:      earliest 70% of labelled rows
validation: next 15%
test:       latest 15%
```

Defaults are `TRAIN_FRACTION=0.70` and `VALIDATION_FRACTION=0.15`; the remainder is test. This simulates forward-in-time detection and prevents random-split leakage across correlated graph neighborhoods.

Important rules:

- Unknown-label rows are excluded from all three supervised splits.
- Model selection uses **validation only**.
- The test split is evaluated once, after the final model is fitted.
- Oversampling, when enabled, is applied to training folds only — never before the split and never to validation/test.

## 5. Class imbalance

Illicit transactions are a small minority. The primary strategy is cost-sensitive learning:

- Logistic Regression: `class_weight="balanced"`.
- Random Forest: `class_weight="balanced_subsample"`.
- HistGradientBoosting/XGBoost: positive-class sample weights passed through pipeline parameters when supported.

`USE_OVERSAMPLING=true` optionally applies `RandomOverSampler` from imbalanced-learn to training data only. It is disabled by default because synthetic duplicates can distort probability estimates.

## 6. Candidate models

Built by `backend/ml/train.py::build_model()`:

1. **Logistic Regression** — standardized, L2, 2,500 iterations; strong interpretable baseline.
2. **Random Forest** — 140 trees, max depth 12, min leaf 2, balanced subsample weights.
3. **HistGradientBoostingClassifier** — histogram-based nonlinear baseline with sample weights when supported.
4. **XGBoost** — added only when `xgboost` is importable; graceful fallback otherwise.

Every candidate is wrapped in a sklearn `Pipeline` with a median imputer, optional scaler, and classifier, ensuring preprocessing is fitted inside each training fold.

## 7. Model selection and calibration

Selection score:

```text
validation PR-AUC (primary)
→ validation illicit recall (tie-break)
→ validation illicit F1 (tie-break)
```

PR-AUC is prioritized because the positive class is rare and precision/recall trade-offs matter more than overall accuracy.

The selected architecture is then refit on **train + validation** to use all pre-test labelled data. If `CALIBRATE_MODEL=true` and enough labelled rows exist, a `CalibratedClassifierCV` sigmoid calibrator is fitted with 3 internal folds on train+validation. The calibrated model is evaluated on the untouched test set. `calibration` metadata in the report states whether sigmoid calibration was applied.

For a reproducible submitted demo, `python backend/ml/train.py --source demo --model random_forest` (or `POST /api/models/train?source=demo&model=random_forest`) deploys Random Forest explicitly. This is recorded in `selection_rule` as an explicit model choice; all candidates are still trained and their validation metrics remain in the report. It is a deployment choice, not a claim that Random Forest won automatic selection.

## 8. Evaluation metrics

`backend/ml/evaluate.py` computes, for the illicit class:

- Precision, recall, F1
- ROC-AUC and PR-AUC (average precision)
- Confusion matrix with labels `[licit, illicit]`
- Accuracy and balanced accuracy (reported, not used for selection)
- Support counts per class
- Full classification report

Generated reports:

```text
models/model_metrics.json
reports/model_comparison.json
reports/model_comparison.png
reports/confusion_matrix.png
reports/precision_recall.png
```

The dashboard's Model Performance page displays validation comparison plus held-out test metrics, and labels which model was selected.

## 9. Prediction and thresholding

`backend/ml/predict.py` loads `models/model_bundle.joblib` and returns the probability of class `1`. `POST /api/predict` uses a configurable threshold (default `0.5`) to classify:

```text
probability >= threshold → illicit
probability <  threshold → licit
```

If no artifact exists, the response is explicitly unknown:

```json
{
  "predicted_class": "unknown",
  "risk_score": null,
  "confidence": 0.0,
  "note": "No trained model found. Run backend/ml/train.py ..."
}
```

No placeholder probability is ever invented. This behavior is covered by backend tests.

## 10. Explainability

`backend/ml/explain.py` uses SHAP when the installed SHAP version is compatible with the fitted estimator. It reports signed per-feature impacts and names the method (`shap_tree`, `shap_linear`, or global-importance fallback).

If SHAP cannot explain the model, `models/feature_importance.json` is used:

- native `feature_importances_` or `coef_`, or
- `permutation_importance` scored with average precision.

Explanations are **descriptive of model behavior**. They do not establish why a real transaction occurred or imply criminal intent. Every UI explanation panel and prediction response carries that caveat.

## 11. Reproducibility

- `RANDOM_STATE` (default 42) seeds demo generation and model estimators.
- Demo generation is deterministic and writes a `README_SYNTHETIC_DATA.txt` notice.
- Split boundaries, row counts, time boundaries, source, calibration method, oversampling flag, and sklearn version are saved in the report and model bundle.
- Requirements pin compatible major versions; XGBoost and SHAP are optional and degrade gracefully.

## 12. Known limitations

1. Anonymized Elliptic features are not human-interpretable; feature importance shows statistical influence, not real-world cause.
2. Elliptic labels reflect a historical snapshot and may contain noise or selection bias.
3. Graph label ratios can leak label information within the historical dataset; they are not available in a live unlabeled setting.
4. A temporal split reduces leakage but does not remove distribution shift.
5. The demo simulator is intentionally learnable and small; its metrics demonstrate plumbing only.
6. Bitcoin analysis is pseudonymous. Linking a transaction to a person requires lawful external evidence outside this application.
7. Model scores must be reviewed by a human and must not be used as automated accusations.
