"""Build one self-contained HTML tutorial from the size-limited Markdown chapters."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re

import markdown

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS = ROOT / "docs" / "chapters"
OUTPUT = ROOT / "docs" / "modern-python-for-systems-engineers.html"
HTML_DIR = ROOT / "docs" / "html"
ASSET_DIR = ROOT / "docs" / "assets"

CSS = r"""
:root {
  color-scheme: light dark;
  --bg: #f7f8f5;
  --panel: #ffffff;
  --text: #17211d;
  --muted: #5c6b63;
  --line: #dce3de;
  --accent: #126e5a;
  --accent-soft: #e1f2eb;
  --code: #14201c;
  --code-text: #e7f2ec;
  --shadow: 0 12px 36px rgba(21, 42, 34, .08);
}
[data-theme="dark"] {
  --bg: #101613;
  --panel: #17201c;
  --text: #e7eee9;
  --muted: #a5b4ac;
  --line: #314039;
  --accent: #6fd0b1;
  --accent-soft: #203b32;
  --code: #0b100e;
  --code-text: #dcebe3;
  --shadow: none;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) {
    --bg: #101613;
    --panel: #17201c;
    --text: #e7eee9;
    --muted: #a5b4ac;
    --line: #314039;
    --accent: #6fd0b1;
    --accent-soft: #203b32;
    --code: #0b100e;
    --code-text: #dcebe3;
    --shadow: none;
  }
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 2rem; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 16px/1.75 system-ui, -apple-system, "Segoe UI", "Noto Sans TC", sans-serif;
}
a { color: var(--accent); text-underline-offset: .2em; }
.topbar {
  position: sticky; top: 0; z-index: 10;
  display: flex; align-items: center; justify-content: space-between;
  padding: .75rem max(1rem, calc((100vw - 1440px) / 2));
  border-bottom: 1px solid var(--line);
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(14px);
}
.brand { font-weight: 750; letter-spacing: .01em; }
.controls { display: flex; gap: .5rem; }
button {
  border: 1px solid var(--line); border-radius: .55rem;
  padding: .4rem .7rem; background: var(--panel); color: var(--text); cursor: pointer;
}
.layout {
  display: grid; grid-template-columns: 280px minmax(0, 850px); gap: 3rem;
  max-width: 1240px; margin: 0 auto; padding: 2.5rem 2rem 6rem;
}
.sidebar { position: sticky; top: 5rem; align-self: start; max-height: calc(100vh - 6rem); overflow: auto; }
.sidebar h2 { margin: 0 0 .75rem; font-size: .85rem; text-transform: uppercase; color: var(--muted); }
.sidebar ul { list-style: none; margin: 0; padding: 0; }
.sidebar ul ul { padding-left: .9rem; border-left: 1px solid var(--line); }
.sidebar a { display: block; padding: .2rem 0; color: var(--muted); text-decoration: none; font-size: .88rem; line-height: 1.35; }
.sidebar a:hover { color: var(--accent); }
article { min-width: 0; padding: 3rem 4rem 5rem; background: var(--panel); border: 1px solid var(--line); border-radius: 1rem; box-shadow: var(--shadow); }
h1, h2, h3, h4 { line-height: 1.3; letter-spacing: -.015em; }
h1 { margin-top: 0; font-size: clamp(2rem, 5vw, 3.2rem); }
h2 { margin-top: 4rem; padding-top: 1rem; border-top: 1px solid var(--line); font-size: 1.8rem; }
h3 { margin-top: 2.4rem; font-size: 1.28rem; }
p, li { max-width: 76ch; }
blockquote { margin: 1.5rem 0; padding: .7rem 1rem; border-left: 4px solid var(--accent); background: var(--accent-soft); }
blockquote p { margin: 0; }
code { padding: .12em .35em; border-radius: .3rem; background: var(--accent-soft); font: .92em/1.5 ui-monospace, "Cascadia Code", Consolas, monospace; }
pre { overflow: auto; margin: 1.2rem 0 1.8rem; padding: 1rem 1.15rem; border-radius: .75rem; background: var(--code); color: var(--code-text); tab-size: 4; }
pre code { padding: 0; background: transparent; color: inherit; }
table { display: block; width: max-content; max-width: 100%; overflow-x: auto; border-collapse: collapse; margin: 1.2rem 0 2rem; }
th, td { padding: .55rem .75rem; border: 1px solid var(--line); text-align: left; vertical-align: top; }
th { background: var(--accent-soft); }
hr { margin: 4rem 0; border: 0; border-top: 1px solid var(--line); }
.skip-link { position: absolute; left: -9999px; }
.skip-link:focus { left: 1rem; top: 1rem; z-index: 30; padding: .5rem; background: var(--panel); }
.mobile-toc { display: none; margin-bottom: 1rem; }
.footer { margin-top: 4rem; color: var(--muted); font-size: .9rem; }
.chapter-nav { display: flex; justify-content: space-between; gap: 1rem; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--line); }
.chapter-nav a { max-width: 46%; text-decoration: none; }
.chapter-list { margin: 0; padding-left: 1.2rem; }
.chapter-list li { margin: .22rem 0; }
.chapter-list a[aria-current="page"] { color: var(--accent); font-weight: 700; }
.landing-shell { max-width: 1120px; margin: 0 auto; padding: 3rem 1.25rem 6rem; }
.hero { max-width: 780px; margin-bottom: 2.5rem; }
.hero h1 { margin-bottom: .75rem; }
.routes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 2rem 0 3rem; }
.route { padding: 1rem 1.15rem; border: 1px solid var(--line); border-radius: .8rem; background: var(--panel); }
.route strong { display: block; margin-bottom: .3rem; }
.cards { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .8rem; }
.card { display: block; padding: 1rem 1.15rem; border: 1px solid var(--line); border-radius: .8rem; background: var(--panel); text-decoration: none; box-shadow: var(--shadow); }
.card:hover { border-color: var(--accent); transform: translateY(-1px); }
.card strong { display: block; color: var(--text); }
.card span { color: var(--muted); font-size: .92rem; }
@media (max-width: 900px) {
  .layout { display: block; padding: 1rem; }
  .sidebar { display: none; }
  .mobile-toc { display: block; }
  article { padding: 1.5rem clamp(1rem, 4vw, 2rem) 3rem; border-radius: .75rem; }
  h2 { margin-top: 3rem; font-size: 1.55rem; }
  .routes, .cards { grid-template-columns: 1fr; }
  .landing-shell { padding-top: 2rem; }
  .chapter-nav { font-size: .92rem; }
}
@media print {
  .topbar, .sidebar, .mobile-toc { display: none; }
  body, article { background: #fff; color: #000; }
  .layout { display: block; max-width: none; padding: 0; }
  article { border: 0; box-shadow: none; padding: 0; }
  pre { white-space: pre-wrap; }
}
"""

JS = r"""
const root = document.documentElement;
const saved = localStorage.getItem("tutorial-theme");
if (saved) root.dataset.theme = saved;
document.querySelector("#theme-toggle")?.addEventListener("click", () => {
  const next = root.dataset.theme === "dark" ? "light" : "dark";
  root.dataset.theme = next;
  localStorage.setItem("tutorial-theme", next);
});
"""

DESCRIPTIONS = {
    "00-reading-guide": "先建立五句心法與最省力的閱讀方式。",
    "01-quick-start": "執行方式、核心語法、容器、Unicode 與既有語言對照。",
    "02-iterators-functional": "iterator、generator、comprehension 與實用 functional programming。",
    "03-classes-typing": "dataclass、data model、Protocol 與現代型別提示。",
    "04-errors": "exception、錯誤邊界、例外鏈與 ExceptionGroup。",
    "05-memory-raii": "名稱綁定、GC、外部資源與 Python 的 RAII 對應。",
    "06-projects-imports": "module、package、src layout、可被 import 與 wheel。",
    "07-macro-alternatives": "decorator、context manager、registration 與 codegen 的選擇。",
    "08-concurrency": "thread、process、async、GIL 與 free-threaded Python。",
    "09-standard-library": "路徑、subprocess、logging 等日常 module 導航。",
    "10-json": "JSON 型別邊界、驗證、編碼與安全陷阱。",
    "11-http": "同步／非同步 client、timeout、retry、stream 與 endpoint。",
    "12-c-ffi": "ctypes、CFFI、pointer ownership、callback 與 GIL。",
    "13-testing-workflow": "測試分層、品質 gate、dependency 與 public API。",
    "14-openai-responses": "Responses API：stream、image、tool、reasoning、CLI 與 HTTP endpoint。",
    "15-decision-table": "需要選工具時，先從這張表開始。",
    "16-exercises": "由小到大的六個實作練習。",
    "17-references": "Python、Packaging 與 OpenAI 官方資料來源。",
}


def chapter_title(source: str, fallback: str) -> str:
    match = re.search(r"^## (.+)$", source, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def page_head(title: str, stylesheet: str) -> str:
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="給 C++、Go、Lua 工程師的現代 Python 教材">
  <title>{escape(title)} · Modern Python</title>
  <link rel="stylesheet" href="{stylesheet}">
</head>"""


def chapter_list(chapters: list[dict[str, object]], current: str | None = None) -> str:
    items: list[str] = []
    for chapter in chapters:
        current_attr = ' aria-current="page"' if chapter["stem"] == current else ""
        items.append(
            f'<li><a href="{escape(str(chapter["href"]))}"{current_attr}>'
            f'{escape(str(chapter["title"]))}</a></li>'
        )
    return '<ol class="chapter-list">' + "".join(items) + "</ol>"


def main() -> None:
    files = sorted(CHAPTERS.glob("*.md"))
    if not files:
        raise SystemExit("no Markdown chapters found")
    oversized = [path for path in files if path.stat().st_size > 8_000]
    if oversized:
        raise SystemExit(f"Markdown chapters exceed 8 KB: {oversized}")

    HTML_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    (ASSET_DIR / "tutorial.css").write_text(CSS.strip() + "\n", encoding="utf-8", newline="\n")
    (ASSET_DIR / "tutorial.js").write_text(JS.strip() + "\n", encoding="utf-8", newline="\n")

    chapters: list[dict[str, object]] = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        stem = path.stem
        chapters.append(
            {
                "path": path,
                "source": source,
                "stem": stem,
                "title": chapter_title(source, stem),
                "description": DESCRIPTIONS.get(stem, ""),
                "href": f"{stem}.html",
            }
        )

    for index, chapter in enumerate(chapters):
        converter = markdown.Markdown(
            extensions=["extra", "sane_lists", "toc"],
            extension_configs={"toc": {"permalink": True, "toc_depth": "2-3"}},
            output_format="html5",
        )
        content = converter.convert(str(chapter["source"]))
        previous_link = ""
        if index > 0:
            previous = chapters[index - 1]
            previous_link = f'<a rel="prev" href="{previous["href"]}">← {escape(str(previous["title"]))}</a>'
        next_link = ""
        if index + 1 < len(chapters):
            following = chapters[index + 1]
            next_link = f'<a rel="next" href="{following["href"]}">{escape(str(following["title"]))} →</a>'
        navigation = chapter_list(chapters, str(chapter["stem"]))
        document = f"""{page_head(str(chapter["title"]), "../assets/tutorial.css")}
<body>
  <a class="skip-link" href="#content">跳到本文</a>
  <header class="topbar">
    <a class="brand" href="../modern-python-for-systems-engineers.html">Modern Python</a>
    <div class="controls"><button id="theme-toggle" type="button" aria-label="切換明暗主題">明／暗</button></div>
  </header>
  <div class="layout">
    <nav class="sidebar" aria-label="全部章節"><h2>全部章節</h2>{navigation}</nav>
    <main>
      <details class="mobile-toc"><summary>本章目錄</summary>{converter.toc}</details>
      <article id="content">
        {content}
        <nav class="chapter-nav" aria-label="前後章節">{previous_link}<a href="../modern-python-for-systems-engineers.html">回索引</a>{next_link}</nav>
        <p class="footer"><a href="../chapters/{chapter["path"].name}">閱讀本章 Markdown</a> · 最後更新 2026-08-11。</p>
      </article>
    </main>
  </div>
  <script src="../assets/tutorial.js"></script>
</body>
</html>
"""
        (HTML_DIR / str(chapter["href"])).write_text(document, encoding="utf-8", newline="\n")

    cards = "".join(
        f'<a class="card" href="html/{chapter["href"]}"><strong>{escape(str(chapter["title"]))}</strong>'
        f'<span>{escape(str(chapter["description"]))}</span></a>'
        for chapter in chapters
    )
    title = "Modern Python，給 C++／Go／Lua 工程師"
    landing = f"""{page_head(title, "assets/tutorial.css")}
<body>
  <header class="topbar">
    <span class="brand">Modern Python</span>
    <div class="controls"><a href="index.md">Markdown</a><button id="theme-toggle" type="button" aria-label="切換明暗主題">明／暗</button></div>
  </header>
  <main class="landing-shell" id="content">
    <section class="hero">
      <h1>{escape(title)}</h1>
      <p>用你熟悉的 C++、Go、Lua 心智模型，低負擔地追回現代 Python。每章獨立成頁，不必捲完整本書。</p>
    </section>
    <section class="routes" aria-label="建議閱讀路線">
      <div class="route"><strong>快速回鍋</strong><span>先讀 0、1、5、6：心法、語法、RAII、import。</span></div>
      <div class="route"><strong>工程主題</strong><span>直接挑 7–13：macro、並行、JSON、HTTP、FFI、測試。</span></div>
      <div class="route"><strong>完整實戰</strong><span>最後讀 14：OpenAI stream、image、tool、reasoning 與 endpoint。</span></div>
    </section>
    <h2>章節</h2>
    <section class="cards">{cards}</section>
    <p class="footer">Markdown 每檔低於 8 KB；HTML 每章獨立。最後更新 2026-08-11。</p>
  </main>
  <script src="assets/tutorial.js"></script>
</body>
</html>
"""
    OUTPUT.write_text(landing, encoding="utf-8", newline="\n")
    sizes = [(HTML_DIR / str(chapter["href"])).stat().st_size for chapter in chapters]
    print(f"wrote landing + {len(chapters)} chapter pages; largest chapter HTML: {max(sizes):,} bytes")


if __name__ == "__main__":
    main()
