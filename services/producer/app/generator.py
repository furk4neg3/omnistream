import random
import uuid
from datetime import datetime, timezone


SEVERITIES = ["low", "medium", "high", "critical"]
PRODUCTS = ["payments", "search", "auth", "checkout", "mobile"]
CUSTOMER_TIERS = ["free", "pro", "enterprise"]
EVENT_TYPES = ["support_ticket", "customer_chat_message"]

TITLE_BODY_LIBRARY = [
    (
        "Checkout timeout on mobile",
        "Users report timeout after entering OTP during mobile checkout.",
        ["checkout", "mobile", "otp", "timeout"],
    ),
    (
        "Duplicate charge after retry",
        "Customer was charged twice after retrying payment on a slow network.",
        ["payments", "duplicate-charge", "retry"],
    ),
    (
        "Search results missing recent items",
        "Newly added products are not appearing in search results for several hours.",
        ["search", "indexing", "freshness"],
    ),
    (
        "Login link expired immediately",
        "Magic login link appears expired as soon as users click it.",
        ["auth", "login", "magic-link"],
    ),
    (
        "Push notifications not delivered",
        "Mobile users are not receiving important notifications after the latest release.",
        ["mobile", "notifications", "release"],
    ),
    (
        "Enterprise dashboard returns 500",
        "Several enterprise users reported HTTP 500 errors on analytics dashboard pages.",
        ["dashboard", "500", "enterprise"],
    ),
]

CHAT_MESSAGE_LIBRARY = [
    (
        "I cannot complete checkout on iOS. The OTP screen keeps spinning and then fails.",
        ["checkout", "mobile", "otp"],
        "negative",
    ),
    (
        "The magic login link says it is expired even though I just requested it.",
        ["auth", "magic-link", "login"],
        "negative",
    ),
    (
        "An agent suggested retrying payment, but I was charged twice after the second attempt.",
        ["payments", "duplicate-charge", "retry"],
        "negative",
    ),
    (
        "Search still does not show the products I uploaded this morning.",
        ["search", "freshness", "indexing"],
        "neutral",
    ),
    (
        "Thanks, push notifications seem to work again after reinstalling the app.",
        ["mobile", "notifications"],
        "positive",
    ),
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_ticket_id() -> str:
    return f"TICK_{random.randint(1000, 9999)}"


def make_conversation_id() -> str:
    return f"CONV_{random.randint(1000, 9999)}"


def make_message_id() -> str:
    return f"MSG_{random.randint(1000, 9999)}"


def generate_support_ticket_event(tenant_id: str) -> dict:
    title, body, tags = random.choice(TITLE_BODY_LIBRARY)
    severity = random.choices(
        population=SEVERITIES,
        weights=[35, 30, 25, 10],
        k=1,
    )[0]

    product = random.choice(PRODUCTS)
    customer_tier = random.choices(
        population=CUSTOMER_TIERS,
        weights=[50, 30, 20],
        k=1,
    )[0]

    return {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "source": "support_ticket",
        "timestamp": utc_now_iso(),
        "tenant_id": tenant_id,
        "payload": {
            "ticket_id": make_ticket_id(),
            "title": title,
            "body": body,
            "severity": severity,
            "product": product,
            "customer_tier": customer_tier,
            "language": "en",
            "tags": tags,
        },
    }


def generate_customer_chat_message_event(tenant_id: str) -> dict:
    message, tags, sentiment = random.choice(CHAT_MESSAGE_LIBRARY)
    severity = random.choices(
        population=SEVERITIES,
        weights=[40, 30, 22, 8],
        k=1,
    )[0]

    return {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "source": "customer_chat_message",
        "timestamp": utc_now_iso(),
        "tenant_id": tenant_id,
        "payload": {
            "conversation_id": make_conversation_id(),
            "message_id": make_message_id(),
            "sender": random.choices(
                population=["customer", "agent", "system"],
                weights=[75, 20, 5],
                k=1,
            )[0],
            "message": message,
            "severity": severity,
            "product": random.choice(PRODUCTS),
            "customer_tier": random.choices(
                population=CUSTOMER_TIERS,
                weights=[50, 30, 20],
                k=1,
            )[0],
            "sentiment": sentiment,
            "language": "en",
            "tags": tags,
        },
    }


def generate_event(tenant_id: str, event_types: list[str] | None = None) -> dict:
    enabled_event_types = event_types or ["support_ticket"]
    event_type = random.choice(enabled_event_types)

    if event_type == "support_ticket":
        return generate_support_ticket_event(tenant_id)

    if event_type == "customer_chat_message":
        return generate_customer_chat_message_event(tenant_id)

    raise ValueError(f"Unsupported EVENT_TYPES entry: {event_type}")
