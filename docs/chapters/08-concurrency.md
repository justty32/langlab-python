## 8. 多執行緒、process 與 async

先區分兩個詞：

- **Concurrency**：多個工作在進度上重疊。
- **Parallelism**：同一時刻真的在多核心執行。

### 8.1 選擇表

| 工作形狀 | 首選 | 原因／代價 |
|---|---|---|
| 少量 blocking I/O library | `ThreadPoolExecutor` | 最容易接既有同步 API |
| 大量 socket、需要 cancellation/backpressure | `asyncio` | 單 thread 管很多 task；整條 call chain 要 async-aware |
| pure Python CPU-bound | `ProcessPoolExecutor` | 繞過一般 CPython GIL；需 pickle 與 IPC |
| C extension 會釋放 GIL 的 CPU 工作 | thread 可能有效 | 以該 library 文件與 benchmark 為準 |
| Python 3.14 隔離型平行工作 | `InterpreterPoolExecutor`（進階） | 真多核但 interpreter 隔離、資料需序列化 |
| free-threaded CPython 3.13+ | thread 可真平行（進階部署選項） | 非預設 build；extension 相容性要逐一確認 |

不要把 `async` 當「更快的 thread」。它是 cooperative scheduling：task 必須在 `await` 主動讓出控制。

Lua coroutine 也是 cooperative，但本身通常不附帶 I/O event loop、timeout 與 task lifecycle。Python `asyncio` 把 coroutine 接到 event loop；兩者都不會因為 `yield/await` 就自動得到多核心平行。

### 8.2 GIL 的現代說法

一般 CPython build 中，Global Interpreter Lock 讓同一 interpreter 同時只有一個 thread 執行 Python bytecode。因此 CPU-bound pure Python thread 通常不能線性吃滿多核心；但等待檔案、socket，或 native code 釋放 GIL 時，其他 thread 仍可工作。

Python 3.13 起另有 free-threaded build，可停用 GIL；到 3.14 它仍是需特別安裝／建置的模式，第三方 C extension 可能不支援，甚至在 import 時重新啟用 GIL。不要把「3.13 已沒有 GIL」寫進架構假設。

GIL **不是你的資料 race lock**。即使某些 operation 在某個 CPython 版本看似 atomic，多步 invariant 仍要同步，而且 free-threaded build 會使偷懶更快出錯。

### 8.3 Thread：共享記憶體，明確 ownership

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import urlopen


def fetch_size(url: str) -> tuple[str, int]:
    with urlopen(url, timeout=5) as response:
        return url, len(response.read())


urls = ["https://example.com", "https://example.org"]
with ThreadPoolExecutor(max_workers=8, thread_name_prefix="fetch") as pool:
    futures = [pool.submit(fetch_size, url) for url in urls]
    for future in as_completed(futures):
        try:
            print(future.result())
        except OSError as error:
            print("fetch failed:", error)
```

共享狀態用 lock：

```python
from threading import Lock


class Counter:
    def __init__(self) -> None:
        self._value = 0
        self._lock = Lock()

    def increment(self) -> int:
        with self._lock:
            self._value += 1
            return self._value
```

更好的預設是 message passing：`queue.Queue` 在 thread 間傳工作，讓 mutable state 只屬於一個 worker。這接近 Go「不要藉由共享記憶體通訊」的方向，但 Python queue 是 blocking thread primitive。

同步工具：

- `Lock`：普通 mutex；用 `with lock:`。
- `RLock`：同 thread 可重入；常暗示 call graph 太互相糾纏。
- `Event`：一次狀態通知，適合 shutdown flag。
- `Condition`：在 lock 保護的 predicate 上等待；一定用 `while not predicate:`。
- `Semaphore`：限制同時進入數量。
- `Queue`：有同步的 producer/consumer channel。

避免 worker 在同一個已滿 pool 內等待另一個 future，容易 deadlock。`ThreadPoolExecutor` 也不適合永不結束的 daemon service loop。

### 8.4 Process：序列化邊界

```python
from concurrent.futures import ProcessPoolExecutor


def cpu_heavy(number: int) -> int:
    return sum(i * i for i in range(number))


def main() -> None:
    with ProcessPoolExecutor() as pool:
        print(list(pool.map(cpu_heavy, [1_000_000] * 4)))


if __name__ == "__main__":
    main()
```

Windows 與 spawn 模式尤其需要 `if __name__ == "__main__"`。傳入 function、argument、return value 必須可 pickle；lambda、REPL local function、open socket／lock 通常不行。把 process boundary 當小型 RPC：資料要小而明確。

### 8.5 asyncio：接近 goroutine 的地方與不像的地方

```python
import asyncio


async def fetch_one(client, url: str) -> str:
    async with asyncio.timeout(5):
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def main() -> None:
    async with make_async_client() as client:
        async with asyncio.TaskGroup() as group:
            tasks = [group.create_task(fetch_one(client, url)) for url in URLS]
        results = [task.result() for task in tasks]


asyncio.run(main())
```

與 Go 的關鍵差異：Python coroutine 必須由 event loop 驅動；直接呼叫 `fetch_one(...)` 只得到 coroutine object，還沒執行。blocking function 若直接放進 event loop 會卡住全部 task：

```python
result = await asyncio.to_thread(blocking_library_call, argument)
```

Cancellation 是正常控制流：cleanup 放 `finally` 或 `async with`，捕到 `asyncio.CancelledError` 後通常 cleanup 再 re-raise。所有外部等待都設 timeout；timeout 是 correctness，不只是效能參數。

### 8.6 Race 與 shutdown checklist

- 先定義誰擁有 mutable state，再選 lock／queue。
- lock 保護 invariant，不只是單一 container operation。
- 不在持 lock 時做未知 callback、I/O 或等待 future。
- 設 deadline／timeout；區分「不再接受新工作」和「中止既有工作」。
- executor、session、server 都用 context manager 關閉。
- concurrency test 重複跑並加壓；一次綠不代表沒有 race。

---
