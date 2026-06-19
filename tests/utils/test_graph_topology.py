"""Tests for graph topology ranking utilities."""

import pytest
from pydantic import BaseModel

from hyperextract.utils.graph_topology import (
    TIER_CRITICAL,
    rank_graph_nodes,
    rank_hypergraph_nodes,
    topology_summary,
)


class Entity(BaseModel):
    name: str
    type: str = "concept"


class Relation(BaseModel):
    source: str
    target: str
    relation_type: str = "related"


class HyperRelation(BaseModel):
    members: list[str]
    relation_type: str = "event"


def _graph_rank(nodes, edges, **kwargs):
    return rank_graph_nodes(
        nodes,
        edges,
        node_id_extractor=lambda n: n.name,
        node_ids_in_edge_extractor=lambda e: (e.source, e.target),
        node_label_extractor=lambda n: n.name,
        **kwargs,
    )


def _hyper_rank(nodes, edges, **kwargs):
    return rank_hypergraph_nodes(
        nodes,
        edges,
        node_id_extractor=lambda n: n.name,
        nodes_in_edge_extractor=lambda e: tuple(e.members),
        node_label_extractor=lambda n: n.name,
        **kwargs,
    )


class TestRankGraphNodes:
    def test_empty_graph(self):
        assert _graph_rank([], []) == []

    def test_star_graph_center_has_highest_degree(self):
        nodes = [
            Entity(name="Hub"),
            Entity(name="A"),
            Entity(name="B"),
            Entity(name="C"),
        ]
        edges = [
            Relation(source="Hub", target="A"),
            Relation(source="Hub", target="B"),
            Relation(source="Hub", target="C"),
        ]
        rankings = _graph_rank(nodes, edges, top_k=4)
        assert rankings[0].node_id == "Hub"
        assert rankings[0].degree == 3

    def test_chain_middle_is_articulation_when_networkx_available(self):
        nodes = [Entity(name=n) for n in ("A", "B", "C")]
        edges = [
            Relation(source="A", target="B"),
            Relation(source="B", target="C"),
        ]
        rankings = _graph_rank(nodes, edges, top_k=3)
        by_id = {r.node_id: r for r in rankings}
        assert by_id["B"].degree == 2
        try:
            import networkx  # noqa: F401

            assert by_id["B"].is_articulation is True
        except ImportError:
            assert by_id["B"].is_articulation is False

    def test_isolated_node_zero_degree(self):
        nodes = [Entity(name="Lonely"), Entity(name="A"), Entity(name="B")]
        edges = [Relation(source="A", target="B")]
        rankings = _graph_rank(nodes, edges, top_k=3)
        lonely = next(r for r in rankings if r.node_id == "Lonely")
        assert lonely.degree == 0
        assert lonely.importance == 0.0

    def test_metric_degree_orders_by_connectivity(self):
        nodes = [Entity(name=n) for n in ("A", "B", "C")]
        edges = [
            Relation(source="A", target="B"),
            Relation(source="A", target="C"),
        ]
        rankings = _graph_rank(nodes, edges, top_k=2, metric="degree")
        assert rankings[0].node_id == "A"

    def test_invalid_metric_raises(self):
        with pytest.raises(ValueError, match="metric must be one of"):
            _graph_rank([], [], metric="pagerank")

    def test_top_k_limits_results(self):
        nodes = [Entity(name=f"N{i}") for i in range(5)]
        edges = [Relation(source="N0", target=f"N{i}") for i in range(1, 5)]
        rankings = _graph_rank(nodes, edges, top_k=2)
        assert len(rankings) == 2

    def test_topology_summary(self):
        nodes = [Entity(name="Hub"), Entity(name="A")]
        edges = [Relation(source="Hub", target="A")]
        rankings = _graph_rank(nodes, edges, top_k=10)
        summary = topology_summary(rankings, total_nodes=2)
        assert summary["total_nodes"] == 2
        assert summary["avg_degree"] >= 0


class TestRankHypergraphNodes:
    def test_hyperedge_increments_all_member_degrees(self):
        nodes = [Entity(name=n) for n in ("A", "B", "C", "D")]
        edges = [HyperRelation(members=["A", "B", "C"])]
        rankings = _hyper_rank(nodes, edges, top_k=4)
        by_id = {r.node_id: r for r in rankings}
        assert by_id["A"].degree == 2
        assert by_id["B"].degree == 2
        assert by_id["C"].degree == 2
        assert by_id["D"].degree == 0

    def test_critical_tier_assigned_to_hub(self):
        nodes = [Entity(name=n) for n in ("Hub", "X", "Y", "Z")]
        edges = [
            HyperRelation(members=["Hub", "X"]),
            HyperRelation(members=["Hub", "Y"]),
            HyperRelation(members=["Hub", "Z"]),
        ]
        rankings = _hyper_rank(nodes, edges, top_k=4)
        hub = next(r for r in rankings if r.node_id == "Hub")
        assert hub.tier in (TIER_CRITICAL, "high")
