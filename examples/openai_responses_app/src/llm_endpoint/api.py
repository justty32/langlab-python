from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.background import BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from .client import OpenAIResponsesClient
from .errors import LlmConfigurationError, LlmError

app = FastAPI(title="LLM endpoint tutorial", version="0.1.0")


class ChatRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class ChatResponse(BaseModel):
    text: str


@lru_cache(maxsize=1)
def get_client() -> OpenAIResponsesClient:
    # Construct lazily so importing this module does not require an API key.
    return OpenAIResponsesClient()


ClientDependency = Annotated[OpenAIResponsesClient, Depends(get_client)]


@app.exception_handler(LlmError)
async def handle_llm_error(request: Request, error: LlmError) -> JSONResponse:
    # Log the chained traceback in a real service; do not expose it to callers.
    if isinstance(error, LlmConfigurationError):
        return JSONResponse(status_code=503, content={"error": "llm_not_configured"})
    return JSONResponse(status_code=502, content={"error": "upstream_llm_failed"})


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest, client: ClientDependency) -> ChatResponse:
    return ChatResponse(text=client.text(request.prompt))


@app.post("/v1/chat/stream")
def chat_stream(
    request: ChatRequest, client: ClientDependency, background_tasks: BackgroundTasks
) -> StreamingResponse:
    stream = client.stream_text(request.prompt)
    # Run the upstream request before StreamingResponse commits HTTP 200.
    first = next(stream, None)

    def body():
        try:
            if first is not None:
                yield first
            yield from stream
        finally:
            stream.close()

    background_tasks.add_task(stream.close)
    return StreamingResponse(
        body(),
        media_type="text/plain; charset=utf-8",
        headers={"X-Content-Type-Options": "nosniff"},
        background=background_tasks,
    )
