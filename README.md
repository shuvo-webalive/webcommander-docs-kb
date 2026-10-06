# webcommander-docs-kb

Paste-ready HubSpot knowledge base articles for the WebCommander API and SDKs, and a page that
lets you copy each one. The full reference lives on the Mintlify site; every article links to it.

## Using the copy page

Open the published page (GitHub Pages), pick an article, click **Copy article**, then in HubSpot:

1. Open the article and set its title and subtitle to the ones shown on the page.
2. Click into the article body and paste (Ctrl+V, or Cmd+V on a Mac).
3. Save, then preview before you publish.

**Copy article** puts the article on the clipboard as formatted text, the same as copying from a web
page, so it pastes into HubSpot's normal editor with its headings, lists, tables, links, bold and code
intact. No source code view is needed.

## Layout

| Path | What it is |
| --- | --- |
| `src/articles/*.html` | Article sources. Links to the docs are written `{{MINTLIFY}}/<page>`. |
| `src/articles.json` | Title, category and summary for each article. |
| `src/index.template.html` | The copy page. |
| `config.json` | `mintlify_base`, the live docs address, and `docs_dir`, the Mintlify project. |
| `build.py` | Builds `articles/` and `index.html`. |
| `articles/`, `index.html` | Build output. Commit it: GitHub Pages serves it. |

## Building

```bash
python build.py
```

The build needs the Mintlify project checked out at `docs_dir` (by default `../docs`). It fails if:

- a `{{MINTLIFY}}/<page>` link names a page that is not in the Mintlify navigation,
- an article contains an `<h1>`, a `class` attribute, a `<div>` or `<span>`, or a `<style>`,
  `<script>` or `<link>` tag. Articles use only headings, paragraphs, lists, tables, links, bold and
  code, which survive a formatted-text paste; HubSpot renders the title as the heading,
- an article contains a store address or a credential.

While `mintlify_base` is still the placeholder, the copy page shows a warning. Set it to the live
docs address and rebuild before anyone pastes.

## Changing an article

Work on a branch, edit `src/`, run `python build.py`, commit the source and the output together,
and open a pull request.
