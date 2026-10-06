"""Builds the paste-ready knowledge base articles and the copy page from src/.

Articles are plain semantic HTML (headings, paragraphs, lists, tables, links, bold and code),
because they are pasted as formatted text into HubSpot's normal article editor, which keeps that
structure but drops layout boxes such as styled div and span elements. Two kinds of token are
resolved here:

- {{style:<name>}} expands to an inline style from STYLES, so every article shares one look.
- {{endpoints:<module>}} expands to the module's endpoint table, generated from the same
  endpoint list the Mintlify reference is built from.

Every link written as {{MINTLIFY}}/<page> must name a page that is in the Mintlify
navigation and exists on disk; the build fails otherwise.
"""

import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "src"
OUTPUT = ROOT / "articles"
PLACEHOLDER = "https://YOUR-MINTLIFY-SITE"
TOKEN = "{{MINTLIFY}}"

LINE = "#dfe3eb"
SOFT = "#f5f8fa"
MONO = "Consolas, Menlo, Monaco, monospace"

STYLES = {
    "lead": "margin: 0 0 16px;",
    "p": "margin: 0 0 16px;",
    "h2": "margin: 32px 0 12px;",
    "h3": "margin: 24px 0 8px;",
    "ul": "margin: 0 0 16px; padding-left: 24px;",
    "ol": "margin: 0 0 16px; padding-left: 24px;",
    "li": "margin: 0 0 6px;",
    "a": "",
    "code": "font-family: %s; font-size: 0.9em; background-color: %s; border: 1px solid %s; border-radius: 3px; padding: 1px 4px;" % (MONO, SOFT, LINE),
    "pre": "font-family: %s; font-size: 0.9em; line-height: 1.5; background-color: %s; border: 1px solid %s; border-radius: 4px; padding: 12px 14px; margin: 0 0 16px; white-space: pre-wrap; word-break: break-word;" % (MONO, SOFT, LINE),
    "table": "width: 100%%; border-collapse: collapse; margin: 0 0 20px; border: 1px solid %s;" % LINE,
    "th": "text-align: left; font-weight: 700; padding: 8px 12px; background-color: %s; border-bottom: 1px solid %s;" % (SOFT, LINE),
    "td": "padding: 8px 12px; border-bottom: 1px solid %s; vertical-align: top;" % LINE,
}

FORBIDDEN = [
    (re.compile(r"[a-z0-9-]+\.mywebcommander\.com", re.I), "a store address"),
    (re.compile(r"client_secret\s*[:=]", re.I), "credential"),
    (re.compile(r"<h1\b", re.I), "an <h1> (HubSpot renders the title as the heading)"),
    (re.compile(r"<style\b|<script\b|<link\b", re.I), "a tag HubSpot strips"),
    (re.compile(r"\sclass=", re.I), "a class attribute (HubSpot keeps inline styles only)"),
    (re.compile(r"<div\b|<span\b", re.I), "a div or span (lost when pasted as formatted text)"),
    (re.compile(r"\{\{"), "an unresolved template token"),
]


def navigation_pages(docs_json):
    pages = set()

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == "pages":
                    for page in value:
                        if isinstance(page, str):
                            pages.add(page)
                        else:
                            walk(page)
                else:
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(docs_json.get("navigation", {}))
    return pages


def load_module(docs_dir, name):
    path = docs_dir / "tools" / "modules" / (name + ".py")
    spec = importlib.util.spec_from_file_location("reference_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def endpoint_table(module):
    rows = []
    for endpoint in module.ENDPOINTS:
        rows.append(
            '<tr><td style="{{style:td}}"><a href="{{MINTLIFY}}/api-reference/%s/%s" style="{{style:a}}">%s</a>'
            '<br>%s</td>'
            '<td style="{{style:td}} white-space: nowrap;"><strong>%s</strong></td>'
            '<td style="{{style:td}}"><code style="{{style:code}}">%s</code></td></tr>'
            % (module.SLUG, endpoint["slug"], endpoint["title"],
               re.sub(r"`([^`]+)`", r"\1", endpoint["summary"]), endpoint["method"],
               endpoint["path"].replace(module.BASE, "…" + module.BASE[module.BASE.rfind("/"):])))
    return ('<table style="{{style:table}}"><thead><tr>'
            '<th style="{{style:th}}">Endpoint</th><th style="{{style:th}}">Method</th><th style="{{style:th}}">Path</th>'
            '</tr></thead><tbody>' + "".join(rows) + "</tbody></table>")


def render(source, docs_dir, base):
    source = re.sub(r"\{\{endpoints:([a-z_]+)\}\}", lambda m: endpoint_table(load_module(docs_dir, m.group(1))), source)
    links = sorted(set(re.findall(re.escape(TOKEN) + r"/([A-Za-z0-9_/-]+)", source)))
    unknown_styles = sorted(set(re.findall(r"\{\{style:([a-z0-9-]+)\}\}", source)) - set(STYLES))
    html = re.sub(r"\{\{style:([a-z0-9-]+)\}\}", lambda m: STYLES.get(m.group(1), m.group(0)), source)
    html = html.replace(' style=""', "")
    return html.replace(TOKEN, base), links, unknown_styles


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    base = config["mintlify_base"].rstrip("/")
    docs_dir = (ROOT / config["docs_dir"]).resolve()
    pages = navigation_pages(json.loads((docs_dir / "docs.json").read_text(encoding="utf-8")))
    manifest = json.loads((SOURCE / "articles.json").read_text(encoding="utf-8"))
    category = manifest["category"]

    problems = []
    built = []
    for entry in manifest["articles"]:
        source = (SOURCE / "articles" / entry["file"]).read_text(encoding="utf-8")
        html, links, unknown_styles = render(source, docs_dir, base)
        for page in links:
            if page not in pages or not (docs_dir / (page + ".mdx")).is_file():
                problems.append("%s links to '%s', which is not a Mintlify page" % (entry["file"], page))
        for name in unknown_styles:
            problems.append("%s uses an unknown style '%s'" % (entry["file"], name))
        for pattern, meaning in FORBIDDEN:
            if pattern.search(html):
                problems.append("%s contains %s" % (entry["file"], meaning))
        built.append(dict(entry, html=html, size=len(html.encode("utf-8"))))

    if problems:
        print("Build failed:")
        for problem in problems:
            print("  - " + problem)
        return 1

    OUTPUT.mkdir(exist_ok=True)
    for article in built:
        (OUTPUT / article["file"]).write_text(article["html"], encoding="utf-8")

    data = json.dumps(
        {"base": base, "placeholder": base == PLACEHOLDER, "category": category, "articles": built},
        ensure_ascii=False,
    ).replace("</", "<\\/")
    template = (SOURCE / "index.template.html").read_text(encoding="utf-8")
    (ROOT / "index.html").write_text(template.replace("__DATA__", data), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")

    print("Built %d articles; links point to %s%s" % (
        len(built), base, " (placeholder)" if base == PLACEHOLDER else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
