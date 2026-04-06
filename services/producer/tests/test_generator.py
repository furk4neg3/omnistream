from app.generator import generate_event
from app.validator import validate_event


def test_generate_event_matches_schema():
    event = generate_event("acme")
    validate_event(event)

    assert event["source"] == "support_ticket"
    assert event["tenant_id"] == "acme"
    assert "payload" in event
    assert "ticket_id" in event["payload"]