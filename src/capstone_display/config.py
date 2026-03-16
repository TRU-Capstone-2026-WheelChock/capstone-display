from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = "config/config.yml"
CONFIG_PATH_ENV = "DISPLAY_CONFIG_PATH"


@dataclass(frozen=True, slots=True)
class LoggingConfig:
    level: str = "INFO"


@dataclass(frozen=True, slots=True)
class SubscriptionConfig:
    endpoint: str = "tcp://host.docker.internal:5556"
    topics: list[str] = field(default_factory=lambda: [""])
    is_bind: bool = False


@dataclass(frozen=True, slots=True)
class ZmqConfig:
    sub: SubscriptionConfig = field(default_factory=SubscriptionConfig)


@dataclass(frozen=True, slots=True)
class DisplayConfig:
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    zmq: ZmqConfig = field(default_factory=ZmqConfig)


def resolve_config_path(config_path: str | None = None) -> Path:
    if config_path:
        return Path(config_path)
    env_value = os.getenv(CONFIG_PATH_ENV)
    if env_value:
        return Path(env_value)
    return Path(DEFAULT_CONFIG_PATH)


def _expect_mapping(value: Any, *, label: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a mapping")
    return value


def _coerce_topics(value: Any) -> list[str]:
    if value is None:
        return [""]
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise SystemExit("zmq.sub.topics must be a list of strings")
    return value


def load_config(config_path: str | None = None) -> DisplayConfig:
    path = resolve_config_path(config_path)

    try:
        with path.open("r", encoding="utf-8") as file:
            raw_config = yaml.safe_load(file) or {}
    except FileNotFoundError as exc:
        raise SystemExit(f"config not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise SystemExit(f"invalid yaml: {exc}") from exc

    if not isinstance(raw_config, dict):
        raise SystemExit("config root must be a mapping")

    logging_cfg = _expect_mapping(raw_config.get("logging"), label="logging")
    zmq_cfg = _expect_mapping(raw_config.get("zmq"), label="zmq")
    sub_cfg = _expect_mapping(zmq_cfg.get("sub"), label="zmq.sub")

    endpoint = sub_cfg.get("endpoint", "tcp://host.docker.internal:5556")
    if not isinstance(endpoint, str):
        raise SystemExit("zmq.sub.endpoint must be a string")

    is_bind = sub_cfg.get("is_bind", False)
    if not isinstance(is_bind, bool):
        raise SystemExit("zmq.sub.is_bind must be a bool")

    level = logging_cfg.get("level", "INFO")
    if not isinstance(level, str):
        raise SystemExit("logging.level must be a string")

    topics = _coerce_topics(sub_cfg.get("topics", sub_cfg.get("topic")))

    return DisplayConfig(
        logging=LoggingConfig(level=level.upper()),
        zmq=ZmqConfig(
            sub=SubscriptionConfig(
                endpoint=endpoint,
                topics=topics,
                is_bind=is_bind,
            )
        ),
    )
