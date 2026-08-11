from __future__ import annotations

import base64
import json
import unittest
from types import SimpleNamespace

from llm_endpoint import LlmConfigurationError, OpenAIResponsesClient


def item(item_type: str, **values):
    return SimpleNamespace(type=item_type, **values)


def response(text: str, output=()):
    return SimpleNamespace(output_text=text, output=list(output))


class FakeResponses:
    def __init__(self, results):
        self._results = iter(results)
        self.calls = []

    def create(self, **arguments):
        self.calls.append(arguments)
        return next(self._results)


class FakeSdk:
    def __init__(self, results):
        self.responses = FakeResponses(results)


class OpenAIResponsesClientTests(unittest.TestCase):
    def test_missing_api_key_is_a_stable_configuration_error(self) -> None:
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(LlmConfigurationError):
                OpenAIResponsesClient()

    def test_text_uses_configured_model(self) -> None:
        sdk = FakeSdk([response("hello")])
        client = OpenAIResponsesClient(model="test-model", sdk=sdk)

        self.assertEqual(client.text("hi"), "hello")
        self.assertEqual(sdk.responses.calls[0]["model"], "test-model")

    def test_stream_yields_only_text_deltas(self) -> None:
        events = [
            item("response.created"),
            item("response.output_text.delta", delta="你"),
            item("response.output_text.delta", delta="好"),
            item("response.completed"),
        ]
        client = OpenAIResponsesClient(sdk=FakeSdk([events]))
        self.assertEqual("".join(client.stream_text("hi")), "你好")

    def test_generate_image_decodes_base64(self) -> None:
        encoded = base64.b64encode(b"fake png").decode("ascii")
        sdk = FakeSdk([response("", [item("image_generation_call", result=encoded)])])
        client = OpenAIResponsesClient(sdk=sdk)
        self.assertEqual(client.generate_image("draw"), b"fake png")

    def test_tool_loop_returns_final_text_and_sends_output(self) -> None:
        call = item(
            "function_call",
            name="get_runtime_info",
            arguments='{"field":"python_version"}',
            call_id="call_1",
        )
        sdk = FakeSdk([response("", [call]), response("Python is available.")])
        client = OpenAIResponsesClient(sdk=sdk)

        self.assertEqual(
            client.ask_with_runtime_tool("version?"),
            "Python is available.",
        )
        second_input = sdk.responses.calls[1]["input"]
        tool_output = second_input[-1]
        self.assertEqual(tool_output["type"], "function_call_output")
        self.assertEqual(tool_output["call_id"], "call_1")
        self.assertIn("python_version", json.loads(tool_output["output"])["field"])

    def test_reason_collects_presentable_summaries(self) -> None:
        reasoning = item(
            "reasoning",
            summary=[SimpleNamespace(text="Compared the concurrency models.")],
        )
        sdk = FakeSdk([response("Use processes.", [reasoning])])
        client = OpenAIResponsesClient(sdk=sdk)

        result = client.reason("choose")
        self.assertEqual(result.text, "Use processes.")
        self.assertEqual(result.summaries, ("Compared the concurrency models.",))


if __name__ == "__main__":
    unittest.main()
