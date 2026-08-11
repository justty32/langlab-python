## 10. JSON：序列化邊界要窄

```python
import json
from pathlib import Path

data = {"name": "Ada", "enabled": True, "roles": ["admin"]}
wire = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
decoded = json.loads(wire)

try:
    config = json.loads(Path("config.json").read_text(encoding="utf-8"))
except (OSError, json.JSONDecodeError) as error:
    raise ConfigError("cannot load config.json") from error
```

JSON 只有 object、array、string、number、boolean、null。`datetime`、`Decimal`、`bytes`、set、任意 class 都沒有標準表示法；請在 boundary 明確轉換：

```python
from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class Event:
    id: str
    created_at: datetime

    def to_json_value(self) -> dict[str, object]:
        return {
            "id": self.id,
            "created_at": self.created_at.astimezone(timezone.utc).isoformat(),
        }
```

反序列化不是「轉回原 class」；它只產生 dict/list 等基本物件。外部 JSON 必須做 schema validation。小專案可手寫 validator；HTTP API 常用 Pydantic／msgspec 等 library。

注意：

- JSON key 永遠是 string；`{1: "x"}` round-trip 後 key 會變 `"1"`。
- 大整數雖然 Python 能保存，JavaScript consumer 可能失去精度。
- `NaN`／`Infinity` 不是嚴格 JSON；對外可設 `allow_nan=False`。
- 不可信輸入要限制 body size 與 nesting；解析成功不代表語意合法。
- 不用 pickle 接收不可信資料；unpickle 可以執行任意程式碼。

---
