from app.transformer import transform_raw_to_enriched
from app.validator import validate_enriched_event


def test_transform_raw_to_enriched():
    raw_event = {
        "event_id": "evt_123",
        "source": "support_ticket",
        "timestamp": "2026-04-07T10:15:00Z",
        "tenant_id": "acme",
        "payload": {
            "ticket_id": "TICK_1001",
            "title": "Checkout timeout on mobile",
            "body": "Users report timeout after entering OTP during mobile checkout.",
            "severity": "high",
            "product": "payments",
            "customer_tier": "enterprise",
            "language": "en",
            "tags": ["checkout", "otp", "timeout"],
        },
    }

    enriched = transform_raw_to_enriched(
        raw_event=raw_event,
        chunk_size_words=80,
        chunk_overlap_words=20,
        schema_version="v1",
        processing_version="v1",
    )

    validate_enriched_event(enriched)

    assert enriched["ticket_id"] == "TICK_1001"
    assert enriched["tenant_id"] == "acme"
    assert len(enriched["chunks"]) >= 1