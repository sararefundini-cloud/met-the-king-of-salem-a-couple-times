# How the analysis works

A plain-English guide to the choices behind this analysis. The analysis was AI-assisted. The figures below were recomputed from the source texts after a tokenizer correction (em-dashes and contractions).

## What tokenization and stopwords are

Tokenization is how a book is split into words. Every corpus in this project is treated the same way: letters are kept, typographic punctuation is standardized, possessives like *king's* are counted under *king*, and common contractions like *don't* are expanded so they do not become junk pieces (*don* and *t*). King James place names that use an en-dash (*Beth–el*) are joined into one word (*Bethel*), matching ordinary printed Bibles.

Stopwords are the function words that almost every English text uses at a high rate: *the*, *and*, *of*, *is*, plus King James particles such as *unto* and *thou*. They are dropped before rates are computed, so the comparison is about content vocabulary rather than grammar.

## Why rates are per 10,000 content words

The Alchemist, The Great Gatsby, and The Thirty-Nine Steps are similar in length, but they are not identical, and The Economy of God is longer. A raw count of *tent* would favor whichever book has more words. Dividing by the number of content tokens, then scaling to 10,000, puts every book on the same scale: “how often does this word appear, per 10,000 content words?”

Content tokens, not all tokens, are the denominator because stopwords would otherwise swamp the rates.

## What smoothed log-odds is, and why it was used instead of TF-IDF

The question is not “which words are important inside Genesis?” It is “which words are more characteristic of the Abraham material than of ordinary modern English?”

Smoothed log-odds answers that directly. For each word, the method compares its rate in corpus A (here, Genesis 11:26–25:10) with its rate in corpus B (a large modern-English reference from wordfreq). A small constant, 0.5, is added to every count so that rare or missing words do not produce zeros or infinities. A large positive score means the word is much more at home in the biblical corpus than in everyday English. *Melchizedek* scores high; *son* and *came* do not, even though they are common in Genesis, because they are also common in English.

TF-IDF was not used as the lead measure. TF-IDF ranks words inside a document or a small collection of documents. It is a good search and keyword tool, but it does not directly compare two corpora, and it handles rare words less cleanly than a smoothed ratio. Log-odds is a better fit for “is this more distinctive of Abraham’s story than of modern English?”

wordfreq English (version 3.1.1) is treated as a 1-billion-word reference, the scale on which its zipf frequencies are defined.

## Why the cutoff is 4.0, and what happens at 3 or 5

A word is treated as distinctive of the Abraham cycle when it occurs at least three times in Genesis 11:26–25:10, its log-odds versus wordfreq is at least **4.0**, and it is also over-represented against the rest of Genesis (log-odds at least 0.5). Proper names are added separately; Melchizedek and Salem are kept even if they appear only once.

The 4.0 cutoff is a **heuristic**, not a formal significance test. It was set by looking at the score distribution: it admits vocabulary such as *flock* and *altar*, and it rejects ordinary narrative words such as *son* and *came*.

Because it is a judgment call, the headline rate was recomputed at nearby cutoffs. After the tokenizer correction, distinctive-token rates per 10,000 content words are:

| Log-odds cutoff | List size | The Alchemist | The Great Gatsby | The Thirty-Nine Steps |
|---|---:|---:|---:|---:|
| 3.0 | 188 types | 103.76 | 49.85 | 42.53 |
| **4.0 (reported)** | **165 types** | **40.42** | **3.09** | **11.60** |
| 5.0 | 149 types | 17.50 | 0.88 | 4.97 |

At 3.0 the list lets in more ordinary narrative words (*son*, *stood*, *laughed*), the rates jump, and the gap between The Alchemist and Gatsby shrinks. At 5.0 the list is stricter, *tent* falls out of the Alchemist’s leading items, and the headline rate drops to 17.50. The reported 4.0 figures sit between those two. The qualitative gap remains in all three rows, but the size of the “13× Gatsby” contrast is sensitive to the cutoff and to the poorly matched control novels.

## How the counts were checked

- The King James source is the public-domain scrollmapper CSV: 31,102 verses and 790,882 tokens. Combined *Lord*/*LORD*/*lord* totals 7,970, and *Bethel* (after joining *Beth–el*) totals 66, both matching the kjvindex frequency lists.
- Tokenization was spot-checked on possessives, typographic apostrophes, em-dashes, contractions, and the Jordan Baker problem in Gatsby (the name *Jordan* is not counted as the river in the novels).
- A small pytest suite in `tests/test_counts.py` freezes those checks, including Salem (11) and Melchizedek (4) in The Alchemist when the copyrighted text is present.
- Every Alchemist quotation, King James quotation, and Witness Lee quotation on the report was checked against the source texts. Lee chapter numbers were checked against the 24 chapter headings in *The Economy of God*.

The checks are strong for counts and quotations. They do not validate the literary interpretation.

## Limits

- The control novels are public-domain books of similar length and era, not desert-quest or biblical-retelling novels. A shepherd story will naturally use more tents and camels than a novel about wealthy New Yorkers. The size of the frequency gap should not be read as a measure of biblical influence.
- High counts for *desert* and *treasure* often reflect the plot of The Alchemist, not independent evidence of biblical influence.
- The lexicon was chosen with knowledge of the novel, so there is a selection-bias risk.
- A word that appears in Scripture is not automatically a biblical symbol when it appears in the novel. Meanings drawn from Witness Lee’s *The Economy of God* are one typological reading, not the Bible’s own explicit explanation, and not proof of Coelho’s intent.
- Frequency analysis alone cannot establish whether Coelho deliberately reversed Abraham’s theology.
- The 4.0 threshold is a heuristic. The table above shows how the headline rate moves if it is set to 3 or 5.
