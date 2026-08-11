"""Check Markdown size/link invariants and the generated HTML structure."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
HTML = DOCS / "modern-python-for-systems-engineers.html"


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.hrefs: list[str] = []
        self.local_references: list[str] = []
        self.heading_level: str | None = None
        self.heading_text: list[str] = []
        self.headings: list[tuple[str, str]] = []
        self.has_viewport = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if identifier := attributes.get("id"):
            self.ids.append(identifier)
        if href := attributes.get("href"):
            self.local_references.append(href)
            if tag == "a":
                self.hrefs.append(href)
        if source := attributes.get("src"):
            self.local_references.append(source)
        if tag == "meta" and attributes.get("name") == "viewport":
            self.has_viewport = True
        if tag in {"h1", "h2", "h3"}:
            self.heading_level = tag
            self.heading_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == self.heading_level:
            self.headings.append((tag, "".join(self.heading_text).strip()))
            self.heading_level = None

    def handle_data(self, data: str) -> None:
        if self.heading_level:
            self.heading_text.append(data)


def resolve_local_link(source: Path, href: str) -> Path | None:
    parsed = urlsplit(href)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    return (source.parent / unquote(parsed.path)).resolve()


def main() -> None:
    errors: list[str] = []
    markdown_files = [ROOT / "README.md"]
    markdown_files += sorted(DOCS.rglob("*.md"))
    markdown_files += sorted((ROOT / "examples").rglob("*.md"))
    for path in markdown_files:
        if path.stat().st_size > 8_000:
            errors.append(f"Markdown exceeds 8,000 bytes: {path}")
        text = path.read_text(encoding="utf-8")
        if text.count("```") % 2:
            errors.append(f"unbalanced fenced code block: {path}")

    index = DOCS / "index.md"
    for line in index.read_text(encoding="utf-8").splitlines():
        if "](chapters/" not in line:
            continue
        relative = line.split("](chapters/", 1)[1].split(")", 1)[0]
        if not (DOCS / "chapters" / relative).is_file():
            errors.append(f"index target missing: {relative}")

    chapter_markdown = sorted((DOCS / "chapters").glob("*.md"))
    chapter_html = sorted((DOCS / "html").glob("*.html"))
    expected_html_names = {f"{path.stem}.html" for path in chapter_markdown}
    actual_html_names = {path.name for path in chapter_html}
    if actual_html_names != expected_html_names:
        errors.append(
            f"chapter HTML set differs from Markdown: "
            f"missing={sorted(expected_html_names - actual_html_names)}, "
            f"extra={sorted(actual_html_names - expected_html_names)}"
        )
    if HTML.stat().st_size > 10_000:
        errors.append(f"HTML landing page is too large: {HTML.stat().st_size} bytes")
    for path in chapter_html:
        if path.stat().st_size > 20_000:
            errors.append(f"chapter HTML is too large: {path} ({path.stat().st_size} bytes)")

    all_headings: list[tuple[str, str]] = []
    total_links = 0
    for html_file in [HTML, *chapter_html]:
        document = html_file.read_text(encoding="utf-8")
        parser = DocumentParser()
        parser.feed(document)
        all_headings.extend(parser.headings)
        total_links += len(parser.hrefs)
        if not document.lower().startswith("<!doctype html>"):
            errors.append(f"HTML5 doctype missing: {html_file}")
        if not parser.has_viewport:
            errors.append(f"viewport meta missing: {html_file}")
        if "<style" in document.lower():
            errors.append(f"inline CSS found instead of shared asset: {html_file}")
        duplicate_ids = sorted({value for value in parser.ids if parser.ids.count(value) > 1})
        if duplicate_ids:
            errors.append(f"duplicate HTML ids in {html_file.name}: {duplicate_ids}")

        id_set = set(parser.ids)
        for reference in parser.local_references:
            parsed = urlsplit(reference)
            if parsed.path in {"", html_file.name} and parsed.fragment and parsed.fragment not in id_set:
                errors.append(f"broken fragment in {html_file.name}: {reference}")
            target = resolve_local_link(html_file, reference)
            if target is not None and not target.exists():
                errors.append(f"broken local link in {html_file.name}: {reference}")

    landing = DocumentParser()
    landing.feed(HTML.read_text(encoding="utf-8"))
    landing_chapters = {urlsplit(href).path.removeprefix("html/") for href in landing.hrefs if href.startswith("html/")}
    if landing_chapters != expected_html_names:
        errors.append("landing page does not link every chapter exactly once")

    h2_text = [text for level, text in all_headings if level == "h2"]
    expected = [f"{number}." for number in range(1, 17)] + ["參考資料"]
    for prefix in expected:
        if not any(text.startswith(prefix) for text in h2_text):
            errors.append(f"missing h2 section: {prefix}")

    if errors:
        raise SystemExit("\n".join(errors))
    print(
        f"OK: {len(markdown_files)} Markdown files, "
        f"{len(chapter_html)} chapter HTML files, "
        f"{len(all_headings)} headings, {total_links} links"
    )


if __name__ == "__main__":
    main()
