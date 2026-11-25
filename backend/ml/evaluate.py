"""Evaluation metrics, comparison charts and reproducible reports."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_probability: np.ndarray | None = None,
) -> dict[str, Any]:
    """Compute illicit-focused metrics with graceful handling of edge cases."""
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    metrics: dict[str, Any] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist(),
        "support": int(len(y_true)),
        "illicit_support": int((y_true == 1).sum()),
        "licit_support": int((y_true == 0).sum()),
        "classification_report": classification_report(
            y_true,
            y_pred,
            labels=[0, 1],
            target_names=["licit", "illicit"],
            output_dict=True,
            zero_division=0,
        ),
    }
    if y_probability is not None and len(np.unique(y_true)) == 2:
        probability = np.asarray(y_probability, dtype=float)
        metrics["roc_auc"] = float(roc_auc_score(y_true, probability))
        metrics["pr_auc"] = float(average_precision_score(y_true, probability))
        metrics["precision_recall_curve"] = {
            "precision": precision_recall_curve(y_true, probability)[0].tolist(),
            "recall": precision_recall_curve(y_true, probability)[1].tolist(),
        }
    else:
        metrics["roc_auc"] = None
        metrics["pr_auc"] = None
    return metrics


def select_best_model(
    comparison: Mapping[str, Mapping[str, Any]],
    *,
    primary: str = "pr_auc",
    secondary: str = "recall",
) -> str:
    """Select a model using illicit PR-AUC, then recall, then F1."""
    def score(item: tuple[str, Mapping[str, Any]]) -> tuple[float, float, float]:
        _, metrics = item
        return (
            float(metrics.get(primary) or 0.0),
            float(metrics.get(secondary) or 0.0),
            float(metrics.get("f1") or 0.0),
        )

    return max(comparison.items(), key=score)[0]


def plot_model_comparison(comparison: Mapping[str, Mapping[str, Any]], out_dir: Path) -> Path:
    names = list(comparison.keys())
    metrics_to_plot = ["precision", "recall", "f1", "roc_auc", "pr_auc"]
    values = {
        metric: [float(comparison[name].get(metric) or 0.0) for name in names]
        for metric in metrics_to_plot
    }
    x = np.arange(len(names))
    width = 0.16
    fig, axis = plt.subplots(figsize=(10, 5.2))
    for offset, (metric, series) in enumerate(values.items()):
        axis.bar(x + (offset - 2) * width, series, width, label=metric.replace("_", "-").upper())
    axis.set_ylabel("Score")
    axis.set_title("Model comparison (temporal test split)")
    axis.set_xticks(x)
    axis.set_xticklabels([name.replace("_", " ") for name in names], rotation=15, ha="right")
    axis.set_ylim(0, 1.05)
    axis.legend(fontsize=8, ncol=3)
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "model_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_confusion_matrix(metrics: Mapping[str, Any], out_dir: Path) -> Path:
    matrix = np.array(metrics.get("confusion_matrix", [[0, 0], [0, 0]]))
    fig, axis = plt.subplots(figsize=(5.2, 4.4))
    image = axis.imshow(matrix, cmap="Blues")
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            axis.text(column, row, str(matrix[row, column]), ha="center", va="center", fontsize=14)
    axis.set_xticks([0, 1], ["Predicted licit", "Predicted illicit"])
    axis.set_yticks([0, 1], ["Actual licit", "Actual illicit"])
    axis.set_title("Confusion matrix")
    fig.colorbar(image, ax=axis, fraction=0.046)
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "confusion_matrix.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_pr_curves(
    curves: Mapping[str, Mapping[str, list[float]]], out_dir: Path
) -> Path | None:
    valid = {name: curve for name, curve in curves.items() if curve.get("recall")}
    if not valid:
        return None
    fig, axis = plt.subplots(figsize=(5.6, 4.4))
    for name, curve in valid.items():
        axis.plot(curve["recall"], curve["precision"], label=name.replace("_", " "))
    axis.set_xlabel("Recall")
    axis.set_ylabel("Precision")
    axis.set_title("Precision-Recall (illicit class)")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1.05)
    axis.legend(fontsize=8)
    axis.grid(alpha=0.25)
    fig.tight_layout()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "precision_recall_curves.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def save_evaluation_report(
    out_dir: Path,
    *,
    comparison: Mapping[str, Mapping[str, Any]],
    best_model: str,
    split_info: Mapping[str, Any],
    dataset_info: Mapping[str, Any],
    selection_rule: str | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "best_model": best_model,
        "selection_rule": selection_rule
        or "highest illicit PR-AUC, then recall, then F1",
        "models": dict(comparison),
        "split": dict(split_info),
        "dataset": dict(dataset_info),
        "note": "Metrics are computed on a chronologically held-out test set. Accuracy is informational only.",
    }
    (out_dir / "model_comparison.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )
    best_metrics = comparison[best_model]
    plot_model_comparison(comparison, out_dir)
    plot_confusion_matrix(best_metrics, out_dir)
    curves = {
        name: metrics.get("precision_recall_curve", {}) for name, metrics in comparison.items()
    }
    plot_pr_curves(curves, out_dir)
    return report
