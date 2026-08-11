## 1. 30 分鐘重新上手

### 1.1 執行方式

```powershell
python                 # REPL
python hello.py        # 把檔案當 script
python -m some.module  # 以 module 身分執行；專案內優先用這個
python -m pip --version
```

`python -m x` 類似「請目前這個 interpreter 從 import path 找到 `x` 再執行」。它能避免 Windows 上 `pip` 和 `python` 指向不同環境。

建立隔離環境：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

Linux／macOS 的啟用指令是 `source .venv/bin/activate`。也可以用較快的 `uv venv`、`uv pip install ...`，但先懂標準工具，才不會把套件管理器和 Python 本身混在一起。

### 1.2 一頁語法

```python
from dataclasses import dataclass

name = "Ada"                       # str
count = 3                          # int 不會 overflow 成負數
ratio = 0.5                        # float 通常是 IEEE-754 double
payload = b"\x00\x01"             # bytes，不是 str
missing = None                     # 類似 nil/null，但它是一個物件

items = ["c++", "go", "lua"]      # list，可變 sequence
point = (10, 20)                   # tuple，不可變 sequence
scores = {"c++": 10, "go": 9}     # dict，保持插入順序
tags = {"systems", "backend"}      # set

if name and count > 0:
    print(f"{name=}, {count=}")

for index, language in enumerate(items, start=1):
    print(index, language)

squares = [n * n for n in range(10) if n % 2 == 0]


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("b must not be zero")
    return a / b


@dataclass(frozen=True, slots=True)
class User:
    name: str
    languages: tuple[str, ...] = ()
```

縮排是語法。慣例為四個空白；沒有 `begin/end` 或 `{}`。

### 1.3 C++／Go／Lua 心智映射

| Python | 最接近的既有直覺 | 重要差異 |
|---|---|---|
| `list[T]` | `std::vector<T>`／Go slice／Lua array-like table | 裡面可混型別，型別提示不強制 |
| `dict[K, V]` | `unordered_map`／Go map／Lua table | 保持插入順序；key 必須 hashable |
| `tuple` | `std::tuple`／Go struct value | 不可變，可當 dict key（元素也需 hashable） |
| `dataclass` | aggregate struct | class 仍是 runtime object；預設可變 |
| `Protocol` | Go interface | structural typing，但主要由 type checker 檢查 |
| exception | C++ exception | Go 通常用 `(value, error)`；Python 以 exception 為主 |
| generator | lazy range／Lua coroutine | `yield` 暫停 frame，按需產生值 |
| context manager | RAII guard／Go `defer` | scope 由 `with` 明確標出 |

### 1.4 名稱綁定，不是 value slot

```python
a = [1, 2]
b = a
b.append(3)
assert a == [1, 2, 3]   # a、b 指向同一個 list

c = a.copy()            # shallow copy
c.append(4)
assert a == [1, 2, 3]

x = 10
y = x
y += 1
assert x == 10           # int 不可變；y 被重新綁到另一個 int
```

函式參數也是名稱綁定。常有人稱它「call by object sharing」：傳入的不是 C++ reference 語法，但 caller 與 callee 一開始指向同一個物件。

```python
def mutate(xs: list[int]) -> None:
    xs.append(99)       # 修改 caller 看得到的物件


def rebind(xs: list[int]) -> None:
    xs = [99]           # 只改 local name，caller 看不到
```

### 1.5 高頻語法糖

```python
first, *middle, last = [1, 2, 3, 4]
pair = (first, last)

for left, right in zip([1, 2], [10, 20], strict=True):
    print(left + right)

config = {"timeout": 10, "debug": False}
override = {"debug": True}
merged = config | override

status = "ready" if count > 0 else "empty"

if (size := len(payload)) > 0:     # := 賦值運算式；少量使用
    print(size)

match command:                     # structural pattern matching
    case {"op": "add", "x": x, "y": y}:
        result = x + y
    case {"op": "quit"}:
        result = None
    case _:
        raise ValueError("unknown command")
```

常用內建優先記：`len`、`range`、`enumerate`、`zip`、`sorted`、`min/max`、`sum`、`any/all`、`isinstance`。

`is` 比 identity，`==` 比 value：

```python
if value is None:       # 正確
    ...

if value == 0:          # value equality
    ...
```

不要靠小整數或字串 interning 猜 `is` 的結果。

### 1.6 Unicode 與 bytes

Python 3 的 `str` 是 Unicode text；`bytes` 是 0–255 的 byte sequence。FFI、檔案與 HTTP 邊界必須明確 encode/decode。

```python
text = "臺灣"
wire = text.encode("utf-8")
assert wire.decode("utf-8") == text

with open("config.json", "r", encoding="utf-8") as file:
    source = file.read()
```

規則：內部盡量用 `str`；在 I/O 邊界才轉 `bytes`。不要用 `str(bytes_value)` 期待 decode。

---
