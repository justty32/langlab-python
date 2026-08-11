## 3. Class、dataclass、Protocol 與 typing

### 3.1 先用 dataclass 表達資料

```python
from dataclasses import dataclass, field


@dataclass(slots=True)
class Job:
    id: str
    tags: list[str] = field(default_factory=list)

    def add_tag(self, tag: str) -> None:
        self.tags.append(tag)
```

絕對不要寫 `tags: list[str] = []`：那會讓所有 instance 共用同一個 list。`default_factory` 類似每次建構時呼叫 factory。

`slots=True` 可減少 per-instance 儲存並禁止任意新增 attribute；它不是 C++ 固定 layout 保證。`frozen=True` 產生阻擋一般賦值的 API，不等於 C++ transitive const。

### 3.2 Python data model（dunder protocol）

```python
class BytesView:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, index: int) -> int:
        return self._data[index]

    def __repr__(self) -> str:
        return f"BytesView({self._data!r})"
```

Python 的操作常是 protocol：`len(x)` 找 `x.__len__()`，`with x` 找 `__enter__/__exit__`，`for` 找 iterable protocol。這比「所有東西都由 magic 反射」更精準。

### 3.3 Composition 優先；需要 interface 時用 Protocol

```python
from typing import Protocol


class Writer(Protocol):
    def write(self, data: bytes) -> int: ...


def write_packet(target: Writer, payload: bytes) -> None:
    written = target.write(payload)
    if written != len(payload):
        raise OSError("short write")
```

這最接近 Go interface：class 不必顯式繼承 `Writer`，只要 shape 相符，static type checker 就接受。runtime 預設仍是 duck typing。

### 3.4 現代 typing 最小集合

```python
from collections.abc import Callable, Iterable, Mapping, Sequence
from typing import Literal, TypedDict, TypeVar

T = TypeVar("T")


def first(values: Sequence[T]) -> T | None:
    return values[0] if values else None


class ConfigDict(TypedDict):
    endpoint: str
    mode: Literal["fast", "safe"]
    timeout: float
```

注意：

- annotation 通常不做 runtime validation，也不等於 C++ compile-time type。
- public API 加型別最划算；一次把所有 local variable 標滿通常只是噪音。
- container 參數優先接受抽象介面如 `Iterable[T]`／`Mapping[K, V]`；若真的需要 indexing 才收 `Sequence[T]`。
- `Any` 會停止型別檢查傳播；它不是 `object`。

建議選一個 checker：Pyright（許多 IDE 直接支援）或 mypy。formatter/linter 可用 Ruff；它們是工具選擇，不是 Python 語言要求。

---
