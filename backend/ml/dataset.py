"""Robust dataset loading plus a clearly labelled synthetic demo dataset.

The real Elliptic CSVs are headerless in the public Kaggle release, but this
loader does not assume that: headers are detected heuristically and columns
are aligned by position/identifier rather than by fixed names.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from app.core.config import Settings, get_settings
from app.core.logging import logger

ID_LIKE_NAMES = {
    "txid",
    "tx_id",
    "txid1",
    "txid2",
    "tx_id1",
    "tx_id2",
    "id",
    "transactionid",
    "transaction_id",
    "tx",
    "from",
    "to",
    "source",
    "target",
}
LABEL_LIKE_NAMES = {"class", "label", "target", "category"}

LABEL_ILLICIT = 1
LABEL_LICIT = 0
LABEL_UNKNOWN = np.nan

ILLICIT_FEATURES = (5, 17, 42, 88, 131, 149)
LICIT_FEATURES = (9, 23, 61, 105, 140)


class DatasetNotFoundError(FileNotFoundError):
    """Raised when the requested dataset files cannot be located."""


class DatasetFormatError(ValueError):
    """Raised when dataset files are structurally invalid."""


@dataclass
class TransactionDataset:
    transactions: pd.DataFrame
    edges: pd.DataFrame
    feature_matrix: np.ndarray
    feature_names: list[str]
    source: str
    is_synthetic: bool
    metadata: dict = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.transactions)

    @property
    def labeled_mask(self) -> np.ndarray:
        return self.transactions["label"].notna().to_numpy()

    @property
    def illicit_count(self) -> int:
        return int((self.transactions["label"] == LABEL_ILLICIT).sum())

    @property
    def licit_count(self) -> int:
        return int((self.transactions["label"] == LABEL_LICIT).sum())

    @property
    def unknown_count(self) -> int:
        return int(self.transactions["label"].isna().sum())

    def row_for(self, tx_id: str) -> pd.Series | None:
        matches = self.transactions.loc[self.transactions["tx_id"] == tx_id]
        return None if matches.empty else matches.iloc[0]

    def feature_row(self, tx_id: str) -> np.ndarray | None:
        row = self.row_for(tx_id)
        if row is None:
            return None
        return self.feature_matrix[int(row["feature_index"])].copy()

    def time_step_for(self, tx_id: str) -> int | None:
        row = self.row_for(tx_id)
        return None if row is None else int(row["time_step"])


def _looks_numeric(token: str) -> bool:
    try:
        float(token.strip())
        return True
    except (TypeError, ValueError):
        return False


def _first_row(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        for row in csv.reader(handle):
            return row
    return []


def detect_header(path: Path, *, kind: str) -> bool:
    """Heuristically detect a header row without relying on fixed names."""
    row = _first_row(path)
    if not row:
        return False
    first = row[0].strip().lower()
    if first in ID_LIKE_NAMES:
        return True
    if kind == "features":
        return not _looks_numeric(row[0]) or any(
            (idx > 1 and not _looks_numeric(token)) for idx, token in enumerate(row)
        )
    if kind == "classes":
        return len(row) > 1 and row[1].strip().lower() in LABEL_LIKE_NAMES
    if kind == "edges":
        return len(row) > 1 and row[1].strip().lower() in ID_LIKE_NAMES
    return False


def _read_csv(path: Path, *, kind: str, header: bool | None = None) -> pd.DataFrame:
    has_header = detect_header(path, kind=kind) if header is None else header
    frame = pd.read_csv(
        path,
        header=0 if has_header else None,
        dtype=str,
        keep_default_na=False,
        na_values=["", "?", "NaN", "nan", "null", "NULL", "unknown", "UNKNOWN"],
        encoding="utf-8-sig",
        comment="#",
        engine="python",
    )
    return frame


def _find_file(raw_dir: Path, patterns: Iterable[str], required_name: str) -> Path:
    for pattern in patterns:
        matches = sorted(raw_dir.glob(pattern))
        if matches:
            return matches[0]
    raise DatasetNotFoundError(
        f"Could not find the {required_name} CSV in {raw_dir}. "
        "Expected something like data/raw/elliptic_txs_features.csv. "
        "See docs/KAGGLE_SETUP.md for download instructions, or run in demo mode."
    )


def map_label(raw: object) -> float:
    """Map Elliptic labels to a numeric target: 1=illicit, 0=licit, NaN=unknown."""
    if raw is None or (isinstance(raw, float) and np.isnan(raw)):
        return LABEL_UNKNOWN
    text = str(raw).strip().lower()
    if text in {"1", "illicit", "illegal", "true", "1.0"}:
        return LABEL_ILLICIT
    if text in {"2", "licit", "legal", "false", "0", "0.0"}:
        return LABEL_LICIT
    return LABEL_UNKNOWN


def load_elliptic_dataset(raw_dir: Path) -> TransactionDataset:
    """Load real Elliptic CSVs with header detection and safe alignment."""
    features_path = _find_file(
        raw_dir,
        ("elliptic_txs_features*.csv", "*txs_features*.csv", "*features*.csv"),
        "transaction features",
    )
    classes_path = _find_file(
        raw_dir,
        ("elliptic_txs_classes*.csv", "*txs_classes*.csv", "*classes*.csv"),
        "transaction classes",
    )
    edges_path = _find_file(
        raw_dir,
        ("elliptic_txs_edgelist*.csv", "*txs_edgelist*.csv", "*edgelist*.csv"),
        "transaction edge list",
    )

    features_raw = _read_csv(features_path, kind="features")
    classes_raw = _read_csv(classes_path, kind="classes")
    edges_raw = _read_csv(edges_path, kind="edges")

    if features_raw.shape[1] < 3:
        raise DatasetFormatError(
            "Features CSV must contain at least an ID, a time step and one feature column. "
            f"Got {features_raw.shape[1]} column(s)."
        )
    if classes_raw.shape[1] < 2:
        raise DatasetFormatError("Classes CSV must contain an ID and a label column.")
    if edges_raw.shape[1] < 2:
        raise DatasetFormatError("Edge list CSV must contain two identifier columns.")

    ids = features_raw.iloc[:, 0].astype(str).str.strip()
    if ids.duplicated().any():
        raise DatasetFormatError("Duplicate transaction IDs found in features CSV.")

    time_steps = pd.to_numeric(features_raw.iloc[:, 1], errors="coerce")
    if time_steps.isna().any():
        raise DatasetFormatError("Some time steps in the features CSV are not numeric.")

    feature_values = features_raw.iloc[:, 2:].apply(pd.to_numeric, errors="coerce")
    feature_names = [f"feature_{i:03d}" for i in range(feature_values.shape[1])]

    label_map = {}
    for _, row in classes_raw.iterrows():
        key = str(row.iloc[0]).strip()
        if key and key.lower() not in {"nan", "none"}:
            label_map[key] = map_label(row.iloc[1])

    transactions = pd.DataFrame(
        {
            "tx_id": ids.to_numpy(),
            "time_step": time_steps.astype(int).to_numpy(),
            "label": ids.map(label_map).astype(float).to_numpy(),
            "feature_index": np.arange(len(ids)),
            "dataset_source": "elliptic_kaggle",
        }
    )

    edges = pd.DataFrame(
        {
            "source": edges_raw.iloc[:, 0].astype(str).str.strip(),
            "target": edges_raw.iloc[:, 1].astype(str).str.strip(),
        }
    )
    known = set(transactions["tx_id"])
    before = len(edges)
    edges = edges[edges["source"].isin(known) & edges["target"].isin(known)].reset_index(
        drop=True
    )
    dropped = before - len(edges)

    matrix = feature_values.to_numpy(dtype=np.float32).copy()
    # Replace infinities so downstream imputers see ordinary missing values.
    matrix[~np.isfinite(matrix)] = np.nan

    logger.info(
        "Loaded Elliptic dataset: %d transactions, %d features, %d edges (%d dropped)",
        len(transactions),
        matrix.shape[1],
        len(edges),
        dropped,
    )
    return TransactionDataset(
        transactions=transactions,
        edges=edges,
        feature_matrix=matrix,
        feature_names=feature_names,
        source="elliptic_kaggle",
        is_synthetic=False,
        metadata={
            "features_file": features_path.name,
            "classes_file": classes_path.name,
            "edges_file": edges_path.name,
            "edges_dropped_unknown_ids": dropped,
        },
    )


def generate_demo_dataset(
    output_dir: Path,
    *,
    n_transactions: int = 360,
    n_time_steps: int = 40,
    seed: int = 42,
    force: bool = False,
) -> TransactionDataset:
    """Create a deterministic, explicitly synthetic dataset for demonstrations.

    These identifiers are not Bitcoin hashes and the records are not real
    blockchain observations. Every UI surface must label them as synthetic.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    features_path = output_dir / "demo_txs_features.csv"
    classes_path = output_dir / "demo_txs_classes.csv"
    edges_path = output_dir / "demo_txs_edgelist.csv"
    notice_path = output_dir / "README_SYNTHETIC_DATA.txt"

    if all(p.exists() for p in (features_path, classes_path, edges_path)) and not force:
        return _load_demo_dataset(output_dir)

    rng = np.random.default_rng(seed)
    n_transactions = max(60, int(n_transactions))
    n_time_steps = max(6, int(n_time_steps))
    n_features = 166  # 1 id + 1 time step + 164 Elliptic-like features

    ids = [f"DEMO{i:08d}" for i in range(1, n_transactions + 1)]
    time_steps = rng.integers(1, n_time_steps + 1, size=n_transactions)
    # Three hidden behavioural groups produce learnable but imperfect signal.
    group = rng.choice([0, 1, 2], size=n_transactions, p=[0.13, 0.57, 0.30])
    base = rng.normal(loc=0.0, scale=1.0, size=(n_transactions, n_features - 2)).astype(
        np.float32
    )

    for idx in ILLICIT_FEATURES:
        base[group == 0, idx] += rng.normal(2.2, 0.5, size=(group == 0).sum())
        base[group == 2, idx] += rng.normal(0.8, 0.4, size=(group == 2).sum())
    for idx in LICIT_FEATURES:
        base[group == 1, idx] += rng.normal(1.6, 0.45, size=(group == 1).sum())
    # Correlated "fan-out" feature typical of chaining behaviour.
    base[:, 70] += base[:, 5] * 0.45 + rng.normal(0, 0.2, n_transactions)

    # A small fraction of missing values exercises the imputation pipeline.
    missing = rng.random(base.shape) < 0.006
    base[missing] = np.nan

    labels = np.full(n_transactions, "unknown", dtype=object)
    labels[group == 0] = "1"
    labels[group == 1] = "2"
    # Unknown group 2 stays unlabelled. A few labelled records are also hidden.
    hide = rng.random(n_transactions) < 0.06
    labels[hide] = "unknown"

    # Directed edges: temporal chaining plus a few random cross-links.
    edge_pairs: set[tuple[int, int]] = set()
    ordered = np.argsort(time_steps)
    for position, src in enumerate(ordered):
        if position == 0:
            continue
        candidate_window = ordered[max(0, position - 12) : position]
        for _ in range(int(rng.integers(0, 4))):
            dst = int(rng.choice(candidate_window))
            if src != dst:
                edge_pairs.add((int(src), int(dst)))
    for _ in range(n_transactions // 3):
        src, dst = rng.integers(0, n_transactions, size=2)
        if src != dst:
            edge_pairs.add((int(src), int(dst)))

    feature_lines = []
    for i, tx_id in enumerate(ids):
        values = [tx_id, str(int(time_steps[i]))]
        values += ["" if np.isnan(v) else f"{float(v):.6f}" for v in base[i]]
        feature_lines.append(",".join(values))
    features_path.write_text("\n".join(feature_lines) + "\n", encoding="utf-8")

    classes_path.write_text(
        "\n".join(f"{ids[i]},{labels[i]}" for i in range(n_transactions)) + "\n",
        encoding="utf-8",
    )
    edges_path.write_text(
        "\n".join(f"{ids[src]},{ids[dst]}" for src, dst in sorted(edge_pairs)) + "\n",
        encoding="utf-8",
    )
    notice_path.write_text(
        "SYNTHETIC DEMO DATA - NOT REAL BLOCKCHAIN DATA\n"
        "==============================================\n"
        "Every transaction ID below starts with DEMO and is randomly generated.\n"
        "Labels and features were produced by a seeded simulator, not by the\n"
        "Elliptic dataset and not by any Bitcoin blockchain observation.\n"
        "Use this data only to exercise the application UI and test suite.\n",
        encoding="utf-8",
    )
    logger.info("Generated synthetic demo dataset at %s", output_dir)
    return _load_demo_dataset(output_dir)


def _load_demo_dataset(output_dir: Path) -> TransactionDataset:
    dataset = load_elliptic_dataset(output_dir)
    dataset.source = "demo_synthetic"
    dataset.is_synthetic = True
    dataset.transactions["dataset_source"] = "demo_synthetic"
    return dataset


def load_dataset(
    *,
    source: str = "auto",
    settings: Settings | None = None,
) -> TransactionDataset:
    """Load the requested dataset, with an explicit synthetic fallback."""
    config = settings or get_settings()
    config.ensure_directories()

    if source in {"elliptic", "real"}:
        return load_elliptic_dataset(config.raw_data_path)
    if source in {"demo", "synthetic"}:
        return generate_demo_dataset(
            config.demo_data_path,
            n_transactions=config.demo_transactions,
            n_time_steps=config.demo_time_steps,
            seed=config.random_state,
        )

    try:
        return load_elliptic_dataset(config.raw_data_path)
    except DatasetNotFoundError:
        logger.warning(
            "Real Elliptic CSVs not found; falling back to labelled synthetic demo data."
        )
        return generate_demo_dataset(
            config.demo_data_path,
            n_transactions=config.demo_transactions,
            n_time_steps=config.demo_time_steps,
            seed=config.random_state,
        )
