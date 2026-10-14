from __future__ import annotations

import base64
import json
import os
from collections.abc import Generator
from contextlib import closing
from dataclasses import dataclass
from typing import Any, Literal

from openai import OpenAI, OpenAIError

from .errors import LlmConfigurationError, LlmError, ToolLoopLimitError
from .tools import RUNTIME_INFO_TOOL, TOOL_HANDLERS

ReasoningEffort = Literal["none", "low", "medium", "high", "xhigh", "max"]


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    text: str
    summaries: tuple[str, ...]


class OpenAIResponsesClient:
    """Small domain wrapper around the OpenAI Responses API.

    Pass ``sdk=`` in tests to keep all tests offline.
    """

    def __init__(self, *, model: str | None = None, sdk: Any | None = None) -> None:
        self._model = model or os.environ.get("OPENAI_MODEL", "gpt-5.6")
        if sdk is not None:
            self._sdk = sdk
        else:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise LlmConfigurationError("OPENAI_API_KEY is not set")
            self._sdk = OpenAI(api_key=api_key)

    @property
    def model(self) -> str:
        return self._model

    def text(self, prompt: str) -> str:
        try:
            response = self._sdk.responses.create(model=self._model, input=prompt)
            return response.output_text
        except OpenAIError as error:
            raise LlmError("OpenAI text request failed") from error

    def stream_text(self, prompt: str) -> Generator[str, None, None]:
        try:
            with closing(
                self._sdk.responses.create(
                    model=self._model,
                    input=prompt,
                    stream=True,
                )
            ) as stream:
                for event in stream:
                    if event.type == "response.output_text.delta":
                        yield event.delta
                    elif event.type == "response.completed":
                        return
                    elif event.type in {"error", "response.failed", "response.incomplete"}:
                        raise LlmError(f"OpenAI stream ended with {event.type}")
                raise LlmError("OpenAI stream ended without response.completed")
        except OpenAIError as error:
            raise LlmError("OpenAI streaming request failed") from error

    def analyze_image(self, image_url: str, prompt: str) -> str:
        try:
            response = self._sdk.responses.create(
                model=self._model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": image_url,
                                "detail": "auto",
                            },
                        ],
                    }
                ],
            )
            return response.output_text
        except OpenAIError as error:
            raise LlmError("OpenAI image-input request failed") from error

    def generate_image(self, prompt: str) -> bytes:
        try:
            response = self._sdk.responses.create(
                model=self._model,
                input=prompt,
                tools=[{"type": "image_generation", "action": "generate"}],
            )
            for item in response.output:
                if item.type == "image_generation_call" and item.result:
                    return base64.b64decode(item.result, validate=True)
        except OpenAIError as error:
            raise LlmError("OpenAI image-generation request failed") from error
        except ValueError as error:
            raise LlmError("OpenAI returned invalid base64 image data") from error
        raise LlmError("OpenAI response did not contain a generated image")

    def ask_with_runtime_tool(self, prompt: str, *, max_turns: int = 4) -> str:
        input_items: list[Any] = [{"role": "user", "content": prompt}]
        try:
            for _ in range(max_turns):
                response = self._sdk.responses.create(
                    model=self._model,
                    input=input_items,
                    tools=[RUNTIME_INFO_TOOL],
                )
                input_items.extend(response.output)
                calls = [item for item in response.output if item.type == "function_call"]
                if not calls:
                    return response.output_text

                for call in calls:
                    handler = TOOL_HANDLERS.get(call.name)
                    if handler is None:
                        result: dict[str, object] = {"error": "tool_not_allowed"}
                    else:
                        try:
                            arguments = json.loads(call.arguments)
                            if not isinstance(arguments, dict):
                                raise ValueError("arguments must be a JSON object")
                            result = handler(arguments)
                        except (json.JSONDecodeError, ValueError, TypeError) as error:
                            result = {"error": "invalid_tool_arguments", "detail": str(error)}

                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(result, ensure_ascii=False),
                        }
                    )
        except OpenAIError as error:
            raise LlmError("OpenAI tool-calling request failed") from error
        raise ToolLoopLimitError(f"tool loop exceeded {max_turns} turns")

    def reason(self, prompt: str, *, effort: ReasoningEffort = "medium") -> ReasoningResult:
        try:
            response = self._sdk.responses.create(
                model=self._model,
                input=prompt,
                reasoning={"effort": effort, "summary": "auto"},
            )
        except OpenAIError as error:
            raise LlmError("OpenAI reasoning request failed") from error

        summaries: list[str] = []
        for item in response.output:
            if item.type != "reasoning":
                continue
            for summary in item.summary or []:
                if summary.text:
                    summaries.append(summary.text)
        return ReasoningResult(response.output_text, tuple(summaries))
