"""Tests for LiteLLM proxy provider integration."""

import pytest

from hyperextract.utils.client import _env_api_key
from hyperextract.cli.config import ConfigManager


class TestEnvApiKeyLitellm:
    def test_prefers_litellm_api_key(self, monkeypatch):
        monkeypatch.setenv("LITELLM_API_KEY", "sk-litellm")
        monkeypatch.setenv("LITELLM_MASTER_KEY", "sk-master")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
        assert _env_api_key("litellm") == "sk-litellm"

    def test_falls_back_to_master_key(self, monkeypatch):
        monkeypatch.delenv("LITELLM_API_KEY", raising=False)
        monkeypatch.setenv("LITELLM_MASTER_KEY", "sk-master")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
        assert _env_api_key("litellm") == "sk-master"

    def test_falls_back_to_openai_key(self, monkeypatch):
        monkeypatch.delenv("LITELLM_API_KEY", raising=False)
        monkeypatch.delenv("LITELLM_MASTER_KEY", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")
        assert _env_api_key("litellm") == "sk-openai"


class TestConfigManagerLitellm:
    def test_get_llm_config_uses_litellm_base_url_env(self, tmp_path, monkeypatch):
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.setenv("LITELLM_BASE_URL", "https://litellm.example.com/v1")
        monkeypatch.setenv("LITELLM_API_KEY", "sk-master")

        cm = ConfigManager(tmp_path / "config.toml")
        cm.set_llm(provider="litellm", model="gpt-4o-mini", api_key="", base_url="")
        cfg = cm.get_llm_config()

        assert cfg.base_url == "https://litellm.example.com/v1"
        assert cfg.api_key == "sk-master"

    def test_validate_requires_base_url(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LITELLM_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.setenv("LITELLM_API_KEY", "sk-master")

        cm = ConfigManager(tmp_path / "config.toml")
        cm.set_llm(provider="litellm", model="gpt-4o-mini", api_key="sk-master", base_url="")
        cm.set_embedder(
            provider="litellm",
            model="text-embedding-3-small",
            api_key="sk-master",
            base_url="",
        )

        valid, msg = cm.validate()
        assert not valid
        assert "base_url" in msg.lower()

    def test_validate_requires_api_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LITELLM_API_KEY", raising=False)
        monkeypatch.delenv("LITELLM_MASTER_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        cm = ConfigManager(tmp_path / "config.toml")
        cm.set_llm(
            provider="litellm",
            model="gpt-4o-mini",
            api_key="",
            base_url="https://litellm.example.com/v1",
        )
        cm.set_embedder(
            provider="litellm",
            model="text-embedding-3-small",
            api_key="",
            base_url="https://litellm.example.com/v1",
        )

        valid, msg = cm.validate()
        assert not valid
        assert "master" in msg.lower() or "api key" in msg.lower()

    def test_validate_passes_with_full_config(self, tmp_path):
        cm = ConfigManager(tmp_path / "config.toml")
        cm.set_llm(
            provider="litellm",
            model="gpt-4o-mini",
            api_key="sk-master",
            base_url="https://litellm.example.com/v1",
        )
        cm.set_embedder(
            provider="litellm",
            model="text-embedding-3-small",
            api_key="sk-master",
            base_url="https://litellm.example.com/v1",
        )

        valid, msg = cm.validate()
        assert valid, msg

    def test_get_llm_config_raises_without_base_url(self, tmp_path, monkeypatch):
        monkeypatch.delenv("LITELLM_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        cm = ConfigManager(tmp_path / "config.toml")
        cm.set_llm(provider="litellm", model="gpt-4o-mini", api_key="sk-master", base_url="")

        with pytest.raises(ValueError, match="base_url"):
            cm.get_llm_config()
