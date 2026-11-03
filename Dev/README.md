ND iTC GitHub hosted website for sharing additional information and training, https://ND-iTC.github.io.

## Editing the site

The home page, the Technical Decision pages, the NDcPP v4.0 dependency map, and the allowed-with list and training pages are generated. Do not edit their HTML by hand.

| To change | Edit | Then |
|---|---|---|
| A document, release, allowed-with list or resource | `data/site.json` | `python3 scripts/build.py` |
| Add a Technical Decision | append to `data/tds.json` (and add the PDF under `TD/<year>/`) | `python3 scripts/build.py` |
| Archive a Technical Decision | move its entry from `data/tds.json` to `data/tds_archived.json` | `python3 scripts/build.py` |
| The NDcPP v4.0 dependency map (after the cPP HTML changes) | `python3 scripts/extract_sfr_map.py` (reads `cPP/NDcPP_v4_0.html` Annex E and the SD HTML, writes `data/ndcpp_v4_sfr.json`) | `python3 scripts/build.py` |
| An allowed-with list or the training page | the `.adoc` file (`AWL/*.adoc`, `training/index.adoc`) | `python3 scripts/build.py` (needs `asciidoctor`) |
| The site navigation (left sidebar) | `NAV` in `scripts/build.py` | `python3 scripts/build.py` |
| Look and feel | `site.css`, `site.js`, `map.js` | none |

The build uses the Python standard library; the allowed-with list and training pages also need `asciidoctor` (if it is missing, those pages are left as they are). It writes `index.html`, `TD/tech_dec.html`, `TD/tech_dec_arch.html`, `map/ndcpp-4.0.html`, `AWL/*.html`, `training/index.html`, `feed.xml`, `sitemap.xml` and `data/tds.csv`, and stops if a Technical Decision PDF is missing. Commit the generated files.

`index.adoc`, `TD/tech_dec.adoc` and `TD/tech_dec_arch.adoc` are the previous AsciiDoc sources and are no longer used to build these pages.

The cPP, Supporting Document and PP-Module HTML files are the documents themselves and keep their own look. PDFs are the authoritative editions. `scripts/build.py` adds a light/dark toggle to those HTML files (`doc-theme.css`, `doc-theme.js`, injected before `</head>`; safe to rerun). If the documents are regenerated, run the build again to restore it.

`training/index.html` is kept but not linked from the site. `NDcPPv4.0_draft_comment_matrix.docx` is stored at the repository root for reference and is also not linked.

## Previewing changes

`scripts/make_dev.sh` builds a copy of the site as its own repository in `../ND-iTC-site-dev`, with a "DEVELOPMENT PREVIEW" banner and `noindex`, ready to push to `ND-iTC/ND-iTC-site-dev` and publish with GitHub Pages. Do not edit that copy by hand; rerun the script after each change.
