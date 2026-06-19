"""CLI tests for he analyze topology command."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from hyperextract.cli.cli import app

runner = CliRunner()


@pytest.fixture
def graph_ka_dir(tmp_path):
    ka = tmp_path / "ka"
    ka.mkdir()
    (ka / "metadata.json").write_text(
        json.dumps({"template": "general/graph", "lang": "en"}),
        encoding="utf-8",
    )
    (ka / "data.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {"name": "Hub", "type": "concept", "description": ""},
                    {"name": "A", "type": "concept", "description": ""},
                ],
                "edges": [
                    {
                        "source": "Hub",
                        "target": "A",
                        "type": "related",
                        "description": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return ka


class TestAnalyzeCommand:
    def test_analyze_help(self):
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "--metric" in result.output
        assert "--json" in result.output

    def test_analyze_nonexistent_ka(self):
        result = runner.invoke(app, ["analyze", "/nonexistent/ka/path"])
        assert result.exit_code != 0

    @patch("hyperextract.cli.cli.Template.create")
    @patch("hyperextract.cli.cli.validate_config")
    def test_analyze_non_graph_type(self, _mock_cfg, mock_create, graph_ka_dir):
        mock_ka = MagicMock()
        del mock_ka.analyze_topology
        mock_create.return_value = mock_ka

        result = runner.invoke(app, ["analyze", str(graph_ka_dir)])
        assert result.exit_code != 0
        assert "graph-based" in result.output

    @patch("hyperextract.cli.cli.Template.create")
    @patch("hyperextract.cli.cli.validate_config")
    def test_analyze_json_output(self, _mock_cfg, mock_create, graph_ka_dir):
        from hyperextract.utils.graph_topology import NodeRanking

        mock_ka = MagicMock()
        ranking = NodeRanking(
            node_id="Hub",
            label="Hub",
            degree=1,
            betweenness=0.0,
            is_articulation=False,
            importance=1.0,
            tier="critical",
        )
        mock_ka.nodes = [MagicMock(), MagicMock()]
        mock_ka.analyze_topology.side_effect = [
            [ranking],
            [ranking],
        ]
        mock_create.return_value = mock_ka

        result = runner.invoke(app, ["analyze", str(graph_ka_dir), "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["metric"] == "composite"
        assert payload["rankings"][0]["node_id"] == "Hub"
