from datetime import datetime, timezone
from types import SimpleNamespace

from app.ingestion import build_chunk_records, transform_raw_to_enriched
from app.models import CustomerChatMessagePayload, RawEvent, RawEventPayload


def test_transform_raw_to_enriched_and_build_chunk_records():
    settings = SimpleNamespace(
        chunk_size_words=80,
        chunk_overlap_words=20,
        schema_version="v1",
        processing_version="v1",
    )

    event = RawEvent(
        event_id="evt_test_001",
        source="support_ticket",
        timestamp=datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc),
        tenant_id="acme",
        payload=RawEventPayload(
            ticket_id="TICK_9001",
            title="Checkout timeout on mobile",
            body="Users report timeout after entering OTP during mobile checkout.",
            severity="high",
            product="checkout",
            customer_tier="enterprise",
            language="en",
            tags=["checkout", "otp", "timeout"],
        ),
    )

    enriched = transform_raw_to_enriched(
        raw_event=event,
        settings=settings,
    )
    records = build_chunk_records(enriched)

    assert enriched["ticket_id"] == "TICK_9001"
    assert enriched["tenant_id"] == "acme"
    assert enriched["metadata"]["summary"] == "Checkout timeout on mobile"
    assert len(enriched["chunks"]) >= 1
    assert len(records) >= 1
    assert records[0]["ticket_id"] == "TICK_9001"
    assert records[0]["metadata"]["tenant_id"] == "acme"
    assert records[0]["metadata"]["event_type"] == "support_ticket"


def test_transform_customer_chat_message_to_enriched_and_build_chunk_records():
    settings = SimpleNamespace(
        chunk_size_words=80,
        chunk_overlap_words=20,
        schema_version="v1",
        processing_version="v1",
    )

    event = RawEvent(
        event_id="evt_chat_001",
        source="customer_chat_message",
        timestamp=datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc),
        tenant_id="acme",
        payload=CustomerChatMessagePayload(
            conversation_id="CONV_1001",
            message_id="MSG_2001",
            sender="customer",
            message="Mobile checkout keeps failing after OTP.",
            severity="high",
            product="checkout",
            customer_tier="enterprise",
            sentiment="negative",
            language="en",
            tags=["checkout", "mobile", "otp"],
        ),
    )

    enriched = transform_raw_to_enriched(
        raw_event=event,
        settings=settings,
    )
    records = build_chunk_records(enriched)

    assert enriched["ticket_id"] == "CONV_1001"
    assert enriched["metadata"]["event_type"] == "customer_chat_message"
    assert enriched["metadata"]["source_payload_id"] == "MSG_2001"
    assert len(records) == 1
    assert records[0]["ticket_id"] == "CONV_1001"
    assert records[0]["metadata"]["event_type"] == "customer_chat_message"
