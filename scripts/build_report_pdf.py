"""Build REPORT.pdf from REPORT.md using Chrome/Edge headless printing.

Uses only the Python standard library plus an installed Chromium-based browser.
"""
from __future__ import annotations

import html
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "REPORT.md"
OUTPUT = ROOT / "REPORT.pdf"

BROWSERS = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]

INLINE_CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def inline(text: str) -> str:
    text = html.escape(text)
    text = INLINE_CODE.sub(r"<code>\1</code>", text)
    text = LINK.sub(r'<a href="\2">\1</a>', text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    text = ITALIC.sub(r"<em>\1</em>", text)
    return text


def is_separator(cells: list[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    i = 0
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            chunks: list[str] = []
            for line in paragraph:
                if line.endswith("  "):
                    chunks.append(inline(line.rstrip()) + "<br>")
                else:
                    chunks.append(inline(line))
            out.append("<p>" + " ".join(chunks) + "</p>")
            paragraph.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            flush_paragraph()
            i += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            language = stripped[3:].strip()
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{html.escape(language)}"' if language else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if stripped == "---":
            flush_paragraph()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("> "):
                quote.append(lines[i].strip()[2:])
                i += 1
            out.append("<blockquote>" + inline(" ".join(quote)) + "</blockquote>")
            continue

        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)$", stripped)
        if image:
            flush_paragraph()
            alt, src = image.group(1), image.group(2)
            path = (ROOT / src).resolve()
            figure = (
                '<figure><img src="' + html.escape(path.as_uri(), quote=True) +
                '" alt="' + html.escape(alt, quote=True) + '">'
            )
            if i + 1 < len(lines):
                caption = lines[i + 1].strip()
                if caption.startswith("*") and caption.endswith("*") and not caption.startswith("**"):
                    figure += "<figcaption>" + inline(caption.strip("*")) + "</figcaption>"
                    i += 1
            figure += "</figure>"
            out.append(figure)
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            flush_paragraph()
            header = split_row(stripped)
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_row(lines[i])
                if not is_separator(cells):
                    rows.append(cells)
                i += 1
            table = ["<table><thead><tr>"]
            table.extend(f"<th>{inline(cell)}</th>" for cell in header)
            table.append("</tr></thead><tbody>")
            for row in rows:
                table.append("<tr>")
                table.extend(f"<td>{inline(cell)}</td>" for cell in row)
                table.append("</tr>")
            table.append("</tbody></table>")
            out.append("".join(table))
            continue

        if re.match(r"^[-*]\s+", stripped):
            flush_paragraph()
            items: list[str] = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            out.append("<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>")
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            items: list[str] = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            out.append("<ol>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ol>")
            continue

        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return "\n".join(out)


def build_html() -> str:
    body = markdown_to_html(SOURCE.read_text(encoding="utf-8"))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Project Report - Sentinel Chain</title>
<style>
  @page {{ size: A4; margin: 11mm 12mm 11mm 12mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Segoe UI", Arial, sans-serif; font-size: 9.2pt; line-height: 1.32; color: #182033; margin: 0; }}
  h1 {{ color: #4c2a94; font-size: 19pt; line-height: 1.15; margin: 0 0 9px; border-bottom: 2px solid #22d3ee; padding-bottom: 6px; }}
  h2 {{ color: #3b1f78; font-size: 12.5pt; margin: 13px 0 5px; border-bottom: 1px solid #cfd6e4; padding-bottom: 3px; }}
  h3 {{ color: #2563a8; font-size: 10.5pt; margin: 9px 0 3px; }}
  p {{ margin: 0 0 5px; text-align: justify; }}
  strong {{ color: #26314a; }}
  blockquote {{ margin: 6px 0; padding: 5px 8px; background: #f1f5ff; border-left: 3px solid #6d5bd0; color: #30385a; }}
  hr {{ border: none; border-top: 1px solid #d8deea; margin: 8px 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 6px 0 8px; font-size: 8.1pt; }}
  th, td {{ border: 1px solid #cbd3e1; padding: 2.5px 4px; text-align: left; vertical-align: top; }}
  th {{ background: #e9edf8; color: #2d2352; }}
  tr:nth-child(even) td {{ background: #f8fafc; }}
  ul, ol {{ margin: 3px 0 6px 16px; padding: 0; }}
  li {{ margin-bottom: 2px; }}
  pre {{ background: #0b1430; color: #e8eefc; padding: 6px 8px; border-radius: 4px; overflow: auto; font-family: Consolas, monospace; font-size: 7.8pt; white-space: pre-wrap; }}
  code {{ font-family: Consolas, monospace; }}
  p code, li code, td code, blockquote code {{ background: #edf0f7; color: #7c2d9e; padding: 0 2px; border-radius: 2px; }}
  a {{ color: #2563a8; text-decoration: none; }}
  figure {{ margin: 6px 0; text-align: center; }}
  figure img {{ max-width: 100%; max-height: 72mm; border: 1px solid #cbd3e1; border-radius: 4px; }}
  figcaption {{ font-size: 7.8pt; color: #55627a; margin-top: 3px; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def browser_path() -> Path:
    for candidate in BROWSERS:
        if candidate.exists():
            return candidate
    raise SystemExit("No Chrome or Edge executable found. Install Chrome/Edge to build the PDF.")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="report-pdf-") as tmp:
        html_path = Path(tmp) / "REPORT.html"
        html_path.write_text(build_html(), encoding="utf-8")
        profile = Path(tmp) / "profile"
        command = [
            str(browser_path()),
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--allow-file-access-from-files",
            "--no-pdf-header-footer",
            "--run-all-compositor-stages-before-draw",
            "--virtual-time-budget=15000",
            f"--user-data-dir={profile}",
            f"--print-to-pdf={OUTPUT}",
            html_path.as_uri(),
        ]
        env = dict(os.environ)
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=180)
        if result.returncode != 0:
            raise SystemExit(result.stderr or result.stdout)
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
