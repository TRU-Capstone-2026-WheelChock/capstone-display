from __future__ import annotations

from pathlib import Path

from capstone_display.config import load_config, resolve_config_path


def test_resolve_config_path_prefers_explicit_arg(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DISPLAY_CONFIG_PATH", "/tmp/from-env.yml")

    resolved = resolve_config_path(str(tmp_path / "explicit.yml"))

    assert resolved == tmp_path / "explicit.yml"


def test_load_config_uses_env_when_no_explicit_arg(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "display.yml"
    config_path.write_text(
        """
logging:
  level: debug
zmq:
  sub:
    endpoint: "tcp://center:5556"
    topic: ""
    is_bind: false
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("DISPLAY_CONFIG_PATH", str(config_path))

    config = load_config()

    assert config.logging.level == "DEBUG"
    assert config.zmq.sub.endpoint == "tcp://center:5556"
    assert config.zmq.sub.topic == ""
    assert config.zmq.sub.is_bind is False
