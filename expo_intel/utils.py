import json
from datetime import datetime, timezone
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_uuid() -> str:
    return str(uuid4())


def to_json(value) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=True)


def from_json(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))

