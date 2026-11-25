"""Web3 explorer helpers.

Bitcoin tx hashes are validated locally; live lookup is opt-in and is clearly
separated from the historical, anonymized Elliptic dataset. No keys are used.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import get_settings
from app.core.tx_validation import is_bitcoin_txid, normalize_tx_id
from app.schemas.settings import SettingsUpdateRequest


def build_explorer_url(tx_id: str, base_url: str | None = None) -> str:
    config = get_settings()
    base = (base_url or config.explorer_base_url).rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("Invalid explorer URL")
    return f"{base}/{normalize_tx_id(tx_id)}"


def live_lookup(tx_id: str) -> dict[str, Any]:
    """Query a public explorer only when explicitly enabled in configuration."""
    config = get_settings()
    normalized = normalize_tx_id(tx_id)
    result: dict[str, Any] = {
        "transaction_id": normalized,
        "enabled": config.enable_live_lookup,
        "is_live_blockchain_data": False,
        "found": False,
        "data": None,
        "message": None,
        "explorer_url": build_explorer_url(normalized),
    }
    if not config.enable_live_lookup:
        result["message"] = (
            "Live blockchain lookup is disabled. Enable it in Settings/environment "
            "and provide a real 64-character Bitcoin transaction hash."
        )
        return result
    if not is_bitcoin_txid(normalized):
        result["message"] = (
            "This identifier is not a Bitcoin transaction hash. Elliptic dataset IDs "
            "are historical and anonymized; they cannot be looked up on-chain."
        )
        return result

    api_base = config.explorer_api_base_url.rstrip("/")
    try:
        with httpx.Client(timeout=config.live_lookup_timeout) as client:
            response = client.get(f"{api_base}/tx/{normalized}")
        if response.status_code == 404:
            result["message"] = "Transaction not found by the configured public explorer."
            return result
        response.raise_for_status()
        payload = response.json()
        # Select only public transaction fields; never include credentials.
        status = payload.get("status") or {}
        result.update(
            {
                "found": True,
                "is_live_blockchain_data": True,
                "data": {
                    "txid": payload.get("txid"),
                    "confirmed": bool(status.get("confirmed")),
                    "block_height": status.get("block_height"),
                    "fee": payload.get("fee"),
                    "vin_count": len(payload.get("vin") or []),
                    "vout_count": len(payload.get("vout") or []),
                },
                "message": "Live explorer data. It is unrelated to the historical dataset.",
            }
        )
    except Exception as exc:  # pragma: no cover - network conditions vary
        result["message"] = f"Live lookup failed: {type(exc).__name__}"
    return result


def sanitize_settings_update(update: SettingsUpdateRequest) -> dict[str, Any]:
    """Accept only whitelisted preferences; never accept keys or secrets."""
    return update.model_dump(exclude_none=True)
