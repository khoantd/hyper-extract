"""
Remote LiteLLM Proxy Demo

Extract entities and relationships using a remote LiteLLM OpenAI-compatible proxy.
Requires a running LiteLLM proxy with configured models for LLM and embeddings.

Usage:
    export LITELLM_BASE_URL=https://litellm.example.com/v1
    export LITELLM_API_KEY=sk-your-master-key
    python examples/providers/litellm_demo.py
"""

import os

from hyperextract import create_client, AutoGraph

proxy_url = os.environ.get("LITELLM_BASE_URL", "https://litellm.example.com/v1")
api_key = os.environ.get("LITELLM_API_KEY", "sk-your-master-key")

llm, emb = create_client(
    llm=f"litellm:gpt-4o-mini@{proxy_url}",
    embedder=f"litellm:text-embedding-3-small@{proxy_url}",
    api_key=api_key,
)

graph = AutoGraph(
    instruction="Extract people and their relationships",
    llm_client=llm,
    embedder=emb,
    node_key_extractor=lambda n: n.name,
    edge_key_extractor=lambda e: (e.source, e.target, e.type),
    nodes_in_edge_extractor=lambda e: (e.source, e.target),
)

text = "Zhang San founded ByteDance. Li Si serves as CEO."
graph.parse(text)

print(f"Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)}")
for n in graph.nodes:
    print(f"  - {n.name} ({n.type})")
