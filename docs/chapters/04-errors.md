## 4. 錯誤處理：exception、expected 與 error boundary

### 4.1 與 C++／Go 的對照

| 情況 | Python 慣例 |
|---|---|
| 無法開檔、JSON 壞掉、HTTP timeout | raise exception |
| 查不到是正常分支 | 回傳 `None`、sentinel，或提供 `get/require` 兩種 API |
| programmer bug／invariant 破壞 | raise，不要轉成普通回傳值 |
| 跨 process／HTTP boundary | 捕捉後轉成穩定 error code／response |

Python 標準生態更接近 C++ exception，不常處處回傳 Go `(value, error)`。如果需要 `expected` 風格，可定義明確的 result type，但不要同一層 API 一半回傳 error、一半 raise。

Lua 的 `pcall/xpcall` 把「是否成功＋結果」變成普通回傳值；Python 通常讓 exception 沿 call stack 傳播，只在能恢復或跨 boundary 時捕捉。不要把每次 Python 呼叫都包成 `pcall` 式大範圍 `try`。

### 4.2 完整 try 結構

```python
try:
    document = load_document(path)
except FileNotFoundError:
    document = default_document()
except PermissionError as error:
    raise ConfigError(f"cannot read {path}") from error
else:
    validate(document)   # 只在 try 沒拋例外時執行
finally:
    metrics.increment("load.attempt")
```

把 `try` 範圍縮小，避免誤抓到同型但來自別行的 exception。

```python
try:
    value = mapping[key]
except KeyError:
    value = compute_default(key)
```

這是 EAFP（先做、失敗再處理）。若先檢查 `key in mapping` 再取值，在並行或外部狀態上可能產生 TOCTOU。

### 4.3 自訂例外與鏈結

```python
class AppError(Exception):
    """Application-level failure."""


class InvalidConfigError(AppError):
    pass


def parse_port(text: str) -> int:
    try:
        port = int(text)
    except ValueError as error:
        raise InvalidConfigError(f"invalid port: {text!r}") from error
    if not 1 <= port <= 65535:
        raise InvalidConfigError(f"port out of range: {port}")
    return port
```

`raise ... from error` 保留因果鏈，類似 Go `%w`，但 traceback 更完整。bare `raise` 在 `except` 內重新拋原例外。

避免：

```python
try:
    run()
except Exception:
    pass  # 吞掉錯誤、traceback 與 cancellation 訊號
```

若在 top-level boundary 必須抓廣泛錯誤，要 log traceback、回報失敗，且不要假裝成功。不要捕捉 `BaseException`，否則連 `KeyboardInterrupt`、`SystemExit` 也被吃掉。

### 4.4 `ExceptionGroup` 與 `except*`（用到再學）

多個 concurrent task 可能同時失敗，Python 3.11+ 用 `ExceptionGroup` 保存它們：

```python
try:
    async with asyncio.TaskGroup() as group:
        group.create_task(fetch("a"))
        group.create_task(fetch("b"))
except* TimeoutError as group:
    for error in group.exceptions:
        log_timeout(error)
```

---
