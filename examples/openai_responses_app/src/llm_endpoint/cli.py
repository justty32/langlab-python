from __future__ import annotations

import argparse
from pathlib import Path

from .client import OpenAIResponsesClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="llm-demo")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for command in ("text", "stream", "tool"):
        child = subparsers.add_parser(command)
        child.add_argument("prompt")

    vision = subparsers.add_parser("vision")
    vision.add_argument("image_url")
    vision.add_argument("prompt")

    image = subparsers.add_parser("image")
    image.add_argument("prompt")
    image.add_argument("--output", type=Path, default=Path("generated.png"))

    reason = subparsers.add_parser("reason")
    reason.add_argument("prompt")
    reason.add_argument(
        "--effort",
        choices=("none", "low", "medium", "high", "xhigh", "max"),
        default="medium",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    client = OpenAIResponsesClient()

    if arguments.command == "text":
        print(client.text(arguments.prompt))
    elif arguments.command == "stream":
        for delta in client.stream_text(arguments.prompt):
            print(delta, end="", flush=True)
        print()
    elif arguments.command == "vision":
        print(client.analyze_image(arguments.image_url, arguments.prompt))
    elif arguments.command == "image":
        arguments.output.write_bytes(client.generate_image(arguments.prompt))
        print(arguments.output.resolve())
    elif arguments.command == "tool":
        print(client.ask_with_runtime_tool(arguments.prompt))
    elif arguments.command == "reason":
        result = client.reason(arguments.prompt, effort=arguments.effort)
        if result.summaries:
            print("Reasoning summary:")
            print("\n".join(result.summaries))
            print("\nAnswer:")
        print(result.text)
    else:
        raise AssertionError(f"unhandled command: {arguments.command}")
    return 0
