from dataclasses import dataclass
from typing import Any


ROUTE_VERSION = "v1"


@dataclass(frozen=True)
class RoutedEvent:
    event_type: str
    router_label: str
    record_id: str
    source_payload_id: str
    chunk_id_prefix: str
    title: str
    body: str
    severity: str
    product: str
    customer_tier: str
    language: str
    summary: str
    entities: list[str]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _short_message(message: str, max_chars: int = 80) -> str:
    normalized = " ".join(message.split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 1].rstrip() + "..."


def route_raw_event(raw_event: dict[str, Any]) -> RoutedEvent:
    source = raw_event["source"]
    payload = raw_event["payload"]

    if source == "support_ticket":
        ticket_id = payload["ticket_id"]
        return RoutedEvent(
            event_type="support_ticket",
            router_label="support_ticket:v1",
            record_id=ticket_id,
            source_payload_id=ticket_id,
            chunk_id_prefix=ticket_id,
            title=payload["title"],
            body=payload["body"],
            severity=payload["severity"],
            product=payload["product"],
            customer_tier=payload["customer_tier"],
            language=payload.get("language", "en"),
            summary=payload["title"],
            entities=list(payload.get("tags", [])),
        )

    if source == "customer_chat_message":
        conversation_id = payload["conversation_id"]
        message_id = payload["message_id"]
        sender = payload["sender"]
        sentiment = payload.get("sentiment", "neutral")
        message = payload["message"]

        return RoutedEvent(
            event_type="customer_chat_message",
            router_label="customer_chat_message:v1",
            record_id=conversation_id,
            source_payload_id=message_id,
            chunk_id_prefix=f"{conversation_id}_{message_id}",
            title=f"{sender.capitalize()} chat message in {conversation_id}",
            body=message,
            severity=payload["severity"],
            product=payload["product"],
            customer_tier=payload["customer_tier"],
            language=payload.get("language", "en"),
            summary=f"{sender.capitalize()} chat: {_short_message(message)}",
            entities=_dedupe([sender, sentiment, *payload.get("tags", [])]),
        )

    raise ValueError(f"Unsupported raw event source: {source}")
