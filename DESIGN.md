# DESIGN.md

Design source of truth for **La causa científica**. Every page (the shell and each poem's `index.html`) follows this file. If a page needs something this file does not allow, change this file first.

## 1. Intent

A small literary press that publishes poems which happen to have code. The poem is the book; the code is the footnote. The site should feel like a publisher's catalogue (reference: Fitzcarraldo Editions): typographic, quiet, rigorous. It must not feel like a tech product or an AI tool.

## 2. What to avoid (the "not Claudesque" rules)

These are hard rules, not preferences.

- No cream, beige or warm-grey ground.
- No terracotta, sage or any earthy accent. One accent only (section 3).
- No rounded corners, pills, cards, shadows, gradients, glassmorphism.
- No emoji or decorative icons.
- No tracked, uppercase, monospace "kickers" or labels.
- No centred hero blocks, no taglines.
- No muted-grey body text. Secondary text is ink at smaller size, not paler.
- No sidebar chrome. The page is a single column under a masthead.
- Monospace never sets poem text.

## 3. Colour

| Token | Value | Use |
|---|---|---|
| `--paper` | `#fbfbf9` | Page background (near-white, not cream) |
| `--ink` | `#111111` | All text, rules, figure strokes |
| `--accent` | `#1d2fd1` | Links, active state, index numerals. Nothing else |
| `--rule` | `#111111` | 1px hairlines |

No dark mode. Contrast of text on paper must be at least 4.5:1.

Figures look like printed plates: ink and the single accent. The only exception is the N-terminus to C-terminus rainbow in *Versos proteics*, which stays inside its figure.

## 4. Typography

- **Serif (voice):** a contemporary text serif (Newsreader or Source Serif 4; final pick after the specimen). Used for titles, poem text, prose, the wordmark.
- **Grotesque (UI):** a neutral grotesque (Hanken Grotesk or Instrument Sans), small, sentence case. Used for the masthead links, metadata lines, captions, buttons.
- **Mono (machine):** IBM Plex Mono. Used only for code, sequences, data and other machine-produced text, set small. Not Space Mono.
- **Italics** (Newsreader italic), used the way a publisher does: roman for the names (titles, author), italic for the descriptive layer around them. Italic: one-line summaries, method and credit lines (`.sub`, e.g. *amb ESMFold*), figure captions, works cited and foreign words inside prose, emphasis inside poems. Roman: titles, author names, poem text by default, numerals. Never bold for emphasis in running text; never italic for UI labels, links in the masthead, or machine text.
- Rule: serif for what is read, mono for what the machine produced. Never both at full size on one line.
- Scale: title `clamp(2.5rem, 6vw, 5rem)` weight 400, tight leading (1.05); poem text 1.25rem/1.6; prose 1.125rem/1.6; UI 0.875rem; mono 0.8125rem.
- Required glyphs (check in every font): `l·l`, `ŀ`, `à è é í ò ó ú ï ü ç`, `« »`, `—`.
- Fonts are vendored as base64 `woff2` (latin + latin-ext subsets) so each `index.html` stays self-contained, with no external requests (see `CONVENTIONS.md`).

## 5. Layout

- One column under a masthead. Generous margins: 24px on phones, 6vw on desktop.
- 12-column grid. Poem text measure about 34em; prose about 38em; figures may span the full width.
- Masthead: wordmark "La causa científica" on the left (serif), links on the right ("Sobre el projecte"), one 1px rule below. No other chrome.
- Vertical rhythm in multiples of 8px. Hairlines separate sections; there are no boxes.

## 6. Home (catalogue)

- Short intro paragraph in Catalan (two or three sentences) above the list.
- One row per poem, in `order:` sequence: numeral (accent, grotesque), large serif title, and the italic one-line `summary:` from `metadata.yml`. Hairline between rows.
- No dates, no tags. Hover and focus: title turns accent. No motion.
- A separate page, "Sobre el projecte": method, tools, credits.

## 7. Poem page

- Large serif title; one small grotesque line below it (author, kind of computation if useful).
- If the piece has several views (for example El poema / El mapa / Metodologia), they appear as a plain text row under the title; the current one is accent with a 1px underline.
- Order: the poem, then a quiet "Com està fet" section with mono code and figures.
- The shell shows the poem full width in an iframe; the page has no rail of its own.

## 8. Motion and accessibility

- Visible focus outlines (2px accent, offset 2px). Never remove them.
- Scrollbars are the browser default.
- Respect `prefers-reduced-motion`. Allowed motion: a 150ms fade between poems.
- Keyboard: `j`/`k` next/previous piece, `←`/`→` previous/next view inside a piece (its `.subnav`), `Esc` back to the index. Keys pressed inside a piece are forwarded to the shell by `shared/design/nav.html`. The shortcuts are listed on the "Sobre el projecte" page. Everything is also reachable with Tab and real links.
- The browser Back button must work (history entries per poem).

## 9. Copy

- UI text in Catalan, plain and short. Poems in Catalan. Code and code docs in English.
- Name everywhere: **La causa científica**.
- Sentence case. No exclamation marks.

## 10. Implementation notes

- Tokens and base styles live in `shared/design/` (`tokens.css`, `base.css`) and are inlined into every page by the build scripts. Do not copy them into poem templates.
- Per-poem CSS only covers that poem's figures and interactions.
- Old values (`#f0ebe6`, `#c7513b`, `#2f7d68`, Space Mono) must not reappear.

## 11. Social visuals and link previews

Generated, never hand-made: `python scripts/make_social.py` renders HTML cards in this same design with headless Chrome and writes PNGs to `social/` (committed). Titles and summaries come from `metadata.yml`.

- Poem cards are paper with ink type and a blue numeral: title in large serif anchored low, italic summary, hairlines, author and URL in the grotesque. The collection card, avatar and banner are the one place the blue is used as a full field, with paper-coloured type.
- Formats: `og/` 1200x630 (link previews), `square/` 1080x1080 (feed posts), `story/` 1080x1920, `verse/` 1080x1080 (only for poems that define `excerpt:` lines in `metadata.yml`), `brand/` (avatar, banner, favicon, touch icons).
- The site build copies them next to each page and adds Open Graph and Twitter tags (`site/build_site.py`). A poem URL opened directly redirects into the shell.
- Same rules as the site: no photos, no decoration, one accent. Long titles shrink to fit and wrap; they are never cropped.

