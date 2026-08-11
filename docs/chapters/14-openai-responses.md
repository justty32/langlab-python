## 14. 最終實戰：OpenAI Responses API

完整可執行專案在 [`examples/openai_responses_app`](../../examples/openai_responses_app/)。它有三層：

```text
CLI / FastAPI endpoint       # transport boundary、輸入驗證、錯誤映射
        ↓
OpenAIResponsesClient        # 可 import 的 application API
        ↓
OpenAI Python SDK            # HTTP、SSE、response object
```

此章以 2026-08-11 的 OpenAI 官方文件核對，使用 Responses API。模型與介面會變；範例預設模型放在 `OPENAI_MODEL`，程式不把 secret 或 model ID 散落各處。

### 14.1 安裝與 secret

```powershell
cd examples\openai_responses_app
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[server]"
$env:OPENAI_API_KEY = "..."
$env:OPENAI_MODEL = "gpt-5.6"
```

SDK 會讀 `OPENAI_API_KEY`。不要把 key 寫進 Python、`.env` commit、URL query string 或 log。production 用平台 secret manager，並設 budget／rate limit。

### 14.2 最小文字 request

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-5.6",
    input="用三點解釋 Python context manager。",
)
print(response.output_text)
```

Responses API 的 output 是 typed item list，不永遠只有文字；`output_text` 是 SDK 提供的便利聚合屬性。

### 14.3 Stream：處理事件，不猜 chunk

```python
stream = client.responses.create(
    model="gpt-5.6",
    input="解釋 GIL，限 200 字。",
    stream=True,
)

for event in stream:
    if event.type == "response.output_text.delta":
        print(event.delta, end="", flush=True)
    elif event.type == "response.completed":
        print()
    elif event.type == "error":
        raise RuntimeError(str(event))
```

官方 stream 是 SSE，會有 `response.created`、`response.output_text.delta`、`response.completed`、`error` 等 semantic event。不要假設每個 network chunk 都是完整 UTF-8 字元或 JSON message；讓 SDK 做 framing。

若你的 server 再把它轉送給 browser，要處理 client disconnect 與 backpressure；不要無界 queue 累積 delta。

### 14.4 Image input（vision）

```python
response = client.responses.create(
    model="gpt-5.6",
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "這張圖有哪些值得注意的 UI 問題？"},
            {"type": "input_image", "image_url": image_url, "detail": "auto"},
        ],
    }],
)
```

`image_url` 可是完整 URL 或 base64 data URL。接受使用者 URL 代抓時要注意 SSRF、內容大小、MIME 與 timeout；更嚴謹的服務會先下載到受控儲存，再傳 file ID。

### 14.5 Image generation tool

```python
import base64
from pathlib import Path

response = client.responses.create(
    model="gpt-5.6",
    input="產生一張簡潔的 Python iterator 流程圖，深色背景。",
    tools=[{"type": "image_generation", "action": "generate"}],
)

for item in response.output:
    if item.type == "image_generation_call" and item.result:
        Path("iterator.png").write_bytes(base64.b64decode(item.result))
        break
else:
    raise RuntimeError("response did not contain an image")
```

Image input（看圖）與 image generation（產圖）是兩件事。模型／帳號是否可用某工具要以當下 model catalog 與你的 project 權限為準。

### 14.6 Function tool calling：模型提議，程式執行

工具宣告是 JSON Schema：

```python
TOOLS = [{
    "type": "function",
    "name": "get_runtime_info",
    "description": "Read allowlisted Python runtime information.",
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
}]
```

完整 loop：

```python
import json

conversation = [{"role": "user", "content": question}]
response = client.responses.create(model=model, input=conversation, tools=TOOLS)

conversation += response.output  # 保留 reasoning/tool call 等 typed items
called = False
for item in response.output:
    if item.type != "function_call":
        continue
    called = True
    if item.name != "get_runtime_info":
        result = {"error": "tool_not_allowed"}
    else:
        arguments = json.loads(item.arguments)
        result = dispatch_runtime_info(arguments)

    conversation.append({
        "type": "function_call_output",
        "call_id": item.call_id,
        "output": json.dumps(result),
    })

if called:
    response = client.responses.create(model=model, input=conversation, tools=TOOLS)

print(response.output_text)
```

Production tool loop 要加：最大回合數、tool allowlist、schema validation、per-tool timeout、權限與 side-effect approval、輸出大小限制、audit log。模型輸出的 argument 是不可信輸入，即使開了 strict schema 也要在 domain boundary 驗證。

### 14.7 Thinking：reasoning control，不是偷看私密 chain-of-thought

```python
response = client.responses.create(
    model="gpt-5.6",
    input="比較 thread、process、async，替這個 workload 做決策。",
    reasoning={"effort": "medium", "summary": "auto"},
)
print(response.output_text)
```

正確心智模型：

- `reasoning.effort` 控制模型在支援範圍內投入多少推理工作；高不保證永遠較好，會影響 latency／token。
- `summary` 若模型與帳號支援，要求可呈現的 reasoning summary。
- 不要假定 API 會提供完整內部 chain-of-thought；應用程式需要的是答案、可驗證證據、tool trace 與可呈現摘要。
- 多輪 continuation 可用 `previous_response_id`；若手動管理 history，保留 `response.output` 的 typed item，不要只留下純文字。

若 response 因 token 限制 incomplete，要檢查 status／incomplete details；可能只有 partial output，也可能 token 都花在 reasoning 而還沒有文字。

### 14.8 CLI 與 endpoint

範例 CLI：

```powershell
llm-demo text "用 C++ 類比解釋 decorator"
llm-demo stream "逐步解釋 Python import"
llm-demo vision "https://example.com/image.png" "描述圖片"
llm-demo image "畫一張 RAII 對照 context manager 的示意圖" --output out.png
llm-demo tool "我的 Python 版本是什麼？"
llm-demo reason "替 CPU-bound pipeline 選 concurrency 模型" --effort medium
```

啟動 HTTP server：

```powershell
uvicorn llm_endpoint.api:app --reload
```

Endpoint 示範 `POST /v1/chat` 與 `POST /v1/chat/stream`。這不是仿造 OpenAI 全部 wire protocol，而是把自己的 domain API 建在可 import client 上；這能避免 transport 與 SDK 細節滲透整個專案。

### 14.9 OpenAI error boundary

SDK error 至少分成：authentication/permission、rate limit、timeout/connection、bad request、server error。只對暫時性且安全重試的 request 做有界 retry。將外部錯誤轉成自己的 `LlmError`，但用 exception chaining 保留原 traceback；HTTP 層再映射成不洩漏 secret 的 status/body。

---
