"""Graph topology analysis — rank nodes by connectivity and structural importance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, List, Optional, Sequence, Tuple, TypeVar

NodeSchema = TypeVar("NodeSchema")
EdgeSchema = TypeVar("EdgeSchema")

TIER_CRITICAL = "critical"
TIER_HIGH = "high"
TIER_MEDIUM = "medium"
TIER_LOW = "low"

VALID_METRICS = frozenset({"degree", "betweenness", "composite"})


def _ensure_networkx():
    """Lazy import networkx; optional for betweenness and articulation."""
    try:
        import networkx as nx

        return nx
    except ImportError:
        return None


def _normalize(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    lo = min(values.values())
    hi = max(values.values())
    if hi == lo:
        return {k: 1.0 if hi > 0 else 0.0 for k in values}
    return {k: (v - lo) / (hi - lo) for k, v in values.items()}


def _assign_tiers(
    node_ids: list[str],
    importance: dict[str, float],
    articulation: set[str],
) -> dict[str, str]:
    if not node_ids:
        return {}

    sorted_ids = sorted(node_ids, key=lambda nid: importance.get(nid, 0.0), reverse=True)
    n = len(sorted_ids)
    critical_cutoff = max(1, int(n * 0.1))
    high_cutoff = max(critical_cutoff + 1, int(n * 0.25))

    tiers: dict[str, str] = {}
    for i, nid in enumerate(sorted_ids):
        if nid in articulation or i < critical_cutoff:
            tiers[nid] = TIER_CRITICAL
        elif i < high_cutoff:
            tiers[nid] = TIER_HIGH
        elif i < max(high_cutoff + 1, int(n * 0.6)):
            tiers[nid] = TIER_MEDIUM
        else:
            tiers[nid] = TIER_LOW
    return tiers


@dataclass(frozen=True)
class NodeRanking:
    """Ranked node with topology metrics."""

    node_id: str
    label: str
    degree: int
    betweenness: float
    is_articulation: bool
    importance: float
    tier: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def _build_undirected_graph(
    node_ids: set[str],
    edges: list[tuple[str, str]],
) -> Any:
    nx = _ensure_networkx()
    if nx is None:
        return None
    g = nx.Graph()
    g.add_nodes_from(node_ids)
    for a, b in edges:
        if a in node_ids and b in node_ids and a != b:
            g.add_edge(a, b)
    return g


def _compute_degrees(
    node_ids: set[str],
    edges: list[tuple[str, str]],
) -> dict[str, int]:
    degree: dict[str, int] = {nid: 0 for nid in node_ids}
    for a, b in edges:
        if a not in node_ids or b not in node_ids:
            continue
        if a == b:
            continue
        degree[a] += 1
        degree[b] += 1
    return degree


def _rank_nodes(
    node_list: Sequence[NodeSchema],
    edge_pairs: list[tuple[str, str]],
    *,
    node_id_extractor: Callable[[NodeSchema], str],
    node_label_extractor: Optional[Callable[[NodeSchema], str]],
    top_k: int = 10,
    metric: str = "composite",
    include_betweenness: bool = True,
) -> list[NodeRanking]:
    if metric not in VALID_METRICS:
        raise ValueError(f"metric must be one of {sorted(VALID_METRICS)}, got {metric!r}")

    label_fn = node_label_extractor or (lambda n: str(node_id_extractor(n)))

    node_ids: set[str] = set()
    labels: dict[str, str] = {}
    for node in node_list:
        nid = str(node_id_extractor(node))
        node_ids.add(nid)
        labels[nid] = str(label_fn(node))

    if not node_ids:
        return []

    degree = _compute_degrees(node_ids, edge_pairs)
    nx_graph = _build_undirected_graph(node_ids, edge_pairs) if include_betweenness else None

    betweenness: dict[str, float] = {nid: 0.0 for nid in node_ids}
    articulation: set[str] = set()

    if nx_graph is not None and nx_graph.number_of_edges() > 0:
        nx = _ensure_networkx()
        assert nx is not None
        raw_betweenness = nx.betweenness_centrality(nx_graph, normalized=True)
        betweenness = {nid: float(raw_betweenness.get(nid, 0.0)) for nid in node_ids}
        articulation = set(nx.articulation_points(nx_graph))

    norm_degree = _normalize({nid: float(degree[nid]) for nid in node_ids})
    norm_betweenness = _normalize(betweenness)

    importance: dict[str, float] = {}
    for nid in node_ids:
        if metric == "degree":
            importance[nid] = norm_degree[nid]
        elif metric == "betweenness":
            importance[nid] = norm_betweenness[nid]
        else:
            if nx_graph is not None and nx_graph.number_of_edges() > 0:
                importance[nid] = 0.6 * norm_degree[nid] + 0.4 * norm_betweenness[nid]
            else:
                importance[nid] = norm_degree[nid]

    tiers = _assign_tiers(list(node_ids), importance, articulation)

    rankings = [
        NodeRanking(
            node_id=nid,
            label=labels[nid],
            degree=degree[nid],
            betweenness=round(betweenness[nid], 6),
            is_articulation=nid in articulation,
            importance=round(importance[nid], 6),
            tier=tiers[nid],
        )
        for nid in node_ids
    ]
    rankings.sort(
        key=lambda r: (r.importance, r.degree, r.betweenness, r.label),
        reverse=True,
    )
    if top_k > 0:
        rankings = rankings[:top_k]
    return rankings


def rank_graph_nodes(
    node_list: Sequence[NodeSchema],
    edge_list: Sequence[EdgeSchema],
    *,
    node_id_extractor: Callable[[NodeSchema], str],
    node_ids_in_edge_extractor: Callable[[EdgeSchema], Tuple[str, str]],
    node_label_extractor: Optional[Callable[[NodeSchema], str]] = None,
    top_k: int = 10,
    metric: str = "composite",
    include_betweenness: bool = True,
) -> list[NodeRanking]:
    """Rank nodes in a pairwise graph by topology metrics."""
    edge_pairs: list[tuple[str, str]] = []
    for edge in edge_list:
        source_id, target_id = node_ids_in_edge_extractor(edge)
        edge_pairs.append((str(source_id), str(target_id)))

    return _rank_nodes(
        node_list,
        edge_pairs,
        node_id_extractor=node_id_extractor,
        node_label_extractor=node_label_extractor,
        top_k=top_k,
        metric=metric,
        include_betweenness=include_betweenness,
    )


def rank_hypergraph_nodes(
    node_list: Sequence[NodeSchema],
    edge_list: Sequence[EdgeSchema],
    *,
    node_id_extractor: Callable[[NodeSchema], str],
    nodes_in_edge_extractor: Callable[[EdgeSchema], Sequence[str]],
    node_label_extractor: Optional[Callable[[NodeSchema], str]] = None,
    top_k: int = 10,
    metric: str = "composite",
    include_betweenness: bool = True,
) -> list[NodeRanking]:
    """Rank nodes in a hypergraph by hyperedge participation (clique-expanded for betweenness)."""
    edge_pairs: list[tuple[str, str]] = []
    for edge in edge_list:
        members = [str(m) for m in nodes_in_edge_extractor(edge)]
        unique_members = list(dict.fromkeys(members))
        for i, a in enumerate(unique_members):
            for b in unique_members[i + 1 :]:
                edge_pairs.append((a, b))

    return _rank_nodes(
        node_list,
        edge_pairs,
        node_id_extractor=node_id_extractor,
        node_label_extractor=node_label_extractor,
        top_k=top_k,
        metric=metric,
        include_betweenness=include_betweenness,
    )


def topology_summary(rankings: list[NodeRanking], total_nodes: int) -> dict[str, Any]:
    """Aggregate KPIs for CLI / MCP display."""
    if total_nodes == 0:
        return {
            "total_nodes": 0,
            "avg_degree": 0.0,
            "articulation_count": 0,
            "critical_count": 0,
        }
    all_degrees = [r.degree for r in rankings]
    avg_degree = sum(all_degrees) / total_nodes if total_nodes else 0.0
    return {
        "total_nodes": total_nodes,
        "avg_degree": round(avg_degree, 2),
        "articulation_count": sum(1 for r in rankings if r.is_articulation),
        "critical_count": sum(1 for r in rankings if r.tier == TIER_CRITICAL),
    }
