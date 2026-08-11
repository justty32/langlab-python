from __future__ import annotations

import argparse

from .codec import Packet, encode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="packet-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="encode a text packet")
    encode_parser.add_argument("kind")
    encode_parser.add_argument("payload")
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    if arguments.command == "encode":
        packet = Packet(arguments.kind, arguments.payload.encode("utf-8"))
        print(encode(packet).decode("utf-8"))
        return 0
    raise AssertionError(f"unhandled command: {arguments.command}")
