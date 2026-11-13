# How much does *The Alchemist* draw on Genesis, Exodus, and Leviticus?

All figures below were computed from the cleaned texts in this run. They are not estimates.

## What was compared

| Text | What was counted | Tokens (all words) | Word types | Non-stopword tokens | Non-stopword types |
|---|---|---:|---:|---:|---:|
| *The Alchemist* (Paulo Coelho) | Prologue through Epilogue. Title page, table of contents, the “Ten Years On” introduction, and publisher back matter were removed. | 39,608 | 3,326 | 17,246 | 3,167 |
| *The Great Gatsby* (F. Scott Fitzgerald, 1925; Project Gutenberg #64317) | Body text between the Gutenberg start and end markers. | 49,173 | 6,087 | 23,825 | 5,922 |
| *The Thirty-Nine Steps* (John Buchan, 1915; Project Gutenberg #558) | Same Gutenberg stripping. | 41,677 | 5,303 | 18,547 | 5,143 |
| King James Version | 31,102 verses; 790,882 tokens; 12,559 types. Genesis 38,262 tokens (2,447 types); Exodus 32,686 (2,020); Leviticus 24,541 (1,410). | 790,882 | 12,559 | — | — |

The two novels are the baseline: twentieth-century public-domain fiction of similar length, not biblical retellings. *The Economy of God* (Witness Lee, 1964; 74,454 tokens after dropping the table of contents and endnotes) is a scripture-teaching book and is quoted only as a high-overlap reference point, not as a “neutral” baseline.

Words were lowercased, possessives were reduced to the base word, and typographic dashes and apostrophes were normalized the same way as in the KJV inventory. Stopwords are the same function-word list used there (articles, pronouns, auxiliaries, and KJV particles such as *unto* and *thou*).

## Distinctiveness versus general modern English (lead measure)

The question “how much does *The Alchemist* draw on Genesis?” is easy to get wrong if every word that happens to occur in Genesis is treated as a Genesis word. Everyday narrative English already sits in Genesis, which is why *The Great Gatsby* can look similar to *The Alchemist* under that older measure (see the appendix below). This section uses a **distinctiveness** test against a large general-English frequency list instead.

A content word is *distinctly Genesis* (and, separately, distinctly Exodus or Leviticus) when both of the following hold, or when it is accepted as a proper name of that book:

1. It occurs at least **3** times in that biblical book.
2. Its smoothed log-odds versus **wordfreq 3.1.1 English** (treated as a 1-billion-word reference, the same scale zipf frequencies are defined on) is at least **4.0**. The rate ratio with the same +0.5 smoothing is also stored. The cutoff was set by inspecting the score distribution: it admits *flock* (Genesis log-odds 4.35), *cattle* (4.60), *altar* (4.02), *pharaoh* (7.08), and *begat*-class vocabulary, and it rejects ordinary narrative words such as *son* (3.09), *land* (3.39), *came* (2.69), and *man* (1.56).

Proper names are added even when they miss the count or the log-odds bar. A mid-verse capitalized token (not the first word of the verse, and not the first word after a comma or sentence stop — KJV capitalizes speech that way) is treated as a name if at least 80% of its occurrences in that book are capitalized, the word is at least three letters, and either (a) it occurs mid-verse at least twice and has wordfreq zipf < 4.5, or (b) mid-verse at least twice, zipf ≥ 4.5, and log-odds ≥ 2.5, or (c) it is a hapax-like name with zipf < 3.5. Condition (b) is what keeps *Jordan* off the Genesis list: including it would have counted Jordan Baker 72 times in *The Great Gatsby*. *Israel* (zipf 4.77, log-odds 2.94) and *Adam* (4.57, 2.57) still qualify. *Salem*, *Melchizedek*, and *Potiphar* are force-included so the named allusions in the novel cannot fall out as hapaxes.

The resulting lists have **555** distinctly Genesis types (281 by log-odds, of which 117 are also names; 274 names-only), **307** distinctly Exodus types, and **205** distinctly Leviticus types. A word that qualifies for more than one list is assigned to **one** exclusive bucket, in order Genesis → Exodus → Leviticus, so tokens are not double-counted on the stacked bar. *Egypt* and *pharaoh* therefore count as Genesis. *Tent* just misses the Genesis cutoff (log-odds 3.96) and is assigned to Exodus (4.36).

Rates are per 10,000 **content** (non-stopword) tokens. The chart is `output/alchemist_genesis_distinct.png`. The per-word table, with biblical counts, log-odds, rate ratios, zipf, and counts in all four texts, is `output/distinct_genesis.csv` (899 union types).

| Text | Content tokens | Distinct-Genesis types (tokens, rate/10k) | Distinct-Exodus types (tokens, rate/10k) | Distinct-Leviticus types (tokens, rate/10k) | Combined types (tokens, rate/10k) |
|---|---:|---:|---:|---:|---:|
| *The Alchemist* | 17,246 | 23 (111, 64.36) | 17 (89, 51.61) | 7 (20, 11.60) | 47 (220, 127.57) |
| *The Great Gatsby* | 23,825 | 18 (30, 12.59) | 17 (37, 15.53) | 9 (18, 7.56) | 44 (85, 35.68) |
| *The Thirty-Nine Steps* | 18,547 | 25 (54, 29.12) | 12 (30, 16.18) | 11 (20, 10.78) | 48 (104, 56.07) |
| *The Economy of God* | 31,347 | 44 (328, 104.64) | 50 (926, 295.40) | 25 (367, 117.08) | 119 (1,621, 517.11) |

*The Alchemist* uses distinctly Genesis words at **64.36** per 10k content tokens, about five times *The Great Gatsby* (**12.59**) and a little more than twice *The Thirty-Nine Steps* (**29.12**). Combined Torah-distinct rates: **127.57** vs **35.68** vs **56.07**. *The Economy of God* is much denser (**517.11**), as expected in a book of Bible teaching. 476 of its 926 exclusive-Exodus tokens are *lord*, which passes the Exodus log-odds cutoff (4.60) because LORD is so frequent there; excluding *lord*, its Exodus rate is 143.55 and its combined rate is 365.27 — still well above the novel.

### Distinct-Genesis words in *The Alchemist*, with Gatsby’s count

The novel uses **23** distinct-Genesis types, fewer than 30, so the table is complete rather than a top-30 cut.

| Rank | Word | Alchemist | Gatsby | Thirty-Nine Steps | Economy of God | Genesis log-odds | Included as |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | flock | 22 | 1 | 0 | 0 | 4.35 | log-odds |
| 2 | egypt | 20 | 0 | 0 | 18 | 4.28 | log-odds and name |
| 3 | salem | 11 | 0 | 0 | 0 | 2.06 | proper name |
| 4 | dreamed | 9 | 1 | 0 | 0 | 4.21 | log-odds |
| 5 | awoke | 8 | 2 | 1 | 0 | 4.42 | log-odds |
| 6 | camels | 8 | 0 | 0 | 0 | 5.73 | log-odds |
| 7 | servants | 5 | 7 | 7 | 3 | 4.60 | log-odds |
| 8 | wept | 5 | 1 | 0 | 1 | 5.38 | log-odds |
| 9 | melchizedek | 4 | 0 | 0 | 0 | 5.67 | proper name |
| 10 | egyptian | 3 | 0 | 0 | 5 | 2.49 | proper name |
| 11 | famine | 2 | 0 | 0 | 0 | 5.06 | log-odds |
| 12 | joseph | 2 | 0 | 0 | 0 | 4.83 | log-odds and name |
| 13 | sons | 2 | 0 | 1 | 2 | 4.80 | log-odds |
| 14 | abraham | 1 | 0 | 0 | 1 | 5.91 | log-odds and name |
| 15 | daughters | 1 | 0 | 0 | 0 | 4.47 | log-odds |
| 16 | egyptians | 1 | 0 | 0 | 0 | 4.74 | log-odds and name |
| 17 | flocks | 1 | 0 | 0 | 0 | 6.39 | log-odds |
| 18 | fowl | 1 | 0 | 0 | 0 | 6.07 | log-odds |
| 19 | lad | 1 | 0 | 0 | 0 | 4.11 | log-odds |
| 20 | pharaoh | 1 | 0 | 0 | 5 | 7.08 | log-odds and name |
| 21 | sacks | 1 | 0 | 4 | 0 | 4.16 | log-odds |
| 22 | serpent | 1 | 0 | 0 | 21 | 4.08 | log-odds |
| 23 | servant | 1 | 1 | 6 | 1 | 4.53 | log-odds |

*Servants* is the one high-count Genesis-list word that the baseline novels use as much as, or more than, *The Alchemist*; it is slightly over-represented in Genesis versus modern English, but it is also ordinary period-novel diction. The named allusions are not: *salem* 11, *melchizedek* 4, *egypt* 20, *joseph* 2, *pharaoh* 1, and *abraham* 1, all with Gatsby count 0.

Exclusive-Exodus tokens in the novel: *tent* 31, *urim* 15, *thummim* 15, *breastplate* 6, *horsemen* 6, *midst* 3, *lord* 2, *reared* 2, and one each of *cloths, curtain, garments, jewels, lamps, linen, rings, shone, spices*. Exclusive-Leviticus: *tenth* 9, *priest* 4, *eaten* 2, *pronounce* 2, and one each of *cleanse, offering, reddish*.

Thirty-one of the 47 distinct-Torah types the novel uses also appear in at least one of the other three texts. Shared distinct-Genesis words with counts in two or more of the four texts include *flock* (Alchemist 22, Gatsby 1), *egypt* (Alchemist 20, Economy 18), *dreamed* (Alchemist 9, Gatsby 1), *awoke* (Alchemist 8, Gatsby 2, Steps 1), *servants* (5 / 7 / 7 / 3), *wept* (5 / 1 / 0 / 1), *egyptian* (3 / 0 / 0 / 5), *pharaoh* (1 / 0 / 0 / 5), *abraham* (1 / 0 / 0 / 1), and *serpent* (1 / 0 / 0 / 21). The full shared list is in the CSV (`n_of_4_books` ≥ 2).

A unigram list still has collisions: *servants*, *bare*, *tenth*, and *lord* can be used in a modern sense. That is why the named allusions remain the strongest evidence, and why the rates are a contrast with the baselines, not a source citation.


## Appendix: the older “any appearance in Genesis” measure (why it was misleading)

Each non-stopword word type is placed in **one** exclusive bucket, in this order:

1. **Genesis** — the word occurs at least once in Genesis (it may also occur later).
2. **Exodus** — occurs in Exodus, but not in Genesis.
3. **Leviticus** — occurs in Leviticus, but not in Genesis or Exodus.
4. **rest of OT** — occurs somewhere in the Old Testament, but not in those first three books.
5. **NT only** — occurs in the New Testament and nowhere in the Old Testament.
6. **not in KJV** — does not occur in the KJV at all.

A second, **cumulative** view is also reported: the share of words that appear *anywhere* in Genesis, *anywhere* in Exodus, *anywhere* in Leviticus, in the first three books combined, in the OT, or in the KJV at all. Cumulative figures for Exodus and Leviticus are larger than the exclusive buckets, because many words that first appear in Genesis also appear in those later books.

This is the measure that made *The Great Gatsby* look similar to *The Alchemist*. A word was called a Genesis word if it occurred in Genesis even once, including ordinary narrative English (*man*, *son*, *night*, *day*). Under it, exclusive Genesis type shares were 25.20% in *The Alchemist* vs 14.30% in *The Great Gatsby* and 16.82% in *The Thirty-Nine Steps*; exclusive Genesis token shares were 49.74% vs 40.06% vs 43.21% — close enough to be misleading. The distinctiveness rates above (64.36 vs 12.59 vs 29.12 per 10k content tokens) are the replacement. The six-bucket tables and `output/alchemist_genesis.png` are kept as a record of the older calculation, not as the lead visual.

These percentages do **not** prove that Coelho used the King James text specifically. They measure whether *The Alchemist*’s English vocabulary is also found in those books.

## Vocabulary shares (non-stopword types)

Exclusive buckets:

| Source bucket | *The Alchemist* | *The Great Gatsby* | *The Thirty-Nine Steps* |
|---|---:|---:|---:|
| Genesis | 25.20% (798 types) | 14.30% (847) | 16.82% (865) |
| Exodus | 5.59% (177) | 4.17% (247) | 4.82% (248) |
| Leviticus | 1.71% (54) | 1.25% (74) | 1.57% (81) |
| rest of OT | 18.60% (589) | 14.47% (857) | 16.20% (833) |
| NT only | 5.08% (161) | 3.97% (235) | 4.51% (232) |
| not in KJV | 43.83% (1,388) | 61.84% (3,662) | 56.08% (2,884) |

Cumulative (“found in … at all”):

| Found in | *The Alchemist* | *The Great Gatsby* | *The Thirty-Nine Steps* |
|---|---:|---:|---:|
| Genesis | 25.20% | 14.30% | 16.82% |
| Exodus | 22.20% | 13.12% | 15.40% |
| Leviticus | 15.69% | 9.15% | 10.87% |
| Genesis, Exodus, or Leviticus | 32.49% | 19.72% | 23.22% |
| Old Testament | 51.09% | 34.19% | 39.41% |
| KJV at all | 56.17% | 38.16% | 43.92% |

*The Alchemist* has a clearly higher share of its content vocabulary in Genesis, and in the KJV, than either baseline novel. The gap is about 9–11 percentage points on exclusive Genesis types, and about 12–18 points on “in the KJV at all.” For comparison, *The Economy of God* — a book of Bible messages — has 22.66% exclusive Genesis types and 56.15% of types in the KJV, almost the same type-level KJV overlap as *The Alchemist*. That is striking for a modern novel, but it is still a vocabulary statistic, not a source citation.

## Running text (non-stopword tokens)

Exclusive buckets:

| Source bucket | *The Alchemist* | *The Great Gatsby* | *The Thirty-Nine Steps* |
|---|---:|---:|---:|
| Genesis | 49.74% (8,579 tokens) | 40.06% (9,545) | 43.21% (8,015) |
| Exodus | 5.76% (994) | 5.10% (1,215) | 4.93% (914) |
| Leviticus | 0.92% (159) | 1.06% (252) | 1.30% (241) |
| rest of OT | 15.06% (2,598) | 12.73% (3,032) | 13.84% (2,566) |
| NT only | 2.71% (467) | 2.74% (653) | 2.78% (516) |
| not in KJV | 25.80% (4,449) | 38.31% (9,128) | 33.94% (6,295) |

Cumulative token shares: *The Alchemist* has 49.74% of content tokens occurring in Genesis, 71.49% in the OT, and 74.20% in the KJV. Gatsby: 40.06% / 58.95% / 61.69%. *The Thirty-Nine Steps*: 43.21% / 63.28% / 66.06%.

Token shares are always higher than type shares because frequent everyday words (*man*, *son*, *night*, *day*, and so on) sit in Genesis. The baseline novels show the same inflation, which is why they are there. Even so, *The Alchemist* remains several points above both baselines on Genesis tokens, and about 8–12 points above them on “in the KJV at all.” Leviticus is the weak layer in running text: only 0.92% of *The Alchemist*’s content tokens fall in the exclusive-Leviticus bucket, less than in either baseline.

The older six-bucket stacked bar chart is at `output/alchemist_genesis.png`. The lead chart is `output/alchemist_genesis_distinct.png`.

## Older log-odds versus the two-novel baseline (not the lead list)

A earlier pass scored every Alchemist content word that occurs in Genesis, Exodus, or Leviticus against the **combined two-novel baseline** (90,850 tokens) rather than against general English. That is a useful contrast with Fitzgerald and Buchan, but it is not the distinctiveness list used in the chart and table above (those use wordfreq). A high score here means the word is more characteristic of that biblical book than of those two novels. It does not, by itself, mean Coelho “got the word from” that book.

**Top distinctly Genesis words** (word, Alchemist count, Genesis count, baseline count, log-odds, rate ratio):

- joseph (2, 157, 0, 6.62, 748)
- abraham (1, 134, 0, 6.46, 639)
- pharaoh (1, 94, 0, 6.11, 449)
- egypt (20, 77, 0, 5.91, 368)
- daughters (1, 63, 0, 5.71, 302)
- sons (2, 146, 1, 5.45, 232)
- pray (3, 48, 0, 5.44, 230)
- famine (2, 24, 0, 4.76, 116)
- flocks (1, 24, 0, 4.76, 116)
- camels (8, 23, 0, 4.72, 112)
- bury (1, 15, 0, 4.30, 74)
- destroy (1, 15, 0, 4.30, 74)
- egyptians (1, 13, 0, 4.16, 64)
- angel (9, 11, 0, 4.00, 55)

Several of these are genuine allusions: the novel names Joseph and Abraham, retells Pharaoh’s dream of lean and fat cows, and sends the boy toward Egypt. *Flocks*, *camels*, and *famine* fit the same world. Others (*sons*, *daughters*, *pray*, *meat*, *destroy*) are simply more common in Genesis than in Fitzgerald or Buchan; they should not be over-read.

**Top distinctly Exodus words:**

- egypt (20, 122, 0, 6.53, 681)
- pharaoh (1, 115, 0, 6.47, 642)
- holy (1, 55, 0, 5.73, 309)
- egyptians (1, 53, 0, 5.70, 297)
- offering (1, 49, 0, 5.62, 275)
- rings (1, 38, 0, 5.37, 214)
- serve (5, 25, 0, 4.95, 142)
- breastplate (6, 23, 0, 4.87, 131)

*Egypt* and *pharaoh* are shared with Genesis (they are classified in the exclusive Genesis bucket, but they also have a strong Exodus rate). *Breastplate* is the stand-out Exodus-specific hook: it appears 6 times in the novel, 23 times in Exodus, and never in the baseline novels.

**Top distinctly Leviticus words:**

- offering (1, 249, 0, 7.53, 1,847)
- holy (1, 94, 0, 6.55, 700)
- priest (4, 185, 1, 6.13, 458)
- meat (1, 41, 0, 5.73, 307)
- pronounce (2, 22, 0, 5.12, 167)
- seventh (1, 20, 0, 5.02, 152)

These scores are high because Leviticus repeats ritual vocabulary that almost never appears in the baseline novels. In *The Alchemist* the same words are rare (*offering* once, *holy* once). They are a lexical shadow of priestly language, not a Leviticus plot. The honest Leviticus hook in the novel is *Urim*, *Thummim*, and *breastplate*, not *offering* or *seventh*.

The full per-word table is `compare/alchemist_genesis.csv` (3,167 non-stopword types).

## Shared n-grams (2–5 words) with Genesis, Exodus, and Leviticus

Many shared n-grams are ordinary English (“on the first day”, “father and his mother”). Those do not show dependence. The phrases below are the ones that actually point at the books in question. Counts are raw n-gram occurrences; refs are the first KJV hits.

**Genesis**

- “king of salem” — 5 times in *The Alchemist*; once in Genesis, at Genesis 14:18.
- “flocks of sheep” — 1 / 1, Genesis 29:2.
- “to the well”, “at the well”, “the well to” — several times in the novel; Genesis 24:16, 24:20, 24:30 (Rebekah).
- “a dream and he” — 1 / 1, Genesis 37:5 (Joseph).
- “of his dream the” — 1 / 1, Genesis 40:5.
- “his sheep and”, “of the flock”, “the sheep that” — shepherd language shared with the patriarchal narratives.

**Exodus**

- “a stranger in a strange land” / “stranger in a strange land” — 2 times in *The Alchemist*; Exodus 2:22 (Moses naming Gershom). The novel applies the phrase to Joseph: “His name was Joseph. He, too, was a stranger in a strange land, like you.”
- “of the desert and” — 13 in the novel; Exodus 3:1 (Moses at Horeb).
- “of the desert” — 45 / 1; “into the desert”, “to the desert”, “from the desert” also match.
- “thummim and they” — 1 / 1, Exodus 28:30.
- “of the breastplate” — 1 / 6, Exodus 28:23, 28:24, 28:26, 39:16.

**Leviticus**

- “urim and” — 15 in the novel; Leviticus 8:8.
- “the breastplate” / “breastplate the” — Leviticus 8:8.
- Other shared strings such as “as well the” and “the old man and” are coincidences (the adverb *well*, or a generic “old man”) and are not treated as allusions.

## Story parallels (only matches actually found)

Each row has a short *Alchemist* snippet (trimmed to under 20 words) and the KJV refs this run actually matched.

### Genesis

| Theme | Alchemist snippet | KJV refs matched |
|---|---|---|
| Shepherd / flocks | “…night there. He saw to it that all the sheep entered through the ruined gate, and then laid…” | Genesis 4:2; 4:4; 12:16; 13:5; 20:14; 21:27; 21:28; 24:35; 26:14; 27:9; 29:2; 29:3 (first 12 flock/shepherd hits) |
| Melchizedek, king of Salem | “…in Salem?” The old man laughed. “Well, I’m the king of Salem!” People say strange things, the boy…” | Genesis 14:18 |
| Egypt | “…my interpretation: you must go to the Pyramids in Egypt. I have never heard of them, but, if…” | Genesis 12:10–12, 12:14; 13:1, 13:10; 15:18; 16:1, 16:3; 21:9, 21:21; 25:12 (first 12 *Egypt* hits) |
| Dreams and Joseph | “…am I going to get to Egypt?” “I only interpret dreams. I don’t know how to turn them…” | Genesis 37:5, 37:6, 37:8–10, 37:19, 37:20; 40:5, 40:8, 40:9, 40:16; 41:1 (Joseph cycle, first 12 *dream* hits in Gen 37–41) |
| Wells (Gen 21, 24, 26, 29) | “…THE oasis, rather than being just a well surrounded by a few palm…” | Genesis 21:19, 21:25; 24:11, 24:13, 24:16, 24:20, 24:29, 24:30, 24:42, 24:43, 24:45, 24:62 (water *well/wells* only; the adverb *well* was excluded) |
| Oasis / woman at the well (Rebekah, Rachel) | The boy “approached a woman who had come to the well to fill a goatskin with water.” Fatima is met at the Al-Fayoum oasis. | Genesis 24:15, 24:29, 24:30, 24:45, 24:51, 24:53, 24:58–61, 24:64, 24:67 (Rebekah). Rachel is in Genesis 29 (at a well) but the name *Rachel* is not in the novel, and *Rebekah* is not either. This is a thematic parallel with a real well-and-woman scene in the novel, not a named borrowing. |
| Desert / journey | “…but it had also brought the smell of the desert and of veiled women. It had brought with…” | Genesis 11:2; 12:9; 13:3, 13:11; 14:6; 16:7; 20:1; 21:14, 21:20, 21:21; 24:21; 29:1 |
| Treasure / gold | “…his son a pouch that held three ancient Spanish gold coins. “I found these one day in the…” | Genesis 2:11, 2:12; 13:2; 20:16; 23:15, 23:16; 24:22, 24:35, 24:53; 37:28; 41:42; 43:23 |

The novel also retells Joseph in Egypt in so many words, including the line “He, too, was a stranger in a strange land, like you.” That is an explicit Genesis 41 allusion, not just shared vocabulary.

### Exodus

| Theme | Alchemist snippet | KJV refs matched |
|---|---|---|
| Egypt | “…by both hands and transported me to the Egyptian pyramids.” He paused for a moment to see if…” | Exodus 1:1, 1:5, 1:8, 1:13, 1:15, 1:17–19; 2:11, 2:12, 2:14, 2:19 (first 12 *Egypt* hits) |
| Desert wandering | “…brought the Moors, yes, but it had also brought the smell of the desert and of veiled women.…” | Exodus 3:1, 3:18; 4:27; 5:1, 5:3; 7:16; 8:27, 8:28; 13:18, 13:20; 14:3, 14:11 |
| Urim and Thummim (Ex 28:30) | “…at the center of the breastplate. “They are called Urim and Thummim. The black signifies ‘yes,’ and the…” | Exodus 28:30 |
| Signs / omens | “…being a shepherd, and that it was a good omen.” “That’s the way it always is,” said the…” | Exodus 3:20; 4:8, 4:9, 4:17, 4:21, 4:28, 4:30; 7:3; 8:23; 10:1, 10:2; 11:9 (*sign/signs/wonder/wonders*). The novel’s own word is usually *omen* (59 hits of *omen/omens*). Shared *sign* is a common English word, so this row is a thematic plus lexical overlap, not a quotation. |

### Leviticus

| Theme | Alchemist snippet | KJV refs matched |
|---|---|---|
| Urim and Thummim (Lev 8:8) | “…at the center of the breastplate. “They are called Urim and Thummim. The black signifies ‘yes,’ and the…” | Leviticus 8:8 |
| Breastplate stones | “…by what he saw. The old man wore a breastplate of heavy gold, covered with precious stones. The…” | Leviticus 8:8; 16:4; 16:32 (*breastplate* / *Urim* / *Thummim* / *holy garments*) |

No other sustained Leviticus episode (sacrifice law, leprosy, festivals, clean and unclean animals as a plot) turned up as a real story parallel. The book’s Leviticus footprint is almost entirely the same priestly-breastplate object already anchored in Exodus 28.

## What this does and does not prove

**It does support a real Old Testament — especially Genesis and Exodus — draw in *The Alchemist*.** The evidence is strongest where the novel *names* the source: Melchizedek the king of Salem (Genesis 14:18), Joseph interpreting Pharaoh’s dream and rescuing Egypt from famine (Genesis 41), the phrase “a stranger in a strange land” (Exodus 2:22), and Urim and Thummim set in a gold breastplate (Exodus 28:30; Leviticus 8:8). Santiago as a shepherd who crosses a desert toward Egypt, reads omens, and meets a woman at a well/oasis sits on top of that named core. The distinctiveness rates agree in direction: *The Alchemist* uses distinctly Genesis words at 64.36 per 10k content tokens, against 12.59 in *The Great Gatsby* and 29.12 in *The Thirty-Nine Steps*, and its combined Torah-distinct rate (127.57) sits well above those novels and well below *The Economy of God* (517.11).

**It does not prove that the King James wording was Coelho’s source, or that most of the novel “comes from” Genesis.** More than two-fifths of its content word types (43.83%) are not in the KJV at all. A large share of the words that *are* in Genesis are ordinary narrative English — that is exactly why the older “in Genesis at all” percentages made the baseline novels look close, and why they were replaced as the lead measure. Some high log-odds words (*offering*, *seventh*, *meat*, *sons*) are priestly or patriarchal vocabulary used once or twice, not story structure. Shared n-grams include coincidences. The Rebekah/Rachel parallel is real as a type-scene (a woman at a well) but the novel never uses those names. Leviticus, apart from Urim and Thummim, is not a narrative source here. And a Portuguese novel in English translation can pick up biblical diction from any English Bible, from church language, or from the translator.

The defensible claim is narrower: *The Alchemist* deliberately reuses a small set of Torah figures, objects, and type-scenes — Melchizedek, Joseph, Egypt, desert, shepherd, well, and the breastplate stones — and its remaining English sits somewhat closer to KJV/Genesis vocabulary than comparable secular novels do.
