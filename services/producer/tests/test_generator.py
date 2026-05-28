from app.generator import (
    generate_customer_chat_message_event,
    generate_event,
    generate_support_ticket_event,
)
from app.validator import validate_event


def test_generate_support_ticket_event_matches_schema():
    event = generate_support_ticket_event("acme")
    validate_event(event)

    assert event["source"] == "support_ticket"
    assert event["tenant_id"] == "acme"
    assert "payload" in event
    assert "ticket_id" in event["payload"]


def test_generate_customer_chat_message_event_matches_schema():
    event = generate_customer_chat_message_event("acme")
    validate_event(event)

    assert event["source"] == "customer_chat_message"
    assert event["tenant_id"] == "acme"
    assert "conversation_id" in event["payload"]
    assert "message_id" in event["payload"]


def test_generate_event_respects_enabled_event_types():
    event = generate_event("acme", event_types=["customer_chat_message"])
    validate_event(event)

    assert event["source"] == "customer_chat_message"
