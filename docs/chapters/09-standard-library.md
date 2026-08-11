## 9. 標準庫與日常工程工具

### 9.1 先知道去哪裡找

| 需求 | 先看 |
|---|---|
| 路徑／檔案 | `pathlib`, `shutil`, `tempfile` |
| CLI | `argparse` |
| subprocess | `subprocess.run` |
| log | `logging` |
| 日期時間 | `datetime`, `zoneinfo` |
| regex | `re` |
| queue／counter／LRU-like container | `collections` |
| iterator／函式工具 | `itertools`, `functools` |
| binary layout | `struct`, `memoryview` |
| hash／token | `hashlib`, `hmac`, `secrets` |
| JSON／CSV／SQLite | `json`, `csv`, `sqlite3` |
| test | `unittest`, `unittest.mock` |

### 9.2 `pathlib` 與安全 subprocess

```python
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent
config = root / "config" / "app.json"
text = config.read_text(encoding="utf-8")

completed = subprocess.run(
    ["git", "status", "--short"],
    cwd=root,
    text=True,
    capture_output=True,
    check=True,
    timeout=10,
)
print(completed.stdout)
```

不要把不可信字串拼成 shell command。`shell=False`（預設）加 argument list 最接近 Go `exec.Command` 的安全模型。

### 9.3 Logging，不要到處 print

```python
import logging

logger = logging.getLogger(__name__)


def process(job_id: str) -> None:
    logger.info("processing job", extra={"job_id": job_id})
    try:
        run_job(job_id)
    except JobError:
        logger.exception("job failed")  # 自動帶 traceback
        raise
```

library 不應在 import 時呼叫 `basicConfig`；由 application entry point 決定 handler、level、format。

---
