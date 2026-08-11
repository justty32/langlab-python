## 12. C FFI：ABI、ownership、GIL

先選層級：

| 方法 | 適合 | 代價 |
|---|---|---|
| `ctypes`（stdlib） | 快速呼叫既有簡單 C ABI | 宣告錯誤可能 crash；binding 手寫 |
| CFFI | 中型 C API、想從 header-like declaration 產生介面 | 多一個 dependency/build step |
| CPython C API | 極致整合、需直接操作 Python object | 最複雜，綁 CPython API/ABI |
| pybind11／nanobind | C++ library | template binding 方便，但 build/wheel 與 ownership 仍要懂 |

若你熟 LuaJIT FFI，`ctypes`／CFFI 的整體感覺會很接近：宣告 C ABI 後直接呼叫 shared library；同樣地，錯誤 signature、失效 pointer 與 allocator 不配對都可能直接讓 process crash。

### 12.1 ctypes 最小範例

假設 C library：

```c
// packet.h
#include <stddef.h>
#include <stdint.h>

uint32_t checksum(const uint8_t *data, size_t size);
void *packet_alloc(size_t size);
void packet_free(void *pointer);
```

Python binding：

```python
from ctypes import CDLL, POINTER, c_size_t, c_uint8, c_uint32, c_void_p
from pathlib import Path

library = CDLL(str(Path("packet.dll").resolve()))  # Linux: libpacket.so

library.checksum.argtypes = [POINTER(c_uint8), c_size_t]
library.checksum.restype = c_uint32

library.packet_alloc.argtypes = [c_size_t]
library.packet_alloc.restype = c_void_p
library.packet_free.argtypes = [c_void_p]
library.packet_free.restype = None


def checksum(data: bytes) -> int:
    buffer_type = c_uint8 * len(data)
    buffer = buffer_type.from_buffer_copy(data)
    return int(library.checksum(buffer, len(data)))
```

一定宣告 `argtypes`／`restype`。若忘了 pointer restype，ctypes 可能預設當 C `int`，在 64-bit 截斷 address，結果不是漂亮 exception，而是 process crash。

### 12.2 把 foreign ownership 包成 context manager

```python
class PacketBuffer:
    def __init__(self, size: int) -> None:
        pointer = library.packet_alloc(size)
        if not pointer:
            raise MemoryError(f"packet_alloc({size}) failed")
        self._pointer = c_void_p(pointer)

    @property
    def pointer(self) -> c_void_p:
        if self._pointer is None:
            raise RuntimeError("buffer already closed")
        return self._pointer

    def close(self) -> None:
        if self._pointer is not None:
            library.packet_free(self._pointer)
            self._pointer = None

    def __enter__(self) -> "PacketBuffer":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()
```

這裡的核心不是 Python GC，而是清楚寫出 C allocator 與 deallocator 必須配對。API review 時逐一回答：

1. pointer 是 borrowed 還是 owned？
2. 誰 allocate／誰 free？用同一個 CRT／allocator 嗎？
3. buffer 有多長？是否 NUL terminated？
4. callee 會保留 pointer 超過 call 嗎？
5. callback 可能從哪個 thread 進來？
6. error 用 return code、`errno`，還是 out parameter？

`c_char_p` 適合 NUL-terminated string，不適合內含 `\0` 的 arbitrary buffer。需要 zero-copy 時看 `memoryview`／buffer protocol，但 lifetime 必須比 view 長。

### 12.3 Callback lifetime

```python
from ctypes import CFUNCTYPE, c_int

CALLBACK = CFUNCTYPE(c_int, c_int)


@CALLBACK
def on_value(value: int) -> int:
    try:
        return handle(value)
    except Exception:
        logger.exception("callback failed")
        return -1

callback_keepalive = on_value  # C 還會呼叫時，Python 必須保留 reference
```

不要讓 exception 穿過 C ABI。轉成約定好的 error code，並確保 callback object 不被 GC。C 建立的 thread 呼回 CPython 時還涉及 thread state／GIL，使用的 FFI library 會處理一部分，但必須按其文件設計。

### 12.4 Native code 與 GIL

長時間 blocking／CPU native function 是否釋放 GIL，取決於 binding。CPython extension 常以 `Py_BEGIN_ALLOW_THREADS`／`Py_END_ALLOW_THREADS` 包住不碰 Python object 的區段；pybind11 有 `gil_scoped_release`。釋放後：

- 不可讀寫 Python object／呼叫 Python C API（除明確 thread-safe API）。
- C/C++ 共享狀態要自己同步；GIL 不再替你碰巧保護 global cache。
- free-threaded build 還要求 extension 宣告支援，並檢查 borrowed reference 與 container access。

### 12.5 Shipping

含 native code 的 wheel 通常綁 OS、CPU、Python ABI。CI 至少要為支援平台 build/test wheel；Linux 常用 manylinux，Windows 要對齊 runtime，macOS 要處理 deployment target／universal2。若 ABI 可保持純 C 且 library 可獨立配送，CFFI/ctypes 有時比 CPython extension 更穩定。

---
