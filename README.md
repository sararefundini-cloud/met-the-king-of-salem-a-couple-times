# Met the King of Salem Twice: The Alchemist and Abraham, an Exploratory Text Analytics Project

**Read the report:** https://sararefundini-cloud.github.io/met-the-king-of-salem-a-couple-times/

An exploratory, AI-assisted text analytics report on how Paulo Coelho's *The Alchemist* lines up with Abraham's journey in Genesis.

Interactive report: [dashboard](https://cursor.com/canvas/store-3f56d3a0-7393-4378-8c2f-d5df9305ae31/a25fea83-5077-4720-bbed-186fcbf3a72c)

## Origin

This is a personal starting point, not a finding from the data. In undergrad I was on a team that sorted TripAdvisor reviews about visitor harassment by micro-traders (taxi scams, aggressive street vendors) into categories. Later, at Staples, I analyzed exception tickets in Excel to find trends in benefits enrollment. Those experiences led me to start reading Bible stories the same way, as tickets sorted into categories. I built those categories from Venn diagrams I drew by hand comparing *The Economy of God* and *The Alchemist*, and that lexicon became the backbone of this Python analysis. *The Alchemist* used to be my bible and shaped my decisions; studied next to Genesis, it began to look like a shadow of Abraham's story — the same king of Salem and the same tenth, but with trust placed in personal dreams rather than in God. Abraham's kind of faith is the one I want in my own life.

## Method

The scripts tokenize running text the same way across every corpus (lowercase, typographic apostrophes and dashes normalized, possessives reduced to the base word, common contractions expanded). Em-dashes are treated as punctuation (so *crystal—he* stays two words); en-dashes in King James names are joined (*Beth–el* → *Bethel*). Function words are dropped with a shared English / KJV stopword list. Rates are reported per 10,000 content (non-stopword) tokens.

Distinctiveness uses smoothed log-odds against [wordfreq](https://github.com/rspeer/wordfreq) 3.1.1 English (treated as a large modern-English reference), not TF-IDF. A content word is treated as distinctive of a biblical book when it occurs at least 3 times in that book and its smoothed log-odds is at least **4.0**. That 4.0 cutoff is a **heuristic**, set by inspecting the score distribution; it is not a formal significance test.

Two public-domain novels of similar length and era — *The Great Gatsby* (Project Gutenberg #64317) and *The Thirty-Nine Steps* (Project Gutenberg #558) — are **exploratory, non-genre-matched controls**. They are a baseline for ordinary narrative English, not a representative sample of literature, and they are not desert-quest or biblical-retelling novels. A larger or better-matched comparison group would be the next step.

The King James source is the public-domain scrollmapper CSV in `source/` (31,102 verses). See `source/SOURCE.md`.

## Key observations

The strongest, most specific connection is **Melchizedek and the tithe**. The same king of Salem, and a tenth, appear in Genesis 14:18–20 and in the novel, which itself compares that fee to Abraham.

A secondary quantitative contrast is the **Abraham-cycle rate** (distinctive vocabulary from the Abraham material in Genesis, per 10,000 content tokens):

| Text | Rate per 10k content tokens |
|---|---:|
| *The Alchemist* | 40.42 |
| *The Great Gatsby* | 3.09 |
| *The Thirty-Nine Steps* | 11.60 |

These are observations from an exploratory comparison, not proof of deliberate literary construction. Santiago can be read as a literary foil to Abraham; that is an interpretation, not a statistical conclusion.

## Limitations

- The control novels are poorly matched for genre. A shepherd-and-desert quest will naturally use more tents, camels, and desert language than a novel about wealthy New Yorkers. The 13× Gatsby contrast should be read with that in mind.
- High counts for words such as *desert* and *treasure* often reflect the plot of *The Alchemist*, not independent evidence of biblical influence.
- A word that appears in Scripture is not automatically a biblical symbol when it appears in the novel. Meanings drawn from Witness Lee's *The Economy of God* are one interpretive reading, not the Bible's own explicit explanation, and not proof of Coelho's intent.
- Frequency analysis alone cannot establish whether Coelho deliberately reversed Abraham's theology.
- The analysis was AI-assisted. Treat the numbers as rerunnable observations, and keep them separate from interpretation.

## Repository layout

```
met-the-king-of-salem-a-couple-times/
  compare.py                  Abraham-cycle / source-bucket / distinctiveness study
  build_symbolic_genesis.py   Genesis-sourced lexicon (Leviticus splash for Urim/Thummim)
  textutil.py                 tokenization, stopwords, book cleaners, repo paths
  lexicon.py, build_graph.py  optional KJV motif inventory (used to build the Neo4j files)
  source/KJV.csv              public-domain King James text
  source/SOURCE.md            attribution (scrollmapper) and typography notes
  data/baselines/             Gatsby and The Thirty-Nine Steps, with ATTRIBUTION.md
  data/private/               your copies of the copyrighted books (not in this repo)
  output/                     CSVs, charts, and the written summary
  neo4j/                      Neo4j-ready import files (see below)
```

## How to rerun

You will need Python 3.10+ and the packages in `requirements.txt`.

A plain-English methods guide, including why log-odds was used and how the 4.0 cutoff behaves at 3 and 5, is in [`docs/HOW_THE_ANALYSIS_WORKS.md`](docs/HOW_THE_ANALYSIS_WORKS.md). After installing dependencies, run the checks with `python -m pytest tests/test_counts.py`.


1. **Create a virtual environment and install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Add the copyrighted source texts**

   This repository does **not** include *The Alchemist* or *The Economy of God*. Both are under copyright. Place your own plain-text copies at:

   - `data/private/alchemist.txt`
   - `data/private/economy.txt`

   The cleaners in `textutil.py` drop title pages, tables of contents, and publisher back matter. Do not commit these files; `data/private/` is gitignored.

3. **Run the source and distinctiveness study**

   From this directory (or any directory; paths are resolved relative to the scripts):

   ```bash
   python compare.py
   ```

   This writes `output/alchemist_genesis.csv`, `output/alchemist_genesis.png`, `output/distinct_genesis.csv`, and `output/alchemist_genesis_distinct.png`.

4. **Rebuild the Genesis symbolic lexicon counts**

   ```bash
   python build_symbolic_genesis.py
   ```

   This writes `output/symbolic_genesis.csv` and `output/symbolic_genesis.json`. Snippets stored in those files are limited to one short sentence.

5. **(Optional) Rebuild the KJV motif inventory**

   ```bash
   python build_graph.py
   ```

   This regenerates `output/lexicon.csv`, inventory CSVs under `output/inventory/`, and `neo4j/motifs.csv`. It is not required to reproduce the Alchemist / Abraham figures above.

Precomputed motif-rate tables and charts already in `output/` (`motif_rates.csv`, `term_rates.csv`, and the associated PNGs) come from that inventory compared with the same four texts. They are included as artifacts; regenerating them is not part of the default rerun path.

## Neo4j files

The files under `neo4j/` (`terms.csv`, `motifs.csv`, `import.cypher`) are **Neo4j-ready import files; they have not yet been loaded or tested in a running Neo4j instance.** This analysis did not run against Neo4j. See `neo4j/README.md` if you want to try a load.

## License

The code in this repository is released under the MIT License (see `LICENSE`).

The texts are under their own terms:

- King James source in `source/`: public domain, as distributed by [scrollmapper/bible_databases](https://github.com/scrollmapper/bible_databases). See `source/SOURCE.md`.
- *The Great Gatsby* and *The Thirty-Nine Steps*: public domain in the United States, via Project Gutenberg. See `data/baselines/ATTRIBUTION.md`.
- *The Alchemist* (Paulo Coelho) and *The Economy of God* (Witness Lee) are **not included**. Supply your own copies to rerun. Short quoted snippets in the outputs are limited to one sentence or less.
