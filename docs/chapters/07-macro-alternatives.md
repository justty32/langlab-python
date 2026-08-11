## 7. 「Macro」在 Python 裡怎麼想

Python 沒有一般用途的 preprocessor macro，也沒有 Rust 式 hygienic macro。這通常是好事：runtime object、function 與 protocol 已能直接表達多數意圖。

### 7.1 先辨認你原本用 macro 做什麼

| C/C++ macro 用途 | Python 首選 | Go／Lua 對照 |
|---|---|---|
| 常數 | module constant、`Enum` | `const`／module field |
| 小段重用運算 | function | function |
| logging／計時／retry | decorator 或 context manager | middleware／defer wrapper |
| 產生 boilerplate struct | `dataclass`、class factory | `go generate`／table factory |
| registration | decorator | `init` registration／table insert |
| compile-time flag | build config、環境變數、不同 module | build tags／config |
| template specialization | generic function、`singledispatch` | interface dispatch |
| DSL／source rewrite | code generation、AST/CST tool（最後手段） | `go generate`／parser |

### 7.2 Decorator：包 function，不改語法

```python
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def timed(function: Callable[P, R]) -> Callable[P, R]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            elapsed = perf_counter() - start
            print(f"{function.__qualname__}: {elapsed:.6f}s")
    return wrapper


@timed
def rebuild_index(path: str) -> int:
    ...
```

`@timed` 等價於 `rebuild_index = timed(rebuild_index)`。它是普通 function composition，可 debug、可測試、可保留型別。記得 `@wraps`。

帶參數 decorator 多一層 factory：

```python
def retry(attempts: int):
    def decorate(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            last_error = None
            for _ in range(attempts):
                try:
                    return function(*args, **kwargs)
                except TransientError as error:
                    last_error = error
            assert last_error is not None
            raise last_error
        return wrapper
    return decorate
```

正式 retry 還要考慮 exponential backoff、jitter、deadline、idempotency；不要用 decorator 無差別 retry 所有 exception。

### 7.3 Context manager：只包一段 scope

如果只想計時 function 的一小段，decorator 太大：

```python
from contextlib import contextmanager


@contextmanager
def span(name: str):
    start = perf_counter()
    try:
        yield
    finally:
        print(name, perf_counter() - start)


with span("parse headers"):
    parse_headers(data)
```

### 7.4 Registration decorator：取代 X-macro table

```python
handlers: dict[str, Callable[[dict], object]] = {}


def handles(name: str):
    def register(function):
        if name in handlers:
            raise ValueError(f"duplicate handler: {name}")
        handlers[name] = function
        return function
    return register


@handles("ping")
def handle_ping(message: dict) -> dict:
    return {"type": "pong"}
```

import 會執行 decorator，因此 registration 依賴 module 被 import。大型 plugin 系統可改用 package entry points，避免「神秘 import side effect」。

### 7.5 Class 生成：dataclass → `__init_subclass__` → metaclass

大多數 boilerplate 用 `@dataclass` 已足夠。若 subclass 宣告時要驗證：

```python
class Message:
    opcode: int

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not isinstance(getattr(cls, "opcode", None), int):
            raise TypeError(f"{cls.__name__} must define integer opcode")


class Ping(Message):
    opcode = 1
```

Metaclass 是「class object 的 class」。只有 framework 需要攔截 class creation 且 `__init_subclass__`／class decorator 都不夠時再用。它更接近 runtime class factory，不是 textual macro。

### 7.6 Descriptor（進階但常在 framework 看見）

`property`、method binding、ORM field 背後都可用 descriptor protocol：`__get__`、`__set__`、`__delete__`。

```python
class Positive:
    def __set_name__(self, owner, name):
        self.storage_name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.storage_name)

    def __set__(self, instance, value):
        if value <= 0:
            raise ValueError("must be positive")
        setattr(instance, self.storage_name, value)
```

### 7.7 AST、codegen、eval 的界線

- 若輸入是 data：解析 data，不要生成 Python source。
- 若是固定 boilerplate：寫 generator，在 build/dev 時產生並提交或驗證輸出。
- 若要修改 Python source 且保留格式：考慮 LibCST；內建 `ast` 不保留原格式。
- `eval`／`exec` 絕不能吃不可信輸入；它不是 macro 系統。
- import hook 能改寫載入行為，但會讓 debug、IDE、packaging 都變難；除 framework／研究工具外避免。
- `assert` 可被 `python -O` 移除，只能檢查內部 invariant，不能驗證外部輸入。

---

---
