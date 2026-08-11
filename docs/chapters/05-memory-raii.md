## 5. 記憶體、ownership 與 RAII

### 5.1 Python 的 ownership 模型

語言層保證的是「物件在仍可達時存在」，不保證 CPython reference count 的精確釋放時刻是 portable semantics。CPython 主要用 reference counting，另有 cyclic GC；其他 implementation 可以不同。

```python
import gc
import sys

obj = []
alias = obj
print(sys.getrefcount(obj))  # 含呼叫本身的暫時 reference；只適合診斷
del alias                   # 刪除名稱綁定，不是 delete/free obj
gc.collect()                # 通常不該成為業務邏輯
```

最重要的區分：

- Python object memory：由 runtime 管。
- external resource（fd、socket、lock、C buffer、transaction）：由你的程式明確管理。

Python 官方 data model 也明確提醒：GC 不保證發生，因此外部資源應提供並使用 `close()` 等明確釋放方式。

這和 Lua 的 GC 心智模型相近：一般 object 交給 runtime，但 `__gc` finalizer 不適合當重要資源的正常釋放路徑。若你用 Lua 5.4，to-be-closed variable（`<close>`）在目的上比 GC 更接近 Python `with`。

### 5.2 `with` 是最接近 RAII 的主力

```python
from pathlib import Path

path = Path("data.bin")
with path.open("rb") as file:
    header = file.read(16)
# 正常 return 或 exception 都會 close
```

對 C++ 工程師可把 context manager 看成顯式 scope guard：

```python
class Transaction:
    def __enter__(self) -> "Transaction":
        self.begin()
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False  # 不吞 exception
```

更常用 `contextlib` 寫：

```python
from contextlib import contextmanager
from collections.abc import Iterator


@contextmanager
def locked(lock) -> Iterator[None]:
    lock.acquire()
    try:
        yield
    finally:
        lock.release()
```

Go `defer cleanup()` 能把 cleanup 掛在 function scope；Python `with` 能把 cleanup 限定在更小、可組合的 lexical scope。

### 5.3 `__del__` 不是 destructor 等價物

**避免用 `__del__` 管重要資源。** 它可能因 cycle、interpreter shutdown、resurrection 與例外處理而難以推理。優先順序：

1. `with` / async `async with`
2. 明確 `close()`，而且設計成 idempotent
3. `weakref.finalize` 當 safety net，不當正常控制流

### 5.4 Cycle、weakref、copy

```python
import copy
import weakref

shallow = copy.copy(nested)       # 外層新，內層仍共享
deep = copy.deepcopy(nested)      # 遞迴複製；可能昂貴或語意不合理

cache: weakref.WeakValueDictionary[str, Node] = weakref.WeakValueDictionary()
```

不要把 `deepcopy` 當 C++ value semantics 的萬用替代；socket、lock、file、foreign pointer 通常根本不該複製。設計明確的 `clone()` 更好。

### 5.5 記憶體與效能工具

| 問題 | 工具 |
|---|---|
| 哪段慢 | `timeit`（micro）、`cProfile`（whole program） |
| 哪裡配置記憶體 | `tracemalloc` |
| 單一物件淺層大小 | `sys.getsizeof` |
| 避免一次載入全部 | iterator／generator／streaming I/O |
| 大量數值 | NumPy 等 native contiguous array；不是 Python `list[int]` |

先 profile 再改。`__slots__`、object pool、手動 `gc.collect()` 都不是預設第一步。

---
