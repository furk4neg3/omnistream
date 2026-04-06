import random
import uuid
from datetime import datetime, timezone


SEVERITIES = ["low", "medium", "high", "critical"]
PRODUCTS = ["payments", "search", "auth", "checkout", "mobile"]
CUSTOMER_TIERS = ["free", "pro", "enterprise"]

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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_ticket_id() -> str:
    return f"TICK_{random.randint(1000, 9999)}"


def generate_event(tenant_id: str) -> dict:
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