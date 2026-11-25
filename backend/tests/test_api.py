from __future__ import annotations


def test_health(client) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["dataset_source"] == "demo"
    assert body["is_synthetic"] is True


def test_dashboard_summary(client) -> None:
    body = client.get("/api/dashboard/summary").json()
    assert body["total_transactions"] >= 60
    assert body["illicit_transactions"] > 0
    assert body["licit_transactions"] > 0
    assert body["unknown_transactions"] > 0
    assert "synthetic" in (body["note"] or "").lower()


def test_transaction_list_pagination_and_filters(client) -> None:
    first = client.get("/api/transactions?page=1&page_size=5&sort_by=time_step&order=asc").json()
    assert first["page"] == 1
    assert len(first["items"]) == 5
    assert first["total"] >= 60
    illicit = client.get("/api/transactions?label=illicit&page_size=3").json()
    assert all(item["ground_truth_label"] == "illicit" for item in illicit["items"])
    masked = client.get("/api/transactions?mask=true&page_size=3").json()
    assert all("…" in item["transaction_id"] for item in masked["items"])


def test_transaction_detail_and_graph(client) -> None:
    first_id = client.get("/api/transactions?page_size=1").json()["items"][0]["transaction_id"]
    # Use an unmasked ID via the API list response without the mask flag.
    unmasked = client.get("/api/transactions?page_size=1&mask=false").json()["items"][0]["transaction_id"]
    detail = client.get(f"/api/transactions/{unmasked}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["time_step"] >= 1
    assert body["is_synthetic"] is True
    graph = client.get(f"/api/transactions/{unmasked}/graph?depth=1&limit=20")
    assert graph.status_code == 200
    assert graph.json()["center"] == unmasked
    explanation = client.get(f"/api/transactions/{unmasked}/explanation")
    assert explanation.status_code == 200


def test_prediction_endpoints(client) -> None:
    tx_id = client.get("/api/transactions?page_size=1&mask=false").json()["items"][0]["transaction_id"]
    single = client.post("/api/predict", json={"transaction_id": tx_id})
    assert single.status_code == 200
    body = single.json()
    assert body["predicted_class"] in {"licit", "illicit"}
    assert 0.0 <= (body["risk_score"] or 0.0) <= 1.0
    assert body["warning"] == "Model prediction is not proof of criminal activity"
    assert body["is_synthetic_data"] is True

    batch = client.post("/api/predict/batch", json={"transaction_ids": [tx_id, "DEMO99999999"]})
    assert batch.status_code == 200
    result = batch.json()
    assert result["succeeded"] == 1
    assert result["failed"] == 1

    uploaded = client.post(
        "/api/predict/batch/upload",
        files={"file": ("batch.csv", f"tx_id\n{tx_id}\n".encode(), "text/csv")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["succeeded"] == 1


def test_prediction_validation_and_not_found(client) -> None:
    invalid = client.post("/api/predict", json={"transaction_id": "not-an-id!!"})
    assert invalid.status_code == 422
    missing = client.post("/api/predict", json={"transaction_id": "DEMO99999999"})
    assert missing.status_code == 404


def test_analytics_and_settings(client) -> None:
    metrics = client.get("/api/models/metrics").json()
    assert metrics["available"] is True
    assert metrics["best_model"]
    temporal = client.get("/api/analytics/temporal").json()
    assert len(temporal["points"]) > 0
    risk = client.get("/api/analytics/risk-distribution?bins=5").json()
    assert len(risk["buckets"]) == 5
    settings = client.get("/api/settings").json()
    assert settings["keys_required"] == []
    updated = client.post("/api/settings", json={"table_page_size": 20}).json()
    assert updated["overrides"]["table_page_size"] == 20
    client.post("/api/settings", json={"table_page_size": 12})


def test_web3_lookup_is_clearly_separated(client) -> None:
    lookup = client.get("/api/blockchain/lookup/DEMO00000001").json()
    assert lookup["enabled"] is False
    assert lookup["is_live_blockchain_data"] is False
    url = client.get("/api/blockchain/explorer-url?tx_id=DEMO00000001").json()
    assert url["url"].startswith("https://")


def test_openapi_documentation(client) -> None:
    schema = client.get("/openapi.json").json()
    assert "/api/predict" in schema["paths"]
    assert "/api/dashboard/summary" in schema["paths"]
