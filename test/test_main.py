from __future__ import annotations

from capstone_display.main import _serialize_received_payload


def test_serialize_received_payload_for_dict() -> None:
    raw = {"sender_id": "center-1"}

    assert _serialize_received_payload(raw) == '{"sender_id": "center-1"}'


class _DummyMessage:
    def model_dump(self, *, mode: str = "python") -> dict[str, str]:
        assert mode == "json"
        return {"sender_id": "center-1"}


def test_serialize_received_payload_for_model_like_object() -> None:
    raw = _DummyMessage()

    assert _serialize_received_payload(raw) == '{"sender_id": "center-1"}'
