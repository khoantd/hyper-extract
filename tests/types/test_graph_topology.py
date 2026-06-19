"""Unit tests for AutoGraph topology analysis."""

from pydantic import BaseModel, Field

from hyperextract.types import AutoGraph


class Entity(BaseModel):
    name: str
    type: str = "concept"
    properties: dict = Field(default_factory=dict)


class Relation(BaseModel):
    source: str
    target: str
    relation_type: str = "related"


class TestAutoGraphTopology:
    def test_analyze_topology_star(self, llm_client, embedder):
        graph = AutoGraph(
            node_schema=Entity,
            edge_schema=Relation,
            node_key_extractor=lambda x: x.name,
            edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
            nodes_in_edge_extractor=lambda x: (x.source, x.target),
            llm_client=llm_client,
            embedder=embedder,
        )
        graph._node_memory.add([
            Entity(name="Hub"),
            Entity(name="A"),
            Entity(name="B"),
        ])
        graph._edge_memory.add([
            Relation(source="Hub", target="A"),
            Relation(source="Hub", target="B"),
        ])

        rankings = graph.analyze_topology(top_k=3)
        assert rankings[0].node_id == "Hub"
        assert rankings[0].degree == 2

    def test_critical_nodes_alias(self, llm_client, embedder):
        graph = AutoGraph(
            node_schema=Entity,
            edge_schema=Relation,
            node_key_extractor=lambda x: x.name,
            edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
            nodes_in_edge_extractor=lambda x: (x.source, x.target),
            llm_client=llm_client,
            embedder=embedder,
        )
        graph._node_memory.add([Entity(name="A"), Entity(name="B")])
        graph._edge_memory.add([Relation(source="A", target="B")])

        critical = graph.critical_nodes(top_k=2)
        assert len(critical) == 2

    def test_topology_view_context(self, llm_client, embedder):
        graph = AutoGraph(
            node_schema=Entity,
            edge_schema=Relation,
            node_key_extractor=lambda x: x.name,
            edge_key_extractor=lambda x: f"{x.source}-{x.relation_type}-{x.target}",
            nodes_in_edge_extractor=lambda x: (x.source, x.target),
            llm_client=llm_client,
            embedder=embedder,
        )
        graph._node_memory.add([Entity(name="A"), Entity(name="B")])
        graph._edge_memory.add([Relation(source="A", target="B")])

        ctx = graph._topology_view_context(top_k=2)
        assert "node_rankings" in ctx
        assert "critical_node_ids" in ctx
        assert ctx["topology_total_nodes"] == 2
