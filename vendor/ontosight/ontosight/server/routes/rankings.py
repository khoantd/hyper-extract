"""API route: GET /api/rankings - node topology rankings for critical-node panel."""

import logging

from fastapi import APIRouter, HTTPException

from ontosight.server.state import global_state

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/rankings")
async def get_rankings() -> dict:
    """Return precomputed node importance rankings when available."""
    data = global_state.get_all_visualization_data()
    rankings = data.get("node_rankings", [])
    if not rankings:
        raise HTTPException(status_code=404, detail="No topology rankings available")

    return {
        "rankings": rankings,
        "critical_node_ids": data.get("critical_node_ids", []),
        "metric": data.get("topology_metric", "composite"),
        "total_nodes": data.get("topology_total_nodes"),
    }
