from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone


def configure_logging() -> None:
    logger = logging.getLogger("trustledger")
    if getattr(logger, "_trustledger_configured", False):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.handlers = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False

    request_logger = logging.getLogger("trustledger.request")
    request_logger.handlers = [handler]
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = False

    setattr(logger, "_trustledger_configured", True)
    setattr(request_logger, "_trustledger_configured", True)


def emit_structured_log(
    logger_name: str,
    *,
    message: str,
    level: int = logging.INFO,
    **fields,
) -> None:
    logger = logging.getLogger(logger_name)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": logging.getLevelName(level).lower(),
        "logger": logger_name,
        "message": message,
    }
    payload.update(fields)
    logger.log(level, json.dumps(payload, separators=(",", ":"), default=str))
