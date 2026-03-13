"""Tests for broker.config — YAML loading and accessor functions."""

import os

from broker.config import load_config, get_tiled_url, get_api_key, get_max_entities


def test_load_config(sample_config):
    cfg = load_config(sample_config)
    assert "service_dir" in cfg
    assert "data_dir" in cfg
    assert cfg["schema_version"] == "data"
    assert cfg["max_entities"] == 10


def test_load_config_missing_broker_section(tmp_path):
    config_path = tmp_path / "empty.yml"
    config_path.write_text("other_key: 123\n")
    cfg = load_config(config_path)
    assert cfg == {}


def test_get_tiled_url_default(monkeypatch):
    monkeypatch.delenv("TILED_URL", raising=False)
    assert get_tiled_url() == "http://localhost:8005"


def test_get_tiled_url_from_env(monkeypatch):
    monkeypatch.setenv("TILED_URL", "http://example.com:9000")
    assert get_tiled_url() == "http://example.com:9000"


def test_get_api_key_default(monkeypatch):
    monkeypatch.delenv("TILED_API_KEY", raising=False)
    assert get_api_key() == "secret"


def test_get_max_entities_from_config(sample_config):
    cfg = load_config(sample_config)
    assert cfg["max_entities"] == 10
