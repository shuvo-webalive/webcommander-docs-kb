"""Builds the paste-ready knowledge base articles and the copy page from src/.

Every link written as {{MINTLIFY}}/<page> must name a page that exists in the Mintlify
project and is in its navigation; the build fails otherwise.
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SOURCE = ROOT / "src"
OUTPUT = ROOT / "articles"
PLACEHOLDER = "https://YOUR-MINTLIFY-SITE"
TOKEN = "{{MINTLIFY}}"
FORBIDDEN = [
    (re.compile(r"01404cc6", re.I), "store base URL"),
    (re.compile(r"mywebcommander\.com", re.I), "store host"),
    (re.compile(r"client_secret\s*[:=]", re.I), "credential"),
    (re.compile(r"<h1\b", re.I), "an <h1> (HubSpot renders the title as the heading)"),
    (re.compile(r"<style\b|<script\b|<link\b", re.I), "a tag HubSpot strips"),
    (re.compile(r"\sclass=", re.I), "a class attribute (HubSpot keeps inline styles only)"),
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


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    base = config["mintlify_base"].rstrip("/")
    docs_dir = (ROOT / config["docs_dir"]).resolve()
    docs_json = json.loads((docs_dir / "docs.json").read_text(encoding="utf-8"))
    pages = navigation_pages(docs_json)
    manifest = json.loads((SOURCE / "articles.json").read_text(encoding="utf-8"))

    problems = []
    built = []
    for entry in manifest:
        source = (SOURCE / "articles" / entry["file"]).read_text(encoding="utf-8")
        for page in sorted(set(re.findall(re.escape(TOKEN) + r"/([A-Za-z0-9_/-]+)", source))):
            if page not in pages or not (docs_dir / (page + ".mdx")).is_file():
                problems.append("%s links to '%s', which is not a Mintlify page" % (entry["file"], page))
        html = source.replace(TOKEN, base)
        for pattern, meaning in FORBIDDEN:
            if pattern.search(html):
                problems.append("%s contains %s" % (entry["file"], meaning))
        built.append(dict(entry, html=html))

    if problems:
        print("Build failed:")
        for problem in problems:
            print("  - " + problem)
        return 1

    OUTPUT.mkdir(exist_ok=True)
    for article in built:
        (OUTPUT / article["file"]).write_text(article["html"], encoding="utf-8")

    data = json.dumps(
        {"base": base, "placeholder": base == PLACEHOLDER, "articles": built},
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
