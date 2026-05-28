from app.router import route_raw_event
from app.transformer import transform_raw_to_enriched
from app.validator import validate_enriched_event, validate_raw_event


def test_routes_and_enriches_customer_chat_message():
    raw_event = {
        "event_id": "evt_chat_001",
        "source": "customer_chat_message",
        "timestamp": "2026-04-12T12:00:00Z",
        "tenant_id": "acme",
        "payload": {
            "conversation_id": "CONV_1001",
            "message_id": "MSG_2001",
            "sender": "customer",
            "message": "Mobile checkout keeps failing after OTP.",
            "severity": "high",
            "product": "checkout",
            "customer_tier": "enterprise",
            "sentiment": "negative",
            "language": "en",
            "tags": ["checkout", "mobile", "otp"],
        },
    }

    validate_raw_event(raw_event)
    route = route_raw_event(raw_event)
    enriched = transform_raw_to_enriched(
        raw_event=raw_event,
        chunk_size_words=80,
        chunk_overlap_words=20,
        schema_version="v1",
        processing_version="v1",
    )
    validate_enriched_event(enriched)

    assert route.event_type == "customer_chat_message"
    assert enriched["ticket_id"] == "CONV_1001"
    assert enriched["metadata"]["event_type"] == "customer_chat_message"
    assert enriched["metadata"]["record_id"] == "CONV_1001"
    assert enriched["metadata"]["source_payload_id"] == "MSG_2001"
    assert enriched["chunks"][0]["chunk_id"].startswith("CONV_1001_MSG_2001")
