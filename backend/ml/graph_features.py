"""Practical, leakage-aware NetworkX graph features for transaction nodes."""
from __future__ import annotations

from typing import Iterable

import networkx as nx
import numpy as np
import pandas as pd

from .dataset import LABEL_ILLICIT, LABEL_LICIT, TransactionDataset

GRAPH_FEATURE_NAMES = [
    "graph_in_count",
    "graph_out_count",
    "graph_total_degree",
    "graph_neighbor_known_count",
    "graph_neighbor_illicit_ratio",
    "graph_neighbor_licit_ratio",
    "graph_local_density",
    "graph_component_size",
    "graph_component_illicit_count",
]


def build_temporal_graph(dataset: TransactionDataset) -> nx.DiGraph:
    """Build a directed graph using only non-future relationships.

    An edge is kept only when the source time step is not later than the
    target time step. This prevents future topology from leaking into a
    transaction's features at training time.
    """
    times = dict(
        zip(dataset.transactions["tx_id"], dataset.transactions["time_step"], strict=True)
    )
    graph = nx.DiGraph()
    graph.add_nodes_from(dataset.transactions["tx_id"])
    for source, target in dataset.edges[["source", "target"]].itertuples(index=False):
        if times.get(source, 10**9) <= times.get(target, -1):
            graph.add_edge(source, target)
    return graph


def compute_graph_features(
    dataset: TransactionDataset,
    *,
    graph: nx.DiGraph | None = None,
    feature_names: Iterable[str] | None = None,
) -> tuple[np.ndarray, list[str]]:
    """Return an (n_transactions, n_features) graph-feature matrix."""
    names = list(feature_names or GRAPH_FEATURE_NAMES)
    graph = graph if graph is not None else build_temporal_graph(dataset)
    tx_ids = dataset.transactions["tx_id"].tolist()
    labels = dict(
        zip(dataset.transactions["tx_id"], dataset.transactions["label"], strict=True)
    )

    undirected = graph.to_undirected()
    components = {node: len(comp) for comp in nx.connected_components(undirected) for node in comp}
    component_illicit = {
        node: sum(1 for member in comp if labels.get(member) == LABEL_ILLICIT)
        for comp in nx.connected_components(undirected)
        for node in comp
    }

    rows = np.zeros((len(tx_ids), len(names)), dtype=np.float32)
    for index, tx_id in enumerate(tx_ids):
        predecessors = list(graph.predecessors(tx_id))
        successors = list(graph.successors(tx_id))
        neighbors = set(predecessors) | set(successors)
        known = [labels.get(node) for node in neighbors if pd.notna(labels.get(node))]
        illicit_ratio = (
            sum(1 for label in known if label == LABEL_ILLICIT) / len(known)
            if known
            else 0.0
        )
        licit_ratio = (
            sum(1 for label in known if label == LABEL_LICIT) / len(known)
            if known
            else 0.0
        )
        induced = graph.subgraph(neighbors)
        possible = len(neighbors) * (len(neighbors) - 1)
        density = induced.number_of_edges() / possible if possible else 0.0
        row = {
            "graph_in_count": len(predecessors),
            "graph_out_count": len(successors),
            "graph_total_degree": len(predecessors) + len(successors),
            "graph_neighbor_known_count": len(known),
            "graph_neighbor_illicit_ratio": illicit_ratio,
            "graph_neighbor_licit_ratio": licit_ratio,
            "graph_local_density": density,
            "graph_component_size": components.get(tx_id, 1),
            "graph_component_illicit_count": component_illicit.get(tx_id, 0),
        }
        rows[index] = [row.get(name, 0.0) for name in names]
    return rows, names


def neighborhood(
    graph: nx.DiGraph,
    tx_id: str,
    *,
    depth: int = 1,
    limit: int = 40,
) -> tuple[list[str], list[tuple[str, str]]]:
    """Return a bounded ego-network around a node (no full-graph rendering)."""
    if tx_id not in graph:
        return [], []
    visited = {tx_id}
    frontier = [tx_id]
    for _ in range(max(1, min(int(depth), 3))):
        next_frontier: list[str] = []
        for node in frontier:
            for neighbor in list(graph.successors(node)) + list(graph.predecessors(node)):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_frontier.append(neighbor)
                if len(visited) >= limit:
                    break
            if len(visited) >= limit:
                break
        frontier = next_frontier
        if len(visited) >= limit:
            break
    nodes = list(visited)[:limit]
    node_set = set(nodes)
    edges = [
        (source, target)
        for source, target in graph.edges()
        if source in node_set and target in node_set
    ][: limit * 3]
    return nodes, edges
