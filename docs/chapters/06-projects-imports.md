## 6. Module、package、import 與專案組織

### 6.1 三個容易混淆的名詞

| 名詞 | 例子 | 類比 |
|---|---|---|
| distribution package | PyPI 上的 `beautifulsoup4` | 可安裝 artifact／Go module |
| import package | `bs4/` | C++ library namespace 的一部分／Go package |
| module | `parser.py` | 一個可載入 translation unit，但執行期也是 object |

distribution 名稱可以有 `-`，import 名稱是 identifier，兩者不一定相同。

### 6.2 import 做了什麼

```python
import json                     # local name 是 json module
import pathlib as pl
from collections import deque  # local name 是 deque object
```

粗略流程：

1. 先查 `sys.modules` cache。
2. finder 從 built-in、目前程式、環境的 `site-packages` 等 import path 找 spec。
3. 建立 module object，**執行 module top-level code**。
4. 把結果綁到目前 scope 的名稱。

所以 import 不是 C++ `#include` 的文字貼上，也不是只有宣告的 header；它比較像載入並初始化一個 singleton module object。第一次 import 會執行，之後通常取 cache。

如果從 Lua 看，這很接近 `require` 查 `package.loaded`：第一次載入 module chunk，之後回傳 cache。差別是 Python module 本身有正式 namespace、spec、package hierarchy 與可擴充 finder/loader protocol。

### 6.3 `__init__.py`、absolute 與 relative import

```text
src/
└── packet_lab/
    ├── __init__.py
    ├── codec.py
    └── transport/
        ├── __init__.py
        └── http.py
```

在 `transport/http.py`：

```python
from packet_lab.codec import encode   # absolute；大型專案較清楚
from ..codec import decode            # explicit relative；package 內可用
```

不要寫模糊的 implicit relative import。也不要以修改 `sys.path` 解正常 packaging 問題。

`__init__.py` 讓目錄成為 regular package，並可定義穩定 public API：

```python
# packet_lab/__init__.py
from .codec import Packet, decode, encode

__all__ = ["Packet", "decode", "encode"]
```

`__all__` 主要影響 `from packet_lab import *` 與 API 意圖，不是 access control。Python 的 `_name` 是「internal」慣例，不是 private enforcement。

### 6.4 推薦的 src layout

```text
packet-lab/
├── pyproject.toml
├── README.md
├── src/
│   └── packet_lab/
│       ├── __init__.py
│       ├── __main__.py
│       ├── codec.py
│       └── errors.py
└── tests/
    └── test_codec.py
```

`src/` 隔開 repo root 與可 import 程式碼，可避免「只因目前工作目錄剛好在 path 上所以測試成功」的假象。Python Packaging User Guide 也以此為主要優點。

最小 `pyproject.toml`：

```toml
[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[project]
name = "packet-lab"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[project.scripts]
packet-lab = "packet_lab.cli:main"
```

開發安裝：

```powershell
python -m pip install -e .
python -c "import packet_lab; print(packet_lab.__file__)"
python -m packet_lab
packet-lab --help
```

`-e` 是 editable install：import 指到你的工作樹，改 `.py` 後通常不必重裝。正式驗證還應 build wheel 並在乾淨環境安裝：

```powershell
python -m pip install build
python -m build
python -m pip install dist\packet_lab-0.1.0-py3-none-any.whl
```

### 6.5 `__main__` 與執行入口

```python
# src/packet_lab/__main__.py
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

`python -m packet_lab` 會執行它。一般 module 也可寫 guard：

```python
def main() -> int:
    ...
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

把真正邏輯放在可 import function；guard 只接線。不要從 package 內用 `python src/packet_lab/foo.py` 執行，否則 relative import 與 package identity 容易壞掉；用 `python -m packet_lab.foo`。

### 6.6 Circular import 怎麼避免

常見成因是 module A 和 B 同時在 top-level 互 import。解法優先順序：

1. 把共享型別／協定抽到第三個低階 module。
2. 反轉依賴：傳 callable／Protocol，不直接 import concrete implementation。
3. type-only import 放在 `if TYPE_CHECKING:`。
4. 最後才考慮 function 內 lazy import。

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from packet_lab.transport import Transport
```

避免 import 時連網、啟 thread、讀大型設定。module top-level 以常數、class、function definition 與輕量 registry 為主。

本 repo 的完整可跑版本在 [`examples/package_demo`](../../examples/package_demo/)。

---
