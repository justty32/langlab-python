## 15. 一張決策速查表

| 你正要做 | 先用 | 先不要用 |
|---|---|---|
| 管 file/socket/lock | `with` / `async with` | `__del__`、等 GC |
| 轉換 collection | comprehension／generator | 深層 `map(lambda...)` |
| 包 function 行為 | decorator | source macro／`exec` |
| 包局部 scope 行為 | context manager | 全域 monkey patch |
| 資料 class | dataclass | metaclass |
| interface | Protocol／duck typing | 為一個 method 建深繼承樹 |
| I/O concurrency | thread pool 或 asyncio | CPU-bound Python threads |
| CPU parallel | process pool | 假設一般 GIL 已消失 |
| 呼叫簡單 C ABI | ctypes/CFFI | 未宣告 restype 的 pointer call |
| HTTP | reusable client + timeout | 每次新 client、無 timeout |
| JSON | 明確 boundary conversion + validation | pickle 不可信輸入 |
| 專案 import | src layout + editable install | 改 `sys.path` |
| 錯誤 | specific exception + chaining | `except Exception: pass` |

---
