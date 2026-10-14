## 13. 測試、品質與專案工作流

### 13.1 標準庫測試先跑得起

```python
import unittest

from packet_lab import Packet, decode, encode


class CodecTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        value = Packet(kind="ping", payload=b"hello")
        self.assertEqual(decode(encode(value)), value)


if __name__ == "__main__":
    unittest.main()
```

```powershell
python -m unittest discover -s tests -v
```

團隊常選 pytest，因 assertion、fixture、parametrize 更精簡。選哪個不是重點；重要的是分層：

- pure unit test：快、無網路、無時間依賴。
- fake contract test：驗證你的 fake 與 real adapter 語意一致。
- integration test：真的碰 DB／HTTP／native library，數量少但必要。
- end-to-end：只守最重要流程。

Mock 在 boundary 用；不要 mock 每個 internal method，否則重構就碎。

### 13.2 一個可維護的最小 gate

```powershell
python -m compileall src tests
python -m unittest discover -s tests -v
ruff check .
ruff format --check .
pyright
python -m build
```

版本與 dependency 要有策略：library 通常宣告相容範圍，不鎖死 transitive dependency；application 則產生 lock file 保證部署可重現。不要把 `.venv` commit。

### 13.3 Public API

- 從 package `__init__.py` re-export 想長期支援的少量名稱。
- internal module/name 用前導 `_`。
- semantic versioning 只對你明確承諾的 API 有意義。
- import package 名稱避免與 stdlib（如 `json.py`, `typing.py`）撞名。
- 測試「安裝後 import」，不要只測 repo root。

---
