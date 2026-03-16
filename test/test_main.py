from __future__ import annotations

from msg_handler.schemas import DisplayMessage, MotorState

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
