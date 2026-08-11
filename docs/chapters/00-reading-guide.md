# Modern Python，給 C++／Go／Lua 工程師

> 基準：Python 3.12+。標成「3.13+」「3.14+」的內容才需要更新版本。

這不是語法百科，而是一張重新進入 Python 的地圖。每章都盡量沿用你已經熟悉的概念：C++ 的 RAII、template、thread，Go 的 package、interface、goroutine，Lua 的 table、first-class function。

## 怎麼讀，認知負擔最低

先記住五句話：

1. 變數是「名稱綁到物件」，不是帶型別的儲存格。
2. module 是一個 `.py` 檔；package 是可包含 module 的 module。
3. `with` 管資源生命週期；不要等 GC 幫你關檔案。
4. I/O concurrency 先選 thread 或 async；CPU parallelism 先選 process。
5. Python 沒有 preprocessor macro；函式、decorator、context manager、class factory 通常才是答案。

閱讀標記：

- **現在學**：日常程式會直接用到。
- **用到再學**：知道名字與用途即可。
- **避免**：能做，但通常會讓維護成本上升。

---
