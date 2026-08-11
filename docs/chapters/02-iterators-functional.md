## 2. 容器、iterator、generator 與 functional programming

### 2.1 Iterable 與 iterator

Python 的 `for` 不要求 array。它對物件呼叫 `iter(x)`，再反覆 `next(iterator)`，直到 `StopIteration`。

```python
numbers = iter([10, 20, 30])
assert next(numbers) == 10


class Countdown:
    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self) -> "Countdown":
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value
```

日常不必手寫 iterator class，generator 更簡單：

```python
def countdown(start: int):
    while start > 0:
        yield start
        start -= 1


total = sum(countdown(1_000_000))  # lazy，不先建百萬元素 list
```

`yield from other_iterable` 類似把子 generator 的輸出向外轉送。

Lua 的 iterator 常由 closure 保存狀態，coroutine 也能 `yield`；Python 則把這兩件事收斂成 iterable／iterator protocol。Python generator 每次 `yield` 暫停 frame，但它不是可任意排程的 thread。

### 2.2 Comprehension 優先於 map/filter

```python
names = [user.name for user in users if user.enabled]
lookup = {user.id: user for user in users}
unique_domains = {user.email.rpartition("@")[2] for user in users}
```

Python 也有 `map`、`filter` 與 `functools.reduce`，但簡單轉換通常 comprehension 更可讀：

```python
from functools import reduce
from operator import mul

product = reduce(mul, [2, 3, 4], 1)
```

`map` 適合已有具名函式，`reduce` 適合真的 associative fold；不要為了「functional」把清楚的 loop 壓成一行。

### 2.3 Function 是 first-class object

```python
from collections.abc import Callable
from functools import partial

Transform = Callable[[str], str]


def apply_pipeline(value: str, steps: list[Transform]) -> str:
    for step in steps:
        value = step(value)
    return value


def prefix(marker: str, value: str) -> str:
    return marker + value


warn = partial(prefix, "WARN: ")
result = apply_pipeline(" disk full ", [str.strip, warn])
```

Closure 捕獲的是名稱，不是自動 snapshot：

```python
funcs = [lambda i=i: i * 2 for i in range(3)]  # i=i 固定當次值
assert [f() for f in funcs] == [0, 2, 4]
```

### 2.4 `itertools` 與 `functools`

```python
from functools import cache, lru_cache, singledispatch
from itertools import batched, chain, pairwise

for batch in batched(records, 100):  # 3.12+
    send(batch)

edges = list(pairwise(["a", "b", "c"]))
flat = chain.from_iterable(groups)


@lru_cache(maxsize=256)
def parse_schema(name: str) -> Schema:
    ...
```

cache key 必須 hashable；cached function 不應依賴未包含在參數裡的可變 global state。

### 2.5 FP 的實用邊界

- Pure core / imperative shell 很適合 Python：核心轉換用 pure function，I/O 集中在邊界。
- `tuple`、`frozenset`、`frozen=True` dataclass 能表達 immutable intent，但 Python 不是深層 const 語言。
- recursion depth 不高，沒有保證 tail-call optimization；大量資料優先 loop／generator。
- `lambda` 只能是一個 expression；複雜邏輯請命名成 `def`。

---
