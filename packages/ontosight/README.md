# @royalsolution/ontosight

Visualize [CodeGraph](https://github.com/colbymchenry/codegraph) call subgraphs in [OntoSight](https://pypi.org/project/ontosight/) without installing Hyper-Extract.

This npm package is a thin wrapper that auto-creates the CodeGraph index when missing, then runs the Python package [`ontosight-codegraph`](https://pypi.org/project/ontosight-codegraph/) via `uvx` (or `pipx` as fallback).

## Prerequisites

- **Node 20+** (for npx)
- **Python 3.11+** with **[uv](https://docs.astral.sh/uv/)** (recommended) or **pipx**

## Quick start

```bash
# Opens OntoSight; runs `npx @colbymchenry/codegraph init -i` first if needed
npx @royalsolution/ontosight .

# Seed around a symbol
npx @royalsolution/ontosight . --symbol view_graph --path vendor/ontosight/

# Task-scoped subgraph
npx @royalsolution/ontosight . --task "auth flow" --hops 2 --max-nodes 200
```

Set `ONTOSIGHT_SKIP_AUTO_INIT=1` to require a pre-built index instead of auto-init.

## Options

| Flag | Description |
|------|-------------|
| `--path <prefix>` | Limit symbols to files under this path |
| `--symbol <name>` | Seed symbol for subgraph expansion |
| `--task <text>` | Natural-language task seed |
| `--hops <n>` | BFS hop depth (default: 2) |
| `--max-nodes <n>` | Maximum nodes (default: 200) |

## AI agents

OntoSight complements **CodeGraph MCP** — use `codegraph_*` tools to answer structural questions in chat; use this CLI when the user wants an **interactive call-graph UI**.

| Need | Tool |
|------|------|
| Find symbols, callers, traces, impact (text) | CodeGraph MCP (`codegraph_search`, `codegraph_context`, …) |
| Visual exploration in browser | `npx @royalsolution/ontosight` |

**Full agent guide:** [`AGENTS.md`](./AGENTS.md) — workflows, flags, env vars, troubleshooting.

**Project wiring (Hyper-Extract monorepo):**

| Tool | Location |
|------|----------|
| Cursor | `.cursor/rules/ontosight.mdc`, `.cursor/references/ontosight.md` |
| Kiro | `.kiro/steering/ontosight.md`, `.kiro/references/ontosight.md` |
| Antigravity | `.agent/rules/ontosight.md`, `.agents/references/ontosight.md` |

### Example agent workflow

```text
1. codegraph_context({ task: "auth flow", maxNodes: 20 })  → answer in chat
2. npx @royalsolution/ontosight . --task "auth flow" --hops 2   → open graph for user
```

## Hyper-Extract users

If you already have Hyper-Extract installed, the equivalent command is:

```bash
he show . --codegraph
he show . --codegraph --symbol view_graph --path vendor/ontosight/
```

## Publish (maintainers)

See [`PUBLISH.md`](./PUBLISH.md). Keep `ontosightCodegraphVersion` in `package.json` in sync with the PyPI `ontosight-codegraph` release.
