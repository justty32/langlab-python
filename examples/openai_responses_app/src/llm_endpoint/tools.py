from __future__ import annotations

import platform
import sys
from collections.abc import Callable

RUNTIME_INFO_TOOL = {
    "type": "function",
    "name": "get_runtime_info",
    "description": "Read one allowlisted fact about this Python runtime.",
    "parameters": {
        "type": "object",
        "properties": {
            "field": {
                "type": "string",
                "enum": ["python_version", "platform"],
            }
        },
        "required": ["field"],
        "additionalProperties": False,
    },
    "strict": True,
}


def get_runtime_info(arguments: dict[str, object]) -> dict[str, str]:
    field = arguments.get("field")
    if field == "python_version":
        return {"field": field, "value": sys.version.split()[0]}
    if field == "platform":
        return {"field": field, "value": platform.platform()}
    raise ValueError("field is not allowlisted")


TOOL_HANDLERS: dict[str, Callable[[dict[str, object]], dict[str, str]]] = {
    "get_runtime_info": get_runtime_info,
}
