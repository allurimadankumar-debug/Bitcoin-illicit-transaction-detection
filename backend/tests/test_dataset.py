from __future__ import annotations

import pytest

from ml.dataset import (
    DatasetFormatError,
    DatasetNotFoundError,
    detect_header,
    generate_demo_dataset,
    load_elliptic_dataset,
    map_label,
)


def test_label_mapping() -> None:
    assert map_label("1") == 1
    assert map_label("2") == 0
    assert map_label("illicit") == 1
    assert map_label("unknown") != map_label("unknown")  # NaN
    assert map_label("garbage") != map_label("garbage")


def test_header_detection(tmp_path) -> None:
    features = tmp_path / "features.csv"
    features.write_text("txId,time,feature_0\n1,2,0.5\n", encoding="utf-8")
    classes = tmp_path / "classes.csv"
    classes.write_text("txId,class\n1,1\n", encoding="utf-8")
    edges = tmp_path / "edges.csv"
    edges.write_text("txId1,txId2\n1,2\n", encoding="utf-8")
    assert detect_header(features, kind="features") is True
    assert detect_header(classes, kind="classes") is True
    assert detect_header(edges, kind="edges") is True

    bare = tmp_path / "bare.csv"
    bare.write_text("1,2,0.5\n2,3,0.2\n", encoding="utf-8")
    assert detect_header(bare, kind="features") is False


def test_demo_dataset_is_clearly_synthetic(demo_dataset) -> None:
    assert demo_dataset.is_synthetic is True
    assert demo_dataset.source == "demo_synthetic"
    assert demo_dataset.size >= 60
    assert demo_dataset.feature_matrix.shape[1] >= 100
    assert demo_dataset.transactions["tx_id"].str.startswith("DEMO").all()
    assert 0 < demo_dataset.illicit_count < demo_dataset.size
    assert 0 < demo_dataset.licit_count < demo_dataset.size
    assert demo_dataset.unknown_count > 0


def test_missing_files_give_helpful_error(tmp_path) -> None:
    with pytest.raises(DatasetNotFoundError, match="KAGGLE_SETUP"):
        load_elliptic_dataset(tmp_path)


def test_malformed_dataset_is_rejected(tmp_path) -> None:
    (tmp_path / "elliptic_txs_features.csv").write_text("1\n2\n", encoding="utf-8")
    (tmp_path / "elliptic_txs_classes.csv").write_text("1,1\n2,2\n", encoding="utf-8")
    (tmp_path / "elliptic_txs_edgelist.csv").write_text("1,2\n", encoding="utf-8")
    with pytest.raises(DatasetFormatError, match="at least"):
        load_elliptic_dataset(tmp_path)


def test_loader_accepts_headered_real_style_files(tmp_path) -> None:
    (tmp_path / "elliptic_txs_features.csv").write_text(
        "txId,time,feature_0,feature_1\n1,1,0.1,0.2\n2,2,0.3,0.4\n3,3,0.5,0.6\n",
        encoding="utf-8",
    )
    (tmp_path / "elliptic_txs_classes.csv").write_text(
        "txId,class\n1,1\n2,2\n3,unknown\n", encoding="utf-8"
    )
    (tmp_path / "elliptic_txs_edgelist.csv").write_text(
        "txId1,txId2\n1,2\n2,3\n", encoding="utf-8"
    )
    dataset = load_elliptic_dataset(tmp_path)
    assert dataset.size == 3
    assert dataset.feature_matrix.shape == (3, 2)
    assert dataset.labeled_mask.sum() == 2
    assert dataset.unknown_count == 1
    assert len(dataset.edges) == 2
