from __future__ import annotations

from capstone_display.main import _unwrap_topic_prefixed_payload


def test_unwrap_topic_prefixed_payload_with_raw_json() -> None:
    raw = '{"sender_id":"center-1"}'

    assert _unwrap_topic_prefixed_payload(raw) == raw


def test_unwrap_topic_prefixed_payload_with_topic_prefix() -> None:
    raw = 'display {"sender_id":"center-1"}'

    assert _unwrap_topic_prefixed_payload(raw) == '{"sender_id":"center-1"}'
