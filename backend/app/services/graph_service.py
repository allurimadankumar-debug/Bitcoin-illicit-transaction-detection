from __future__ import annotations

from app.schemas.graph import GraphEdge, GraphNode, GraphResponse
from ml.graph_features import neighborhood

from .data import (
    get_dataset,
    get_graph,
    get_risk_scores,
    high_risk_threshold,
    label_name,
    resolve_transaction,
)
from .settings_service import get_setting

COLOR_ILLICIT = "#f43f5e"
COLOR_LICIT = "#22c55e"
COLOR_UNKNOWN = "#64748b"
COLOR_HIGH_RISK = "#a855f7"


def graph_for_transaction(
    tx_id: str, *, depth: int = 1, limit: int = 30
) -> tuple[GraphResponse, bool]:
    resolved = resolve_transaction(tx_id)
    dataset = get_dataset()
    if resolved is None:
        return (
            GraphResponse(
                center=tx_id,
                nodes=[],
                edges=[],
                depth=depth,
                note="Transaction not found in the loaded dataset.",
                is_synthetic=dataset.is_synthetic,
            ),
            False,
        )

    graph = get_graph()
    nodes, edges = neighborhood(graph, resolved, depth=depth, limit=limit)
    scores = get_risk_scores()
    threshold = high_risk_threshold()
    graph_nodes = []
    for node in nodes:
        row = dataset.row_for(node)
        risk = None
        if row is not None and scores is not None:
            risk = float(scores[int(row["feature_index"])])
        ground_truth = label_name(None if row is None else row["label"])
        if ground_truth == "illicit":
            label, color = "illicit", COLOR_ILLICIT
        elif ground_truth == "licit":
            label, color = "licit", COLOR_LICIT
        elif risk is not None and risk >= threshold:
            label, color = "high-risk-prediction", COLOR_HIGH_RISK
        else:
            label, color = "unknown", COLOR_UNKNOWN
        graph_nodes.append(
            GraphNode(
                id=node,
                label=label,
                color=color,
                risk_score=round(risk, 4) if risk is not None else None,
                time_step=0 if row is None else int(row["time_step"]),
                size=11 if node == resolved else 8,
            )
        )

    note = get_setting("graph_note", None)
    return (
        GraphResponse(
            center=resolved,
            nodes=graph_nodes,
            edges=[GraphEdge(source=source, target=target) for source, target in edges],
            depth=depth,
            truncated=len(nodes) >= limit,
            total_neighbors=max(0, len(nodes) - 1),
            is_synthetic=dataset.is_synthetic,
            note=note,
        ),
        True,
    )
