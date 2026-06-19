# he analyze

Rank critical and most-connected nodes in a graph knowledge abstract.

---

## Synopsis

```bash
he analyze KA_PATH [OPTIONS]
```

## Arguments

| Argument | Description |
|----------|-------------|
| `KA_PATH` | Path to knowledge abstract directory |

## Options

| Option | Description |
|--------|-------------|
| `--top-k`, `-n` | Number of ranked nodes to show (default: 10) |
| `--metric`, `-m` | `degree`, `betweenness`, or `composite` (default) |
| `--tier` | Filter results to a single tier (e.g. `critical`) |
| `--json` | Machine-readable JSON output |

---

## Description

Analyzes graph topology to surface **hub nodes** (high connectivity) and **structurally critical nodes** (articulation points and high betweenness when `networkx` is available).

Composite scoring (default):

`importance = 0.6 × normalized_degree + 0.4 × normalized_betweenness`

Works with:

- `AutoGraph` and temporal/spatial variants
- `AutoHypergraph`

---

## Examples

### Basic ranking

```bash
he analyze ./tesla_kb/
```

### Top 5 by degree only

```bash
he analyze ./tesla_kb/ -n 5 --metric degree
```

### JSON for scripts

```bash
he analyze ./tesla_kb/ --json
```

### Critical tier only

```bash
he analyze ./tesla_kb/ --tier critical
```

---

## Visualization

Open the interactive viewer to see critical nodes highlighted and sized by importance:

```bash
he show ./tesla_kb/
```

OntoSight shows a **Critical / Hub Nodes** sidebar when rankings are available.

---

## See Also

- [`he show`](show.md) — Interactive visualization with critical-node panel
- [`he info`](info.md) — Knowledge abstract statistics
