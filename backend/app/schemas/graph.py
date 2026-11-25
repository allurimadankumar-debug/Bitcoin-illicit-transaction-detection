from __future__ import annotations

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    id: str
    label: str
    color: str
    risk_score: float | None = None
    time_step: int = 0
    size: int = 8


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphResponse(BaseModel):
    center: str
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    depth: int = 1
    truncated: bool = False
    total_neighbors: int = 0
    is_synthetic: bool = False
    note: str | None = None
