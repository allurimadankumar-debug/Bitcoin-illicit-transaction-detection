from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.tx_validation import validate_tx_id
from app.services.explorer_service import build_explorer_url, live_lookup

router = APIRouter(prefix="/blockchain", tags=["web3"])


@router.get("/explorer-url")
def explorer_url(
    tx_id: str = Query(..., min_length=1),
    base_url: str | None = None,
) -> dict[str, str]:
    try:
        normalized = validate_tx_id(tx_id)
        return {"transaction_id": normalized, "url": build_explorer_url(normalized, base_url)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/lookup/{tx_id}")
def lookup(tx_id: str) -> dict:
    try:
        normalized = validate_tx_id(tx_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return live_lookup(normalized)
