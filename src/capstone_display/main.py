from __future__ import annotations

import asyncio
import json
import logging

import msg_handler
import zmq.asyncio
from msg_handler.schemas import DisplayMessage

from capstone_display.config import DisplayConfig, load_config


def setup_logger(level_name: str) -> logging.Logger:
    level = getattr(logging, level_name.upper(), None)
    if not isinstance(level, int):
        raise SystemExit(f"invalid logging level: {level_name}")

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    return logging.getLogger("capstone_display")


def build_sub_options(
    config: DisplayConfig,
    *,
    context: zmq.asyncio.Context,
) -> msg_handler.ZmqSubOptions:
    return msg_handler.ZmqSubOptions(
        endpoint=config.zmq.sub.endpoint,
        topics=config.zmq.sub.topics,
        is_bind=config.zmq.sub.is_bind,
        expected_type="auto",
        context=context,
    )


def _serialize_received_payload(raw_payload: object) -> str:
    if hasattr(raw_payload, "model_dump"):
        model_dump = getattr(raw_payload, "model_dump")
        return json.dumps(model_dump(mode="json"), ensure_ascii=False)
    if isinstance(raw_payload, (dict, list)):
        return json.dumps(raw_payload, ensure_ascii=False, default=str)
    if isinstance(raw_payload, str):
        return raw_payload
    return str(raw_payload)


class DisplaySubscriber:
    def __init__(
        self,
        sub_opt: msg_handler.ZmqSubOptions,
        logger: logging.Logger | None = None,
    ) -> None:
        self.sub_opt = sub_opt
        self.logger = logger or logging.getLogger(__name__)

    async def run(self) -> None:
        async with msg_handler.get_async_subscriber(self.sub_opt) as subscriber:
            self.logger.info(
                "display subscriber is UP endpoint=%s mode=%s topics=%s",
                self.sub_opt.endpoint,
                "bind" if self.sub_opt.is_bind else "connect",
                self.sub_opt.topics,
            )
            async for raw_payload in subscriber:
                if not isinstance(raw_payload, DisplayMessage):
                    self.logger.error(
                        "unexpected message type: expected DisplayMessage, got %s",
                        type(raw_payload).__name__,
                    )
                    continue
                print(_serialize_received_payload(raw_payload), flush=True)


def main(config_path: str | None = None) -> None:
    config = load_config(config_path)
    logger = setup_logger(config.logging.level)
    context = zmq.asyncio.Context()
    subscriber = DisplaySubscriber(build_sub_options(config, context=context), logger)
    try:
        asyncio.run(subscriber.run())
    finally:
        context.term()


if __name__ == "__main__":
    main()
