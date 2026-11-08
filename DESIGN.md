# DESIGN.md

The design of **La causa científica**: a small literary press that publishes poems which happen to have code.

This file is the single source of truth. Every page (the shell and each poem's `index.html`), every social card and every future piece follows it. If something here is wrong or missing, change this file first, then the code.

**Reference:** Fitzcarraldo Editions. Typographic, quiet, rigorous. **Anti-reference:** a tech product, an AI tool, a blog template.

---

## Part I. Principles

Twelve principles. Each one says what to do, why, and what it looks like in practice. When two details conflict, the lower number wins.

### 1. The poem is the book; the code is the footnote
The text comes first and is the largest thing on the page. Code, methods and figures sit after it, smaller and quieter, under a "Com està fet" or "Metodologia" heading.
*In practice:* title, then the poem, then the method. Never open a piece with tooling.

### 2. Type does the work; nothing is decoration
Hierarchy comes from size, weight, spacing and hairlines. There are no icons, cards, shadows, gradients, illustrations or ornaments.
*In practice:* if a layout feels empty, add space or a better headline, not a graphic.

### 3. One paper, one ink, one accent
Near-white paper, near-black ink, one ultramarine blue. The blue marks the one thing that is active or numbered: a link, the current view, an index numeral, a live reading in a figure.
*In practice:* if you reach for a second colour, the structure is wrong.

### 4. Roman by default; italics always mean something
Italics are not a style layer. They are for scientific names (*Podarcis muralis*), titles of cited works (*Veinte poemas de amor…*), a word the sentence stresses, or a quoted foreign phrase. Summaries, subtitles, credit lines, captions, glosses, labels, language names and software names are roman. Never bold for emphasis in running text.
*In practice:* before italicising anything, name which of the four reasons applies. If none does, leave it roman.

### 5. Three voices, never mixed
- **Serif** is what is read: titles, poems, prose, the wordmark.
- **Grotesque** is what operates: menus, controls, labels, metadata.
- **Mono** is what the machine produced: code, sequences, data. Never poem text.

*In practice:* a line never sets serif and mono at the same large size.

### 6. One column, hairlines instead of boxes
A masthead, then one column. Sections are separated by 1px ink rules and white space. There is no sidebar and nothing sits in a box.
*In practice:* group with space, divide with a rule, never with a border-radius.

### 7. Everything scales; mobile is not an afterthought
All sizes are in `rem`, `em`, `%` or `clamp()`. The design is built for a phone first and scales up: the whole page grows on large monitors. Nothing is ever clipped or scrolled sideways to fit: verses wrap, tables of data wrap or fit, the one allowed exception is a code or sequence block that scrolls inside itself.
*In practice:* check 320, 390, 768, 1024, 1440 and 2560 px, in portrait and landscape.

### 8. The first screen shows the thing
Whatever the piece is (a poem, a map, a molecule) must be visible, or clearly reachable, without scrolling past a wall of chrome. Chrome is thin; on phones it gets out of the way while you read.
*In practice:* masthead plus piece bar stay under about 90px on a phone; the masthead tucks away on scroll down.

### 9. Touch and keyboard are first-class
Every control has a hit area of at least 44px on touch devices without looking bigger. Everything works with a keyboard, with a visible focus ring. Hover is an enhancement, never the only way.
*In practice:* use `a::after { inset: -10px }` hit areas; never remove outlines.

### 10. Motion is quiet and optional
Allowed: a 150ms fade between pieces, a piece's own animation (a map drawing, a word darkening). Nothing bounces, slides or parallaxes. `prefers-reduced-motion` turns animation off or shows its final state.
*In practice:* if the page works with all animation removed, it is right.

### 11. Self-contained and fast
Every piece is one `index.html` with fonts, CSS, data and scripts inlined. No external requests, no trackers, no CDN. Generated assets (fonts, social cards) are committed so the site builds without special tools.
*In practice:* open the file from disk; it must look identical.

### 12. One source of truth; never copy
Tokens and base styles live in `shared/design/` and are inlined into every page by `shared/design/inline.py`. A piece's own CSS covers only its own figures and interactions.
*In practice:* if you are about to paste a colour, a font size or a menu style into a poem's template, put it in `shared/design/` instead.

---

## Part II. What never appears

Hard rules. They exist because the previous design looked like a generic AI-tool theme.

- No cream, beige or warm-grey ground; no terracotta, sage or other earthy accent.
- No rounded corners, pills, cards, shadows, gradients, glassmorphism.
- No emoji, no decorative icons, no stock imagery.
- No tracked, uppercase, monospace "kickers" or labels.
- No centred hero blocks, no taglines, no marketing copy.
- No muted-grey body text: secondary text is ink at a smaller size, never paler.
- No sidebars or other persistent chrome beyond the masthead and the piece bar.
- No dark mode (the paper identity is fixed).
- No Space Mono, and none of the old values (`#f0ebe6`, `#c7513b`, `#2f7d68`).
- No exclamation marks, no emojis in copy, no "Welcome to…".

---

## Part III. Specification

### Colour

| Token | Value | Use |
|---|---|---|
| `--paper` | `#fbfbf9` | Page background |
| `--ink` | `#111111` | All text, rules, figure strokes |
| `--accent` | `#1d2fd1` | Links on hover/active, current view, numerals, live readings, social blue field |
| `--rule` | `#111111` | 1px hairlines |

Text on paper meets 4.5:1 contrast. Figures look like printed plates: ink and the accent, with the faint ink tint `rgba(17,17,17,.035)` for land or fills. The one exception is the N-to-C rainbow in *Versos proteics*, which stays inside its 3D figure.

### Typography

| Role | Family | Used for |
|---|---|---|
| Serif | Newsreader (variable, optical size, 300–600) | Titles, poems, prose, wordmark |
| Grotesque | Hanken Grotesk (400–600) | Menus, labels, numerals, captions, controls |
| Mono | IBM Plex Mono (400) | Code, sequences, data |

- Scale: page title `clamp(2.5rem, 5.2vw, 4rem)`, weight 400, leading 1.04, tracking -0.02em; poem text 1.25rem/1.6; prose 1.125rem/1.6 (1.25rem on piece pages); UI 0.875rem; captions 0.8125rem; mono 0.8125rem.
- Measures: poem text about 34em; prose about 38em; figures may use the full width.
- Required glyphs in every font: `l·l`, `ŀ`, `à è é í ò ó ú ï ü ç`, `« »`, `—`.
- Apostrophes are typographic (’). `shared/design/nav.html` converts straight apostrophes between letters at load, outside code and data.
- Fonts are vendored as base64 `woff2` (latin and latin-ext subsets) in `shared/design/fonts.css`, generated by `shared/design/build_fonts.py`.

### Layout and responsiveness

- **Edge:** `--edge = max(6vw clamped 24–96px, (100vw − 80rem)/2, safe-area insets)`. The masthead, the piece bar, the catalogue and every piece use the same edge so everything aligns.
- **Scale up:** root font size is 100% below 1800px, 112.5% from 1800px, 131.25% from 2300px. Because everything is in rem, the whole design grows.
- **Breakpoints** (content adapts; nothing is hidden):
  - up to 380px: the masthead drops the duplicate "Peces" link.
  - up to 640px: compact masthead, two-column piece bar, smaller numeral column.
  - up to 640px: the title block is compact (title `clamp(2rem, 9.5vw, 2.75rem)`, smaller author and descriptor lines).
  - up to 760px: the piece's menu wraps; verses wrap with a hanging indent instead of scrolling; multi-column layouts stack to one column.
  - landscape phones (height up to 520px): the masthead is hidden inside a piece and the title block shrinks.
- **Phones in a piece:** the masthead tucks away when scrolling down and returns on scroll up (the iframe reports scroll direction to the shell).
- Vertical rhythm in multiples of 8px; use `clamp()` for large gaps.

### Components (shared vocabulary in `shared/design/base.css`)

`.page` container · `.head` title block (`.title`, `.by` author, `.sub` plain descriptor) · `.subnav` text menu of views (current: accent + 1px underline) · `.verse` poem text (`.v` line, `.br` stanza gap) · `.prose` running text · `.label` small bold grotesque heading · `.how` "Com està fet" section (hairline above) · `.code` / `pre` machine text · `.fig` + `.cap` figure and caption · `.hair` rule · `.standalone` bar shown only when a page is opened outside the shell.

### Shell (home, about, piece)

- **Masthead:** wordmark left (links home), "Peces" and "Sobre el projecte" right, one rule under.
- **Home:** one short Catalan intro, then the catalogue: per row a blue numeral, a large serif title and the roman one-line `summary:`; hairlines between rows. Hover and focus turn the title blue. Catalogue links are real URLs (`slug/`) that the page routes by hash.
- **About ("Sobre el projecte"):** a few plain paragraphs, then the keyboard shortcuts.
- **Piece view:** a bar (`← Totes les peces`, `03 / 06`, `← Anterior  Següent →`) above the piece's iframe. The piece fills the window; the browser Back button steps through pieces.
- **Footer:** author and GitHub link on a rule.

### Piece pages

1. Title block: the piece's name, the author, one plain line describing it.
2. The text menu of views (for example "El poema / Metodologia"), the current one in accent.
3. The poem or main view. Methodology and code come last, under a hairline.
4. If a piece has sub-poems (as *Versos proteics* does), each gets its own large heading under the page title.

### Keyboard and links

`j` / `k` next and previous piece · `←` / `→` previous and next view inside a piece · `Esc` back to the index. Keys pressed inside a piece are forwarded to the shell by `shared/design/nav.html`. A skip link jumps to the content. Everything is also reachable with Tab and plain links. Opening a poem's own URL redirects into the shell.

### Copy

Catalan for all UI text and poems; English for code and code docs. Sentence case. Short and plain. The name is **La causa científica** everywhere.

### Social visuals and link previews

Generated, never hand-made: `python scripts/make_social.py` renders HTML cards in this same design with headless Chrome into `social/` (committed). Titles and summaries come from `metadata.yml`.

- Poem cards are paper with ink type and a blue numeral: large serif title anchored low, roman summary, hairlines, author and URL in the grotesque. The collection card, avatar and banner use the blue as a full field with paper-coloured type: the only place the accent is a background.
- Formats: `og/` 1200×630, `square/` 1080×1080, `story/` 1080×1920, `verse/` 1080×1080 (only for poems with `excerpt:`), `brand/` (avatar, banner, favicon, touch icons).
- The build copies them next to each page and adds Open Graph and Twitter tags (`site/build_site.py`).
- Long titles shrink to fit and wrap; they are never cropped.

---

## Part IV. How to work with this design

### Adding or changing a piece
1. Copy `_template/poem/` or run `python scripts/new_poem.py "Títol"`. Fill `metadata.yml` including `summary:` (and `excerpt:` if you want a verse card).
2. Build the page with the shared pieces: `design_css()`, `nav_script()` and `standalone_bar()` from `shared/design/inline.py`, in a `_TEMPLATE` string with `{{DESIGN}}`, `{{STANDALONE}}`, `{{NAV}}`. See `content/llangardaix-extingit/code/build_web.py` for the smallest example.
3. Rebuild the page (`code/build_web.py`), the site (`python site/build_site.py`) and, if titles changed, the social cards.

### Before you ship: checklist
- [ ] No horizontal scroll at 320, 390, 768, 1024, 1440, 2560 px, portrait and landscape.
- [ ] First screen shows the piece, not only chrome (phone: chrome under about 90px).
- [ ] Every control is at least 44px to hit on touch, and has a visible keyboard focus.
- [ ] No italics unless one of the four reasons in Principle 4 applies.
- [ ] Only paper, ink and the one accent (plus the one rainbow exception).
- [ ] No mono in poem text; no serif and mono at full size on one line.
- [ ] Works with `prefers-reduced-motion` and without hover.
- [ ] No external requests; the file works opened from disk.
- [ ] Catalan glyphs render (`l·l`, `ŀ`, `« »`, accents); apostrophes are ’.
- [ ] Back button, `j`/`k`/`Esc` and the previous/next links behave inside the shell.
- [ ] No console errors.

### Where things live
`shared/design/` tokens, base, fonts, nav script, inliner · `site/` shell templates and build · `content/<slug>/code/build_web.py` each piece · `scripts/make_social.py` and `social/` the share cards · `CONVENTIONS.md` the repo-level contract.
