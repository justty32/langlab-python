# OpenAI Responses API 實戰

這個專案同時是可 import package、CLI 與 FastAPI HTTP endpoint。詳細解說在教材第 14 章。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[server]"
$env:OPENAI_API_KEY = "..."
$env:OPENAI_MODEL = "gpt-5.6"

llm-demo text "用 C++ 類比解釋 Python decorator"
llm-demo stream "解釋 Python import"
llm-demo tool "目前的 Python runtime 是什麼？"
llm-demo reason "thread、process、async 該怎麼選？"
uvicorn llm_endpoint.api:app --reload
```

離線測試不會呼叫 API：

```powershell
python -m unittest discover -s tests -v
```

`POST /v1/chat/stream` 回傳 `text/plain`。第一段文字送出前的上游失敗會回傳 502 JSON；傳送開始後的失敗會中止 HTTP body，呼叫端須處理串流讀取錯誤，不能只憑 HTTP 200 判斷答案完整。
