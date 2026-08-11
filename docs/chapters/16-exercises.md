## 16. 下一步練習

按這個順序做，每題約 20–40 分鐘：

1. 在 `package_demo` 新增 `Packet.timestamp`，更新 JSON encode/decode 與 test。
2. 寫 `@retry`，只 retry 自訂 `TransientError`，加入 exponential backoff 的 injectable sleep。
3. 用 thread pool 並行抓五個 URL，再改成 async HTTPX；比較 error/cancellation code，而不只 benchmark。
4. 寫一個 C `malloc/free` library，用 context manager 包 owned pointer，故意漏掉 `restype` 觀察為何危險（只在 disposable process）。
5. 為 OpenAI tool 新增一個純函式工具；寫 fake client 測 tool loop，不花 API token。
6. 把 OpenAI streaming endpoint 接到簡單 browser UI，正確處理 disconnect。

---
