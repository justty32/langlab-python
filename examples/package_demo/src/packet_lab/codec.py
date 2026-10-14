from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass

from .errors import PacketFormatError


@dataclass(frozen=True, slots=True)
class Packet:
    kind: str
    payload: bytes


def encode(packet: Packet) -> bytes:
    """Encode a Packet into deterministic UTF-8 JSON bytes."""
    value = {
        "kind": packet.kind,
        "payload_base64": base64.b64encode(packet.payload).decode("ascii"),
    }
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def decode(wire: bytes) -> Packet:
    """Decode JSON bytes, translating boundary errors into PacketFormatError."""
    try:
        value = json.loads(wire)
        if not isinstance(value, dict):
            raise TypeError("top-level JSON value must be an object")

        kind = value["kind"]
        payload_text = value["payload_base64"]
        if not isinstance(kind, str) or not isinstance(payload_text, str):
            raise TypeError("kind and payload_base64 must be strings")

        payload = base64.b64decode(payload_text, validate=True)
        return Packet(kind=kind, payload=payload)
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        KeyError,
        TypeError,
        binascii.Error,
        ValueError,
    ) as error:
        raise PacketFormatError("invalid packet wire value") from error
