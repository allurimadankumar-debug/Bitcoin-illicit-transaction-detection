from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.tx_validation import normalize_tx_id
from app.schemas.graph import GraphResponse
from app.schemas.transaction import TransactionDetail, TransactionPage
from app.services.transaction_service import list_transactions, transaction_detail

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=TransactionPage)
def get_transactions(
    search: str | None = None,
    label: str = Query("all", pattern="^(all|licit|illicit|unknown|predicted_licit|predicted_illicit)$"),
    risk: str = Query("all", pattern="^(all|high-risk|elevated|low-risk|unrated)$"),
    sort_by: str = "time_step",
    order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1, le=100000),
    page_size: int = Query(12, ge=1, le=200),
    mask: bool | None = None,
) -> TransactionPage:
    return list_transactions(
        search=search,
        label=label,
        risk=risk,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size,
        mask=mask,
    )


@router.get("/{tx_id}", response_model=TransactionDetail)
def get_transaction(tx_id: str) -> TransactionDetail:
    detail, found = transaction_detail(normalize_tx_id(tx_id))
    if not found:
        raise HTTPException(status_code=404, detail="Transaction not found in the loaded dataset")
    return detail


@router.get("/{tx_id}/graph", response_model=GraphResponse)
def get_transaction_graph(
    tx_id: str,
    depth: int = Query(1, ge=1, le=3),
    limit: int = Query(30, ge=5, le=80),
) -> GraphResponse:
    from app.services.graph_service import graph_for_transaction

    response, found = graph_for_transaction(tx_id, depth=depth, limit=limit)
    if not found:
        raise HTTPException(status_code=404, detail="Transaction not found in the loaded dataset")
    return response


@router.get("/{tx_id}/explanation")
def get_transaction_explanation(tx_id: str) -> dict:
    from app.services.transaction_service import explanation_for

    return explanation_for(tx_id)
