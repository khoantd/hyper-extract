"""Rich terminal display for graph topology rankings."""

from __future__ import annotations

from typing import Any, Optional

from rich.console import Console
from rich.table import Table

_TIER_STYLES = {
    "critical": "bold #F59E0B",
    "high": "#1E40AF",
    "medium": "dim",
    "low": "dim italic",
}


def _summary_from_rows(rankings: list[dict[str, Any]], total_nodes: int) -> dict[str, Any]:
    if total_nodes == 0:
        return {
            "total_nodes": 0,
            "avg_degree": 0.0,
            "articulation_count": 0,
            "critical_count": 0,
        }
    return {
        "total_nodes": total_nodes,
        "avg_degree": round(
            sum(r.get("degree", 0) for r in rankings) / total_nodes,
            2,
        ),
        "articulation_count": sum(1 for r in rankings if r.get("is_articulation")),
        "critical_count": sum(1 for r in rankings if r.get("tier") == "critical"),
    }


def print_topology_table(
    rankings: list[dict[str, Any]],
    *,
    total_nodes: int,
    metric: str = "composite",
    console: Optional[Console] = None,
) -> None:
    """Print a data-dense critical-nodes table to the terminal."""
    if not rankings:
        return

    out = console or Console()
    summary = _summary_from_rows(rankings, total_nodes)

    out.print(
        f"[dim]Topology[/dim]  nodes={summary['total_nodes']}  "
        f"avg_degree={summary['avg_degree']}  "
        f"articulation={summary['articulation_count']}  "
        f"critical={summary['critical_count']}  "
        f"metric={metric}"
    )

    table = Table(title="Critical / Hub Nodes", show_header=True, header_style="bold")
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("Node", style="cyan", max_width=40, overflow="ellipsis")
    table.add_column("Degree", justify="right")
    table.add_column("Between.", justify="right")
    table.add_column("Importance", justify="right")
    table.add_column("Tier")

    for i, row in enumerate(rankings, start=1):
        tier = row.get("tier", "low")
        style = _TIER_STYLES.get(tier, "")
        articulation = " [dim]cut[/dim]" if row.get("is_articulation") else ""
        table.add_row(
            str(i),
            str(row.get("label", row.get("node_id", ""))) + articulation,
            str(row.get("degree", 0)),
            f"{row.get('betweenness', 0):.3f}",
            f"{row.get('importance', 0):.3f}",
            f"[{style}]{tier}[/{style}]" if style else tier,
        )

    out.print(table)


def rankings_to_json_payload(
    rankings: list[dict[str, Any]],
    *,
    total_nodes: int,
    metric: str = "composite",
    all_rankings: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Serialize rankings for ``he analyze --json`` and MCP."""
    full = all_rankings if all_rankings is not None else rankings
    return {
        "metric": metric,
        "total_nodes": total_nodes,
        "summary": _summary_from_rows(full, total_nodes),
        "rankings": rankings,
        "critical_node_ids": [
            r["node_id"]
            for r in full
            if r.get("tier") in ("critical", "high")
        ],
    }
