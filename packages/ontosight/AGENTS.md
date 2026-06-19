# OntoSight — AI agent usage guide

**OntoSight** visualizes [CodeGraph](https://github.com/colbymchenry/codegraph) call subgraphs in an interactive browser UI. This package (`@royalsolution/ontosight`) is a zero-install npx wrapper around the Python [`ontosight-codegraph`](https://pypi.org/project/ontosight-codegraph/) CLI.

OntoSight is **not** an MCP server. Agents do not call `ontosight_*` tools. Use **CodeGraph MCP** (`codegraph_*`) to answer structural questions in chat; use **OntoSight** when the user wants a visual, interactive call graph.

---

## CodeGraph MCP vs OntoSight

| Goal | Use | Why |
|------|-----|-----|
| Where is X defined? | `codegraph_search` | Sub-ms text answer in chat |
| What calls / is called by Y? | `codegraph_callers` / `codegraph_callees` | Precise lists without opening a browser |
| Trace flow from A → B | `codegraph_trace` | Full path in one MCP call |
| Blast radius of a change | `codegraph_impact` | Ranked impact list |
| Focused context for a task | `codegraph_context` | Curated symbol set for reasoning |
| **Visual exploration** of a subgraph | `npx @royalsolution/ontosight` | Interactive graph + critical-node rankings |
| User says "show me the graph" | OntoSight CLI | Browser UI; user pans, zooms, re-queries |

**Rule of thumb:** gather facts with CodeGraph MCP; open OntoSight when visualization helps the **human** explore complexity you already identified.

---

## When agents should run OntoSight

Run (or suggest) OntoSight when the user:

- Asks to **visualize**, **show**, or **explore** a call graph or architecture
- Wants an **interactive** view after you surfaced symbols via `codegraph_search` / `codegraph_context`
- Is doing **onboarding** or **architecture review** and benefits from a graph UI

Do **not** run OntoSight to collect agent context — that duplicates CodeGraph MCP and blocks the terminal while the browser is open.

---

## Commands

### npm wrapper (recommended)

Auto-creates the CodeGraph index when `.codegraph/codegraph.db` is missing (unless `ONTOSIGHT_SKIP_AUTO_INIT=1`).

```bash
# Full project — seeds from highest fan-in symbols
npx @royalsolution/ontosight .

# Seed around a symbol (optionally scoped to a path)
npx @royalsolution/ontosight . --symbol view_graph --path vendor/ontosight/

# Task-scoped subgraph (keyword FTS seeding)
npx @royalsolution/ontosight . --task "auth flow" --hops 2 --max-nodes 200
```

### Hyper-Extract (monorepo / installed users)

```bash
he show . --codegraph
he show . --codegraph --symbol view_graph --path vendor/ontosight/
he show . --codegraph --task "OntoSight codegraph integration" --hops 2
```

### Python direct (uv / pipx)

```bash
npx @colbymchenry/codegraph init -i   # if index missing
uvx ontosight-codegraph . --symbol view_graph
```

---

## Flags

| Flag | Description | Default |
|------|-------------|---------|
| `[project-path]` | Project root containing `.codegraph/` | `.` (cwd) |
| `--path <prefix>` | Limit symbols to files under this path | — |
| `--symbol <name>` | Seed symbol for BFS subgraph expansion | auto (fan-in) |
| `--task <text>` | Natural-language seed (keyword match) | — |
| `--hops <n>` | BFS hop depth | `2` |
| `--max-nodes <n>` | Cap subgraph size | `200` |

`--symbol` and `--task` are mutually exclusive seeds; `--path` narrows either.

---

## Suggested agent workflows

### 1. Symbol the user named

```text
1. codegraph_search({ query: "view_graph" })     → confirm file + kind
2. Tell user what you found
3. npx @royalsolution/ontosight . --symbol view_graph --path <dir-from-search>
```

### 2. Feature area ("how does auth work?")

```text
1. codegraph_context({ task: "authentication flow", maxNodes: 20 })
2. Summarize key symbols in chat
3. npx @royalsolution/ontosight . --task "authentication flow" --hops 2 --max-nodes 200
```

### 3. Large repo — narrow first

Prefer `--path` or `--symbol` before raising `--max-nodes`. If CLI prints a truncation warning, retry with a narrower `--path` or specific `--symbol`.

### 4. Index missing

```bash
npx @colbymchenry/codegraph init -i
# or let the wrapper auto-init (default)
```

Ask the user before auto-init on very large repos (first index can take a minute).

---

## Environment variables

| Variable | Effect |
|----------|--------|
| `ONTOSIGHT_SKIP_AUTO_INIT=1` | Fail if `.codegraph/codegraph.db` missing instead of running init |
| `ONTOSIGHT_CODEGRAPH_VERSION` | Pin PyPI `ontosight-codegraph` version (overrides `package.json`) |

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Node 20+ | For `npx @royalsolution/ontosight` |
| Python 3.11+ | Used by `ontosight-codegraph` |
| [uv](https://docs.astral.sh/uv/) (recommended) or pipx | Wrapper tries `uvx` first, then `pipx run` |
| CodeGraph index | `.codegraph/codegraph.db` in project root |

---

## What the user sees

1. Terminal prints project path, seed, hops/max-nodes, and a **topology table** (critical / hub nodes).
2. OntoSight opens in the browser with the call subgraph, critical-node highlights, and a CodeGraph query panel for live reloads.
3. Process stays running until the user closes the server (Ctrl+C in terminal).

---

## Troubleshooting

| Issue | Action |
|-------|--------|
| `CodeGraph index not found` | Run `npx @colbymchenry/codegraph init -i` or remove `ONTOSIGHT_SKIP_AUTO_INIT` |
| `Neither uv nor pipx found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Subgraph truncated warning | Add `--symbol`, `--task`, or `--path`; lower scope before raising `--max-nodes` |
| Stale symbols after edits | Wait ~2s for CodeGraph watcher sync, or re-run init |
| Agent needs facts, not UI | Use `codegraph_*` MCP tools instead |

---

## Project wiring (Hyper-Extract monorepo)

| Tool | Rules / reference |
|------|-------------------|
| Cursor | `.cursor/rules/ontosight.mdc`, `.cursor/references/ontosight.md` |
| Kiro | `.kiro/steering/ontosight.md`, `.kiro/references/ontosight.md` |
| Antigravity | `.agent/rules/ontosight.md`, `.agents/references/ontosight.md` |

CodeGraph MCP setup: see `.cursor/rules/codegraph.mdc` (and sibling tool trees).
