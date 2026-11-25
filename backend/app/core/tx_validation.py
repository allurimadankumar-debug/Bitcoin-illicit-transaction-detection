"""Bitcoin transaction ID validation helpers.

Historical Elliptic identifiers are NOT Bitcoin hashes; they are kept as
opaque strings. Separate validation is used only for live explorer lookups.
"""
from __future__ import annotations

import re

BTC_TXID_RE = re.compile(r"^[0-9a-fA-F]{64}$")
DEMO_ID_RE = re.compile(r"^DEMO\d{8}$")


def is_bitcoin_txid(value: str) -> bool:
    """Return True for a canonical 64-character hexadecimal transaction hash."""
    return bool(BTC_TXID_RE.fullmatch(value.strip()))


def is_demo_id(value: str) -> bool:
    return bool(DEMO_ID_RE.fullmatch(value.strip().upper()))


def normalize_tx_id(value: str) -> str:
    value = value.strip()
    if is_demo_id(value):
        return value.upper()
    return value.lower() if is_bitcoin_txid(value) else value


def validate_tx_id(value: str, *, allow_dataset_ids: bool = True) -> str:
    """Validate a user-supplied identifier.

    Dataset identifiers are opaque and accepted. Anything that is not a
    dataset identifier must be a valid Bitcoin transaction hash.
    """
    value = normalize_tx_id(value)
    if not value:
        raise ValueError("Transaction ID cannot be empty")
    if is_bitcoin_txid(value):
        return value
    if allow_dataset_ids and (is_demo_id(value) or value.isdigit()):
        return value
    raise ValueError(
        "Invalid transaction ID. Use a dataset identifier or a 64-character "
        "hexadecimal Bitcoin transaction hash."
    )
