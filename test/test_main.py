from __future__ import annotations

import asyncio
from types import SimpleNamespace

from msg_handler.schemas import DisplayMessage, MotorState

import capstone_display.main as target
from capstone_display.main import _serialize_received_payload


def test_serialize_received_payload() -> None:
    msg = DisplayMessage(
        sender_id="center-1",
        is_override_mode=False,
        moter_mode=MotorState.FOLDED,
    )

    result = _serialize_received_payload(msg)

    assert '"sender_id":"center-1"' in result
    assert '"moter_mode":"FOLDED"' in result


def test_main_passes_coroutine_to_asyncio_run(monkeypatch) -> None:
    config = SimpleNamespace(
        logging=SimpleNamespace(level="INFO"),
        http=SimpleNamespace(host="0.0.0.0", port=8080),
    )
    fake_context = SimpleNamespace(term=lambda: None)
    fake_subscriber = SimpleNamespace(latest_json=None)
    captured = {}

    monkeypatch.setattr(target, "load_config", lambda _config_path=None: config)
    monkeypatch.setattr(target, "setup_logger", lambda _level_name: object())
    monkeypatch.setattr(target.zmq.asyncio, "Context", lambda: fake_context)
    monkeypatch.setattr(target, "build_sub_options", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(target, "DisplaySubscriber", lambda *_args, **_kwargs: fake_subscriber)

    def fake_asyncio_run(coro):
        captured["is_coroutine"] = asyncio.iscoroutine(coro)
        coro.close()

    monkeypatch.setattr(target.asyncio, "run", fake_asyncio_run)

    target.main()

    assert captured["is_coroutine"] is True
