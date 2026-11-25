from __future__ import annotations

from app.services.data import get_dataset, get_graph
from app.services.graph_service import graph_for_transaction
from ml.graph_features import neighborhood


def test_graph_is_directed_and_temporal(demo_dataset) -> None:
    graph = get_graph()
    assert graph.is_directed()
    times = dict(zip(demo_dataset.transactions["tx_id"], demo_dataset.transactions["time_step"], strict=True))
    for source, target in graph.edges():
        assert times[source] <= times[target]


def test_neighborhood_is_bounded(demo_dataset) -> None:
    graph = get_graph()
    center = str(demo_dataset.transactions.iloc[0]["tx_id"])
    nodes, edges = neighborhood(graph, center, depth=1, limit=10)
    assert len(nodes) <= 10
    assert center in nodes
    assert all(source in nodes and target in nodes for source, target in edges)


def test_graph_service_response(demo_dataset) -> None:
    center = str(demo_dataset.transactions.iloc[0]["tx_id"])
    response, found = graph_for_transaction(center, depth=1, limit=20)
    assert found is True
    assert response.center == center
    assert response.is_synthetic is True
    missing, found_missing = graph_for_transaction("DEMO99999999")
    assert found_missing is False
    assert missing.nodes == []
