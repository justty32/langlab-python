import unittest

from fastapi.testclient import TestClient

from llm_endpoint.api import app, get_client
from llm_endpoint.errors import LlmConfigurationError


class FakeClient:
    def text(self, prompt: str) -> str:
        return f"answer: {prompt}"

    def stream_text(self, prompt: str):
        yield "answer: "
        yield prompt


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        app.dependency_overrides[get_client] = FakeClient
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        app.dependency_overrides.clear()

    def test_health_does_not_construct_openai_client(self) -> None:
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_chat_validates_and_returns_json(self) -> None:
        response = self.client.post("/v1/chat", json={"prompt": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"text": "answer: hello"})

    def test_chat_rejects_empty_prompt(self) -> None:
        response = self.client.post("/v1/chat", json={"prompt": ""})
        self.assertEqual(response.status_code, 422)

    def test_configuration_error_has_stable_public_response(self) -> None:
        def not_configured():
            raise LlmConfigurationError("secret detail")

        app.dependency_overrides[get_client] = not_configured
        try:
            response = self.client.post("/v1/chat", json={"prompt": "hello"})
        finally:
            app.dependency_overrides[get_client] = FakeClient
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"error": "llm_not_configured"})
        self.assertNotIn("secret detail", response.text)

    def test_stream_forwards_deltas(self) -> None:
        response = self.client.post("/v1/chat/stream", json={"prompt": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "answer: hello")


if __name__ == "__main__":
    unittest.main()
