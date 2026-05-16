import json
import pytest
from nvibrant_tui import config


@pytest.fixture(autouse=True)
def _patch_path(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_PATH", tmp_path / "config.json")


@pytest.fixture
def config_path(tmp_path):
    return tmp_path / "config.json"


def test_load_missing_file():
    assert config.load() == {}


def test_load_valid(config_path):
    config_path.write_text(json.dumps({"values": [0, 512, 1023]}))
    assert config.load() == {"values": [0, 512, 1023]}


def test_load_corrupt_json(config_path):
    config_path.write_text("{not valid json{{{")
    assert config.load() == {}


def test_load_values_strings(config_path):
    config_path.write_text(json.dumps({"values": ["a", "b", "c"]}))
    assert config.load() == {}


def test_load_values_mixed_types(config_path):
    config_path.write_text(json.dumps({"values": [0, "bad", 512]}))
    assert config.load() == {}


def test_save_roundtrip(config_path):
    data = {"values": [0, 256, 512, 1023]}
    config.save(data)
    assert config.load() == data


def test_save_creates_parent_dirs(tmp_path, monkeypatch):
    nested = tmp_path / "a" / "b" / "config.json"
    monkeypatch.setattr(config, "_PATH", nested)
    config.save({"values": [100]})
    assert nested.exists()


def test_save_overwrites_previous(config_path):
    config.save({"values": [100]})
    config.save({"values": [200, 300]})
    assert config.load() == {"values": [200, 300]}
