# webcommander-docs-kb

Paste-ready HubSpot knowledge base articles for the WebCommander API and SDKs, and a page that
lets you copy each one. The full reference lives on the Mintlify site; every article links to it.

## Using the copy page

Open the published page (GitHub Pages), pick an article, click **Copy HTML**, then in HubSpot:

1. Open the article and set its title to the one shown on the page.
2. In the body toolbar, open **Source code**.
3. Paste, save, then preview before you publish.

Paste into the source code view, not the visual editor, or HubSpot re-tags the markup.

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
- an article contains an `<h1>`, a `class` attribute, or a `<style>`, `<script>` or `<link>` tag
  (HubSpot keeps inline styles only and renders the title as the heading),
- an article contains a store address or a credential.

While `mintlify_base` is still the placeholder, the copy page shows a warning. Set it to the live
docs address and rebuild before anyone pastes.

## Changing an article

Work on a branch, edit `src/`, run `python build.py`, commit the source and the output together,
and open a pull request.
