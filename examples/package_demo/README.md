# package_demo

這是教材第 6 章的可執行版本：distribution 名稱 `packet-lab-demo`，import package 名稱 `packet_lab`。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m packet_lab encode ping hello
packet-lab encode data world
python -m unittest discover -s tests -v
```

觀察 `src/packet_lab/__init__.py` 如何 re-export public API，以及 `__main__.py` 如何把 `python -m packet_lab` 接到 CLI。
