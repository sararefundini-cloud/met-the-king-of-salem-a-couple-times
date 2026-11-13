# Source text

- File: `KJV.csv`
- Origin: [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases) `formats/csv/KJV.csv`
- URL used: https://raw.githubusercontent.com/scrollmapper/bible_databases/master/formats/csv/KJV.csv
- Retrieved: 2026-11-12
- SHA-256: a1051b4395bee78d01e239984425f3919563db5caee6fc162d4ddc7faff7eaa8
- Verses: 31,102 (66-book Protestant canon, header excluded)
- License: public-domain King James text (1769-style edition as distributed by that project)

## Typography notes

This CSV does **not** preserve the conventional small-caps **LORD** (Tetragrammaton) typography; almost all instances are plain `Lord`. Combined `Lord` + `LORD` totals still match the kjvindex cross-check.

Compound place names use an en-dash (U+2013), e.g. `Beth–el`, `Beer–sheba`. The build script joins these so they tokenize as `Bethel`, `Beersheba`, matching kjvindex and most printed KJV conventions.

Possessives use a typographic apostrophe (U+2019), e.g. `king’s`. Tokens are counted under the base word (`king`).

Psalm 119 section headings include a Hebrew letter plus its English name (`א ALEPH.`). Hebrew letters are not counted as words; the English names are.

One supplied word appears in brackets: 1 John 2:23 `[but]`. It is treated as the word `but`.

Spelling in this edition sometimes differs from kjvindex: `enquire` vs `inquire`, `Cesar` vs `Caesar`, `Judea` vs `Judaea`, `counsellors` vs `counsellers`.
