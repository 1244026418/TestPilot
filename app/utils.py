import json
from typing import Any, Optional


def to_json_text(value: Any) -> str:
    if value is None:
        return "{}"
    return json.dumps(value, ensure_ascii=False)


def from_json_text(value: Optional[str], default: Any = None) -> Any:
    if not value:
        return {} if default is None else default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {} if default is None else default
