from app.retrieval import QueryEngine


def test_query_engine_ingests_chunk_records(tmp_path):
    engine = QueryEngine(
        vector_store_dir=str(tmp_path / "vector_store"),
        embedding_model_name="hashing-local-v1",
    )

    manifest = engine.ingest_chunk_records(
        [
            {
                "chunk_id": "CONV_1001_MSG_2001_chunk_0",
                "ticket_id": "CONV_1001",
                "text": "Customer chat message about mobile checkout OTP failure.",
                "metadata": {
                    "tenant_id": "acme",
                    "severity": "high",
                    "product": "checkout",
                    "timestamp": "2026-05-28T22:15:00Z",
                    "customer_tier": "enterprise",
                    "source": "customer_chat_message",
                    "event_type": "customer_chat_message",
                    "record_id": "CONV_1001",
                    "source_payload_id": "MSG_2001",
                    "router_label": "customer_chat_message:v1",
                },
            }
        ]
    )

    assert manifest["record_count"] == 1
    assert engine.manifest["record_count"] == 1
    assert engine.records[0]["metadata"]["event_type"] == "customer_chat_message"
