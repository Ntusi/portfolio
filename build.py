#!/usr/bin/env python3
"""Build ntusekhomngadi.com.

Reads content/projects.json, drops the cards into site/template.html and
writes the finished site to dist/. Standard library only, so it runs the
same on your laptop, in CloudShell and in GitHub Actions.

    python3 build.py              build into dist/
    python3 build.py --serve      build, then preview at http://localhost:8000
"""
import html
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "site"
CONTENT = ROOT / "content" / "projects.json"
DIST = ROOT / "dist"

MUSTARD, PAPER, INK = "#E5A93A", "#F1EEE2", "#17201A"
BANNED = {"—": "em dash", "...": "three dots (use …)"}


class ContentError(Exception):
    pass


def esc(value):
    return html.escape(str(value), quote=True)


def check_text(where, text):
    for bad, name in BANNED.items():
        if bad in text:
            raise ContentError(f"{where}: contains an {name}. Rewrite that bit.")


def check_item(section, i, item):
    where = f'{section}[{i}] "{item.get("title", "?")}"'
    for key in ("title", "description"):
        if not str(item.get(key, "")).strip():
            raise ContentError(f"{where}: missing {key}.")
    for key in ("title", "description", "status", "stack"):
        if key in item:
            check_text(f"{where} {key}", str(item[key]))
    link = item.get("link")
    if link is not None:
        if not isinstance(link, dict) or not link.get("label") or not link.get("url"):
            raise ContentError(f'{where}: link needs both "label" and "url".')
        if not str(link["url"]).startswith(("https://", "mailto:")):
            raise ContentError(f"{where}: link url must start with https://")
        check_text(f"{where} link label", link["label"])


def status_html(item, on_dark):
    status = item.get("status")
    if not status:
        return ""
    live = "progress" in status.lower()
    colour = MUSTARD if (live and on_dark) else (PAPER if on_dark else "#5A3E08" if live else "#2E5A3E")
    return f'<p style="margin: 0 0 10px; font-size: 14px; font-weight: 600; color: {colour}">{esc(status)}</p>\n'


def card(item, on_dark, title_size):
    rule = MUSTARD if on_dark else INK
    body_colour = "color: #E4E1D4" if on_dark else ""
    meta_colour = "#C9C6B6" if on_dark else "#4C574F"
    link = item.get("link")
    parts = [f'<article style="border-top: 1.5px solid {rule}; padding: 24px 0 40px">\n']
    parts.append(status_html(item, on_dark))
    parts.append(f'<h3 class="serif" style="font-size: {title_size}px; line-height: 1.15; margin: 0 0 12px">{esc(item["title"])}</h3>\n')
    parts.append(f'<p style="margin: 0 0 16px; {body_colour}">{esc(item["description"])}</p>\n')
    if item.get("stack"):
        gap = "14px" if link else "0"
        parts.append(f'<p style="margin: 0 0 {gap}; font-size: 14px; color: {meta_colour}">{esc(item["stack"])}</p>\n')
    if link:
        parts.append(f'<a class="tlink" href="{esc(link["url"])}" style="font-size: 15px; font-weight: 600">{esc(link["label"])}</a>\n')
    parts.append("</article>")
    return "".join(parts)


def certifications_html(certs, also):
    items = "".join(f"<li>{esc(c)}</li>\n" for c in certs)
    out = ('<ul style="list-style: none; margin: 0 0 12px; padding: 0; display: flex; '
           'flex-direction: column; gap: 6px; font-size: 16px">\n' + items + "</ul>\n")
    if also:
        out += f'<p style="margin: 0; font-size: 14px; color: #4C574F">{esc(also)}</p>'
    return out


def build():
    try:
        data = json.loads(CONTENT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ContentError(f"projects.json is not valid JSON: line {e.lineno}, column {e.colno}: {e.msg}. "
                           "Usually a missing comma or an extra one after the last item.")

    sections = {"ai": (True, 28), "cloud": (False, 26), "building": (True, 26)}
    rendered = {}
    for name, (on_dark, size) in sections.items():
        items = data.get(name, [])
        if not items:
            raise ContentError(f'"{name}" needs at least one item.')
        for i, item in enumerate(items):
            check_item(name, i, item)
        rendered[name] = "\n".join(card(it, on_dark, size) for it in items)

    certs = data.get("certifications", [])
    for c in certs:
        check_text("certifications", c)
    also = data.get("certifications_also", "")
    check_text("certifications_also", also)

    page = (SITE / "template.html").read_text(encoding="utf-8")
    for marker, value in {
        "<!-- AI_PROJECTS -->": rendered["ai"],
        "<!-- CLOUD_PROJECTS -->": rendered["cloud"],
        "<!-- BUILDING_PROJECTS -->": rendered["building"],
        "<!-- CERTIFICATIONS -->": certifications_html(certs, also),
    }.items():
        if marker not in page:
            raise ContentError(f"template.html is missing the {marker} marker.")
        page = page.replace(marker, value)
    check_text("template.html", page)

    if DIST.exists():
        shutil.rmtree(DIST)
    shutil.copytree(SITE, DIST, ignore=shutil.ignore_patterns("template.html"))
    (DIST / "index.html").write_text(page, encoding="utf-8")
    total = sum(len(data[s]) for s in sections)
    print(f"Built dist/ with {total} projects and {len(certs)} certifications.")


def main():
    try:
        build()
    except ContentError as e:
        print(f"Build stopped: {e}", file=sys.stderr)
        sys.exit(1)
    if "--serve" in sys.argv:
        import functools
        import http.server
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
        print("Preview at http://localhost:8000 (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()


if __name__ == "__main__":
    main()
