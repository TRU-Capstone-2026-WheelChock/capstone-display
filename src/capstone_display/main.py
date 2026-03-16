from __future__ import annotations

import logging

import zmq

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


def _unwrap_topic_prefixed_payload(raw_message: str) -> str:
    if raw_message.lstrip().startswith("{"):
        return raw_message

    parts = raw_message.split(" ", 1)
    if len(parts) == 2 and parts[1].lstrip().startswith("{"):
        return parts[1]
    return raw_message


def run_display_subscriber(config: DisplayConfig, logger: logging.Logger) -> None:
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.setsockopt(zmq.LINGER, 0)
    socket.setsockopt_string(zmq.SUBSCRIBE, config.zmq.sub.topic)

    if config.zmq.sub.is_bind:
        socket.bind(config.zmq.sub.endpoint)
        mode = "bind"
    else:
        socket.connect(config.zmq.sub.endpoint)
        mode = "connect"

    logger.info(
        "display subscriber is UP endpoint=%s mode=%s topic=%r",
        config.zmq.sub.endpoint,
        mode,
        config.zmq.sub.topic,
    )

    try:
        while True:
            raw_message = socket.recv_string()
            print(_unwrap_topic_prefixed_payload(raw_message), flush=True)
    except KeyboardInterrupt:
        logger.info("display subscriber stopped")
    finally:
        socket.close()
        context.term()


def main(config_path: str | None = None) -> None:
    config = load_config(config_path)
    logger = setup_logger(config.logging.level)
    run_display_subscriber(config, logger)


if __name__ == "__main__":
    main()
