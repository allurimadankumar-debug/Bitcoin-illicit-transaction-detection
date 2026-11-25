"""Logging configuration with privacy-aware transaction ID masking."""
from __future__ import annotations

import logging
import re
from typing import Any

from .config import settings

_BTC_TXID_RE = re.compile(r"\b([a-fA-F0-9]{8})[a-fA-F0-9]{56}\b")
_DEMO_ID_RE = re.compile(r"\b(DEMO)(\d{4})(\d{4})\b")


def mask_tx_id(tx_id: str) -> str:
    """Mask an identifier for logs and privacy-aware dashboard tables."""
    if not tx_id:
        return ""
    if len(tx_id) <= 8:
        return f"{tx_id[:2]}***{tx_id[-2:]}"
    return f"{tx_id[:6]}…{tx_id[-4:]}"


def redact_message(message: str) -> str:
    message = _BTC_TXID_RE.sub(lambda m: f"{m.group(1)}…[REDACTED]", message)
    message = _DEMO_ID_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}…{m.group(3)}", message)
    return message


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact_message(str(record.msg))
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: redact_message(v) if isinstance(v, str) else v
                        for k, v in record.args.items()
                    }
                else:
                    record.args = tuple(
                        redact_message(v) if isinstance(v, str) else v for v in record.args
                    )
        except Exception:  # pragma: no cover - logging must never break the app
            pass
        return True


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("bitcoin_detection")
    if logger.handlers:
        return logger
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    handler.addFilter(RedactingFilter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()


def log_event(event: str, **fields: Any) -> None:
    rendered = " ".join(f"{k}={v}" for k, v in fields.items())
    logger.info("%s | %s", event, redact_message(rendered))
