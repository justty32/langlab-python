## 11. HTTP client 與 server

### 11.1 標準庫或第三方？

- `urllib.request`：零依賴、簡單一次性 request。
- `httpx`：現代 sync + async API、connection pooling、streaming；本教材範例首選。
- `requests`：成熟且常見，只支援同步介面。

### 11.2 一個有 production 基本線的 HTTPX client

```python
import httpx


class ApiClient:
    def __init__(self, base_url: str, token: str) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=httpx.Timeout(10.0, connect=3.0),
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

    def __enter__(self) -> "ApiClient":
        return self

    def __exit__(self, *exc_info) -> None:
        self._client.close()

    def get_user(self, user_id: str) -> dict[str, object]:
        response = self._client.get(f"/users/{user_id}")
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise ValueError("expected JSON object")
        return value
```

重用 `Client` 才有 connection pool；不要每個 request 都新建。所有 request 設 timeout。處理錯誤時至少區分：

- transport error／timeout：request 未必到達；可能適合 retry。
- HTTP 4xx：通常是 caller 問題，不盲目 retry。
- HTTP 429／5xx：依 `Retry-After`、idempotency 與 deadline 有界 retry。
- JSON/schema error：peer 回了你不理解的內容；記錄安全的診斷資訊。

Exponential backoff 要加 jitter，且 retry 次數之外還要有總 deadline。POST 是否可 retry 取決於 idempotency key 與 server contract。

### 11.3 Streaming

```python
with httpx.stream("GET", url, timeout=30.0) as response:
    response.raise_for_status()
    for chunk in response.iter_bytes():
        consume(chunk)
```

Streaming 的意義是 bounded memory 與 lower time-to-first-byte，不代表自動處理 message framing。SSE、NDJSON、chunked binary 都需各自 parser。

### 11.4 FastAPI endpoint（用到再學）

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()


class AddRequest(BaseModel):
    left: int = Field(ge=0)
    right: int = Field(ge=0)


@app.post("/add")
def add(request: AddRequest) -> dict[str, int]:
    try:
        return {"result": checked_add(request.left, request.right)}
    except OverflowError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
```

Endpoint 是 error boundary：domain exception 在這裡映射到穩定 HTTP status/body；不要把 traceback 回傳給 client。secret 放環境變數或 secret manager，不進 source／log。接受 URL 參數並由 server 代抓時要防 SSRF。

---
