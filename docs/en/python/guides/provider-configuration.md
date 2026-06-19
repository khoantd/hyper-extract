# Provider Configuration Guide

Configure Hyper-Extract to work with OpenAI, Bailian (Alibaba Cloud), local vLLM, or remote LiteLLM proxy deployments.

---

## Unified Example

All three platforms run the **same extraction task** below. Only the client setup (first 3 lines) changes.

### OpenAI

```python
from hyperextract import create_client, AutoGraph

llm, emb = create_client("openai", api_key="sk-xxx")
```

### Alibaba Bailian

```python
from hyperextract import create_client, AutoGraph

llm, emb = create_client("bailian", api_key="sk-xxx")
# Or override model: create_client("bailian:qwen3.6-plus", api_key="sk-xxx")
```

### Local vLLM

```python
from hyperextract import create_client, AutoGraph

llm, emb = create_client(
    llm="vllm:Qwen3.5-9B@http://localhost:8000/v1",
    embedder="vllm:bge-m3@http://localhost:8001/v1",
    api_key="dummy",
)
```

### Remote LiteLLM Proxy

```python
import os
from hyperextract import create_client, AutoGraph

proxy_url = os.environ["LITELLM_BASE_URL"]  # e.g. https://litellm.example.com/v1
llm, emb = create_client(
    llm=f"litellm:gpt-4o-mini@{proxy_url}",
    embedder=f"litellm:text-embedding-3-small@{proxy_url}",
    api_key=os.environ["LITELLM_API_KEY"],
)
```

### Extraction Task (same for all)

```python
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
```

---

## CLI Equivalents

| Platform | Command |
|----------|---------|
| **OpenAI** | `he config init -p openai -k sk-xxx` |
| **Bailian** | `he config init -p bailian -k sk-xxx` |
| **vLLM** | `he config init` → select "local vLLM" |
| **LiteLLM** | `he config init` → select "LiteLLM Proxy", or `he config llm -p litellm -u https://proxy/v1 -k MASTER_KEY -m gpt-4o-mini` |
| **Mixed** (LLM=Bailian, Embedder=vLLM) | `he config llm -p bailian -k sk-xxx` + `he config embedder -p vllm -u http://localhost:8001/v1 -k dummy` |

---

## String Shorthand Format

`create_client()` supports a compact string syntax for quick configuration:

| Format | Example | Result |
|--------|---------|--------|
| `provider` | `"bailian"` | Uses preset defaults for LLM + embedder |
| `provider:model` | `"bailian:qwen3.6-plus"` | Overrides LLM model, keeps preset embedder |
| `provider:model@url` | `"vllm:Qwen3.5-9B@localhost:8000/v1"` | Full manual specification |

---

## Using Config File Instead

If you prefer file-based configuration, run `he config init` once and then use `Template.create()` or `get_client()`:

```python
from hyperextract import get_client, AutoGraph

llm, emb = get_client()  # Reads ~/.he/config.toml
graph = AutoGraph(..., llm_client=llm, embedder=emb)
```

---

## See Also

- [Provider System & Model Compatibility](../../concepts/provider-system.md) — Full compatibility table and vLLM deployment guide
- [CLI Configuration Reference](../../cli/configuration.md) — Complete `he config` command reference
