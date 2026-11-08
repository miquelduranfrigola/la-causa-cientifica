# La causa científica

An expanded universe for the book *La causa científica* (Miquel Duran-Frigola, La Segona Perifèria): poems and graphic pieces made computationally, each with its method and its place in the printed book.

**Website: https://miquelduranfrigola.github.io/la-causa-cientifica/**

Each piece lives in `content/<slug>/` with its text, its Python code and a self-contained page. The site is static and is published with GitHub Pages. Poems and site text are in Catalan; code and code documentation are in English.

## Repository layout

| Path | What it holds |
| --- | --- |
| `content/<slug>/` | One folder per piece: `poem.md`, `metadata.yml`, `code/`, `data/`, `results/`, `index.html` (the page) |
| `book/` | The printed book: configuration, the facsimile pages the pieces point to |
| `shared/design/` | The design layer (tokens, base CSS, fonts, keyboard script) inlined into every page |
| `site/` | The static site generator (`build_site.py`, templates, styles) |
| `scripts/` | `new_poem.py`, `check_design.py`, `make_social.py`, `make_book_pages.py`, `fetch_assets.py` |
| `social/` | Generated share cards and icons |
| `_template/poem/` | Skeleton copied by `new_poem.py` |

Specifications: [`DESIGN.md`](DESIGN.md) (visual rules), [`CONVENTIONS.md`](CONVENTIONS.md) (folder and file standard), [`book/README.md`](book/README.md) (how a piece maps to the book).

## Usage

```bash
pip install -r site/requirements.txt
python site/build_site.py          # builds the site into _site/
python scripts/check_design.py     # checks DESIGN.md rules (also runs in CI)
python scripts/new_poem.py "Títol del poema"
python scripts/make_book_pages.py  # renders the book pages each piece cites (needs the book PDF)
```

Large files are not stored in git. They are listed in `drive-manifest.yml` files and fetched with `scripts/fetch_assets.py`.

## License

GNU General Public License v3.0. See [`LICENSE`](LICENSE).
