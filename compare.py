#!/usr/bin/env python3
"""Compare The Alchemist with Genesis, Exodus, and Leviticus, plus two control novels.

This is the source-and-distinctiveness study. It tokenizes each book the same
way, drops function words, and asks which words are distinctive of a biblical
book compared with ordinary modern English (smoothed log-odds versus wordfreq).
It also reports how often those distinctive words appear in The Alchemist and
in the control novels, as a rate per 10,000 content words.

Place copyrighted texts in data/private/ (alchemist.txt, economy.txt).
Public-domain baselines live in data/baselines/. Paths are relative to
this file, so the script can be run from any working directory.
"""

from __future__ import annotations

import collections
import csv
import math
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from textutil import (  # noqa: E402
    OT_BOOKS, NT_BOOKS, SOURCE_LABELS, STOPWORDS,
    BASELINES_DIR, OUTPUT_DIR, PRIVATE_DIR, SOURCE_CSV,
    classify_word, load_book, require_private_texts, tokenize,
)
from lexicon import MOTIF_ORDER, build_lexicon  # noqa: E402
from build_graph import compile_lexicon  # noqa: E402

VERSES_CSV = SOURCE_CSV
OUT = OUTPUT_DIR
OUT.mkdir(exist_ok=True)

# Display names and how to clean each book.
# Copyrighted texts must be supplied by the user in data/private/.
BOOKS = {
    "economy": {
        "label": "The Economy of God",
        "path": PRIVATE_DIR / "economy.txt",
        "kind": "economy",
        "year": 1964,
        "author": "Witness Lee",
    },
    "alchemist": {
        "label": "The Alchemist",
        "path": PRIVATE_DIR / "alchemist.txt",
        "kind": "alchemist",
        "year": 1988,
        "author": "Paulo Coelho",
    },
}

BASELINES = {
    "gatsby": {
        "label": "The Great Gatsby",
        "path": BASELINES_DIR / "the_great_gatsby.txt",
        "kind": "gutenberg",
        "year": 1925,
        "author": "F. Scott Fitzgerald",
        "gutenberg_id": 64317,
    },
    "thirty_nine_steps": {
        "label": "The Thirty-Nine Steps",
        "path": BASELINES_DIR / "the_thirty_nine_steps.txt",
        "kind": "gutenberg",
        "year": 1915,
        "author": "John Buchan",
        "gutenberg_id": 558,
    },
}

KJV_LABEL = "KJV"

# Scripture citation pattern used to flag quotations in Economy of God
CITE_RE = re.compile(
    r"\b(?:(?:[1-3]\s)?(?:Genesis|Exodus|Leviticus|Numbers|Deuteronomy|Joshua|"
    r"Judges|Ruth|Samuel|Kings|Chronicles|Ezra|Nehemiah|Esther|Job|Psalms?|"
    r"Proverbs|Ecclesiastes|Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|"
    r"Hosea|Joel|Amos|Obadiah|Jonah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|"
    r"Zechariah|Malachi|Matthew|Mark|Luke|John|Acts|Romans|Corinthians|"
    r"Galatians|Ephesians|Philippians|Colossians|Thessalonians|Timothy|"
    r"Titus|Philemon|Hebrews|James|Peter|Jude|Revelation|"
    r"Gen|Exo|Exod|Lev|Num|Deut|Josh|Judg|Sam|Kgs|Chr|Neh|Esth|Psa|Ps|"
    r"Prov|Eccl|Isa|Jer|Lam|Ezek|Dan|Hos|Joel|Amos|Obad|Jonah|Mic|Nah|"
    r"Hab|Zeph|Hag|Zech|Mal|Matt|Mat|Mk|Lk|Jn|Rom|Cor|Gal|Eph|Phil|Col|"
    r"Thes|Thess|Tim|Tit|Phlm|Heb|Jas|Pet|Rev)\.?)\s+\d{1,3}:\d{1,3}",
    re.I,
)
QUOTE_RE = re.compile(r"“([^”]{3,800})”")


def rate_per_10k(count: int, total_tokens: int) -> float:
    """Hits per 10,000 tokens. Using a rate (not a raw count) lets short and
    long books be compared on the same scale. The report uses content tokens
    — the words left after stopwords are removed — as the denominator.
    """
    if total_tokens <= 0:
        return 0.0
    return (count / total_tokens) * 10000.0


def load_kjv_verses() -> list[dict]:
    """Load verses from source/KJV.csv (Book, Chapter, Verse, Text)."""
    verses = []
    with VERSES_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            book = row.get("book") or row.get("Book")
            chapter = int(row.get("chapter") or row.get("Chapter"))
            verse_n = int(row.get("verse") or row.get("Verse"))
            text = row.get("text") or row.get("Text") or ""
            tokens = tokenize(text)
            verses.append({
                "book": book,
                "chapter": chapter,
                "verse": verse_n,
                "text": text,
                "ref": f"{book} {chapter}:{verse_n}",
                "tokens": tokens,
                "token_set": set(tokens),
            })
    return verses


def book_token_sets(verses: list[dict]) -> dict[str, set[str]]:
    by_book = collections.defaultdict(set)
    ot, nt = set(), set()
    for v in verses:
        by_book[v["book"]].update(v["token_set"])
        if v["book"] in OT_BOOKS:
            ot.update(v["token_set"])
        elif v["book"] in NT_BOOKS:
            nt.update(v["token_set"])
    all_kjv = ot | nt
    return {
        "Genesis": set(by_book["Genesis"]),
        "Exodus": set(by_book["Exodus"]),
        "Leviticus": set(by_book["Leviticus"]),
        "OT": ot,
        "NT": nt,
        "KJV": all_kjv,
        "by_book": by_book,
    }


def kjv_token_counts(verses: list[dict]) -> tuple[collections.Counter, int, dict]:
    """Global KJV counts plus per-book counters and token totals."""
    all_c = collections.Counter()
    n_all = 0
    per = {b: collections.Counter() for b in ("Genesis", "Exodus", "Leviticus")}
    n_per = {b: 0 for b in per}
    for v in verses:
        all_c.update(v["tokens"])
        n_all += len(v["tokens"])
        if v["book"] in per:
            per[v["book"]].update(v["tokens"])
            n_per[v["book"]] += len(v["tokens"])
    return all_c, n_all, {"counts": per, "totals": n_per}


def analyze_text(text: str) -> dict:
    tokens = tokenize(text)
    counts = collections.Counter(tokens)
    return {
        "text": text,
        "tokens": tokens,
        "counts": counts,
        "n_tokens": len(tokens),
        "n_types": len(counts),
        "content_tokens": [t for t in tokens if t not in STOPWORDS],
    }


def mark_quoted_spans(text: str) -> list[tuple[int, int, str]]:
    """Character spans likely to be scripture quotations or immediately cited."""
    spans = []
    for m in QUOTE_RE.finditer(text):
        spans.append((m.start(), m.end(), "quote"))
    for m in CITE_RE.finditer(text):
        # window preceding a citation often holds the quoted verse
        start = max(0, m.start() - 180)
        spans.append((start, m.end(), "citation_window"))
    return spans


def count_hits_in_spans(text: str, term_pattern: re.Pattern, spans: list[tuple[int, int, str]]) -> tuple[int, int]:
    total = 0
    in_span = 0
    for m in term_pattern.finditer(text.lower() if term_pattern.flags & re.I else text):
        total += 1
        pos = m.start()
        if any(a <= pos < b for a, b, _ in spans):
            in_span += 1
    return total, in_span


# -------------------- lexicon matching over a raw text --------------------

def compile_and_match(text: str, compiled: list[dict]) -> dict:
    """Return motif/term hit counts over a whole book treated as one document.

    Phrase/regex/exact matching uses the same compiled lexicon as the KJV build.
    Because a book is not verse-segmented, one hit is one regex/phrase findall
    count (raw occurrences), not a verse count.
    """
    from build_graph import normalize_for_match, term_matches

    # Fake a single 'verse' for special matchers that operate on a verse dict,
    # but count phrase/exact with findall for raw frequency.
    match = normalize_for_match(text)
    term_raw = collections.Counter()
    motif_raw = collections.Counter()
    motif_terms = collections.defaultdict(collections.Counter)
    subgroup_raw = collections.Counter()

    # For special repeating-names, we still walk 'clauses' later if needed;
    # whole-book special matching would be messy, so count via findall for
    # exact/phrase/regex only, and skip special (those are KJV-style vocatives).
    for item in compiled:
        mt = item["match_type"]
        report = item["report_as"]
        motif = item["motif"]
        sg = item.get("subgroup") or ""
        if mt == "special":
            continue
        pat = item.get("pattern")
        if pat is None:
            continue
        # Colors 'red' / infant-death contextual rules are verse-oriented;
        # apply the same term_matches by splitting into paragraph-sized chunks
        # would be slow. For book comparison we use raw pattern finditer on
        # the normalized book text, with a few book-level guards.
        target = match
        if motif == "Colors" and item["term"] == "red":
            target = re.sub(r"\bred\s+sea\b", "xxx xxx", match)
        try:
            n = len(list(pat.finditer(target)))
        except re.error:
            n = 0
        if n:
            term_raw[(motif, sg, report)] += n
            motif_raw[motif] += n
            motif_terms[motif][report] += n
            if sg:
                subgroup_raw[(motif, sg)] += n
    return {
        "term_raw": term_raw,
        "motif_raw": motif_raw,
        "motif_terms": motif_terms,
        "subgroup_raw": subgroup_raw,
    }


def kjv_motif_term_counts(verses: list[dict], compiled: list[dict]) -> dict:
    """Reuse motif_occurrences.csv if it is up to date with current lexicon
    motifs; otherwise recount from verses (always recount — safer)."""
    from build_graph import term_matches

    term_raw = collections.Counter()   # raw term hits across verses (one per term per verse, as in inventory)
    term_occ = collections.Counter()
    motif_raw = collections.Counter()
    motif_verses = collections.defaultdict(set)
    subgroup_raw = collections.Counter()
    subgroup_verses = collections.defaultdict(set)

    for v in verses:
        # term_matches expects keys used in build_graph verses
        vd = {
            "text": v["text"],
            "match": " ".join(v["tokens"]),  # already lowercased tokens; phrases with punctuation may miss
        }
        # Better: use normalize_for_match on original text
    from build_graph import normalize_for_match, normalize_text
    term_raw = collections.Counter()
    motif_hits = collections.Counter()
    motif_verse_n = collections.Counter()
    subgroup_hits = collections.Counter()
    subgroup_verse_n = collections.Counter()

    for v in verses:
        vd = {
            "text": v["text"],
            "match": normalize_for_match(v["text"]),
            "book": v.get("book") or "",
            "chapter": v.get("chapter") or "",
            "verse": v.get("verse") or "",
        }
        seen_m = set()
        seen_s = set()
        seen_t = set()
        for item in compiled:
            reports = term_matches(item, vd)
            for report in reports:
                key = (item["motif"], item.get("subgroup") or "", report)
                if key in seen_t:
                    continue
                seen_t.add(key)
                term_raw[key] += 1
                motif_hits[item["motif"]] += 1
                seen_m.add(item["motif"])
                if item.get("subgroup"):
                    subgroup_hits[(item["motif"], item["subgroup"])] += 1
                    seen_s.add((item["motif"], item["subgroup"]))
        for m in seen_m:
            motif_verse_n[m] += 1
        for s in seen_s:
            subgroup_verse_n[s] += 1
    return {
        "term_raw": term_raw,  # verse-level presence counts (same as inventory hits)
        "motif_hits": motif_hits,
        "motif_verse_n": motif_verse_n,
        "subgroup_hits": subgroup_hits,
        "subgroup_verse_n": subgroup_verse_n,
    }


# -------------------- source analysis (Alchemist vs Torah) --------------------

def exclusive_bucket_shares(content_tokens: list[str], types: list[str], sets: dict) -> dict:
    """Percentages for types and tokens in exclusive buckets and cumulative sets."""
    type_bucket = collections.Counter(classify_word(w, sets) for w in types)
    tok_bucket = collections.Counter(classify_word(w, sets) for w in content_tokens)
    n_types = len(types) or 1
    n_tok = len(content_tokens) or 1

    def pct_types(pred):
        return 100.0 * sum(1 for w in types if pred(w)) / n_types

    def pct_tok(pred):
        return 100.0 * sum(1 for w in content_tokens if pred(w)) / n_tok

    in_gen = lambda w: w in sets["Genesis"]
    in_ex = lambda w: w in sets["Exodus"]
    in_lev = lambda w: w in sets["Leviticus"]
    in_torah = lambda w: w in sets["Genesis"] or w in sets["Exodus"] or w in sets["Leviticus"]
    in_ot = lambda w: w in sets["OT"]
    in_kjv = lambda w: w in sets["KJV"]

    return {
        "n_types": len(types),
        "n_tokens": len(content_tokens),
        "type_bucket": {k: type_bucket.get(k, 0) for k in SOURCE_LABELS},
        "tok_bucket": {k: tok_bucket.get(k, 0) for k in SOURCE_LABELS},
        "type_bucket_pct": {k: 100.0 * type_bucket.get(k, 0) / n_types for k in SOURCE_LABELS},
        "tok_bucket_pct": {k: 100.0 * tok_bucket.get(k, 0) / n_tok for k in SOURCE_LABELS},
        "cumulative": {
            "in_Genesis_types": pct_types(in_gen),
            "in_Exodus_types": pct_types(in_ex),
            "in_Leviticus_types": pct_types(in_lev),
            "in_GenExodLev_types": pct_types(in_torah),
            "in_OT_types": pct_types(in_ot),
            "in_KJV_types": pct_types(in_kjv),
            "in_Genesis_tokens": pct_tok(in_gen),
            "in_Exodus_tokens": pct_tok(in_ex),
            "in_Leviticus_tokens": pct_tok(in_lev),
            "in_GenExodLev_tokens": pct_tok(in_torah),
            "in_OT_tokens": pct_tok(in_ot),
            "in_KJV_tokens": pct_tok(in_kjv),
        },
    }


def log_odds(c_a: float, n_a: int, c_b: float, n_b: int) -> float:
    """Smoothed log-odds ratio of a word in corpus A versus corpus B.

    This asks: is word w more characteristic of A than of B? The 0.5 added to
    every count is a smoothing term, so rare or missing words do not produce
    zeros or infinities. Unlike TF-IDF, which ranks words inside a document,
    this compares two corpora directly. The 4.0 cutoff used later is a
    heuristic, not a formal significance test.
    """
    return (
        math.log((c_a + 0.5) / (n_a - c_a + 0.5))
        - math.log((c_b + 0.5) / (n_b - c_b + 0.5))
    )


def rate_ratio(c_a: float, n_a: int, c_b: float, n_b: int) -> float:
    ra = (c_a + 0.5) / (n_a + 1.0)
    rb = (c_b + 0.5) / (n_b + 1.0)
    return ra / rb


def ngrams(tokens: list[str], n: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def ngram_has_content(ng: tuple[str, ...]) -> bool:
    return any(t not in STOPWORDS for t in ng)


def extract_snippet(text: str, pattern: str, max_words: int = 18) -> str | None:
    m = re.search(pattern, text, re.I)
    if not m:
        return None
    # take a window around the match and trim to <= max_words
    start = max(0, m.start() - 60)
    end = min(len(text), m.end() + 60)
    window = re.sub(r"\s+", " ", text[start:end]).strip()
    words = window.split()
    # center on the match as well as we can
    if len(words) <= max_words:
        snippet = " ".join(words)
    else:
        # find the match text in the window words
        key = m.group(0).split()[0].lower()
        idxs = [i for i, w in enumerate(words) if key in re.sub(r"[^a-z]", "", w.lower())]
        mid = idxs[0] if idxs else len(words) // 2
        a = max(0, mid - max_words // 2)
        b = min(len(words), a + max_words)
        a = max(0, b - max_words)
        snippet = " ".join(words[a:b])
    if start > 0 and not snippet.startswith("…"):
        snippet = "…" + snippet
    if end < len(text):
        snippet = snippet + "…"
    return snippet


def refs_for_pattern(verses: list[dict], book: str | None, pattern: str, chapter_range=None, limit=12) -> list[str]:
    pat = re.compile(pattern, re.I)
    refs = []
    for v in verses:
        if book and v["book"] != book:
            continue
        if chapter_range and not (chapter_range[0] <= v["chapter"] <= chapter_range[1]):
            continue
        if pat.search(v["text"]):
            refs.append(v["ref"])
            if len(refs) >= limit:
                break
    return refs


def build_story_parallels(alchemist_text: str, verses: list[dict]) -> list[dict]:
    """Search both texts for the episode parallels Sara named; only keep hits."""
    rows = []

    def add(theme, source_book, alc_pat, kjv_pat, chapters=None, notes=""):
        snippet = extract_snippet(alchemist_text, alc_pat)
        refs = refs_for_pattern(verses, source_book, kjv_pat, chapters)
        if snippet or refs:
            rows.append({
                "theme": theme,
                "source_book": source_book or "",
                "alchemist_snippet": snippet or "(no matching snippet found in the cleaned Alchemist text)",
                "kjv_refs": "; ".join(refs) if refs else "(no KJV match for this pattern)",
                "n_refs": len(refs),
                "notes": notes,
            })

    # --- Genesis ---
    add("Shepherd / flocks", "Genesis",
        r"\b(sheep|shepherd|shepherds|flock|flocks)\b",
        r"\b(sheep|shepherd|flock|flocks)\b",
        notes="Santiago is a shepherd; Genesis has many flock narratives (Abel, Abram, Jacob, Joseph's brothers).")
    add("Melchizedek, king of Salem", "Genesis",
        r"Melchizedek|king of Salem",
        r"Melchizedek|Melchisedec|king of Salem",
        chapters=(14, 14),
        notes="The Alchemist's king of Salem is named Melchizedek. Genesis 14:18 is the primary KJV occurrence of the title.")
    add("Egypt", "Genesis",
        r"\bEgypt\b",
        r"\bEgypt",
        notes="Santiago travels toward and through Egypt (the pyramids). Genesis Egypt cycles include Abram (Gen 12) and Joseph (Gen 37–50).")
    add("Dreams and their interpretation (Joseph)", "Genesis",
        r"pharaoh dreamed|cows that were thin|His name was Joseph|interpret(ed)? (dreams?|them)",
        r"\bdream",
        chapters=(37, 41),
        notes="The novel itself retells Joseph interpreting Pharaoh's dream of lean and fat cows. KJV refs are Gen 37, 40–41.")
    add("Wells (Gen 21, 24, 26, 29)", "Genesis",
        r"\b(the well|a well|wells|the well's|well's mouth)\b",
        r"\b(the well|a well|wells)\b",
        chapters=(21, 29),
        notes="Water wells only (the adverb 'well' is excluded). Abraham, Isaac, Rebekah, and Rachel scenes in Gen 21–29.")
    add("Oasis / well and a woman (Rebekah, Rachel)", "Genesis",
        r"Fatima|at the (Al-Fayoum )?oasis",
        r"\b(Rebekah|Rachel)\b",
        chapters=(24, 29),
        notes="Thematic only: Fatima at the oasis vs Rebekah (Gen 24) and Rachel (Gen 29) met at wells. The names Rebekah and Rachel do not appear in the novel.")
    add("Desert / journey", "Genesis",
        r"\bdesert\b",
        r"\b(wilderness|desert|journey)",
        notes="Patriarchal journeys and wilderness itineraries. Snippet taken from an actual 'desert' mention, not the generic word 'journey'.")
    add("Treasure / gold", "Genesis",
        r"\btreasure\b|\bgold\b",
        r"\b(gold|treasure|silver)",
        notes="Gold and goods in the patriarchal narratives (e.g. Abram's wealth, gifts in Gen 24).")

    # --- Exodus ---
    add("Egypt (Exodus)", "Exodus",
        r"\bEgypt\b|\bpyramid",
        r"\bEgypt",
        notes="The Exodus Egypt cycle (bondage, departure). Alchemist Egypt is the destination of the treasure journey.")
    add("Desert wandering", "Exodus",
        r"\b(the desert|across the desert|in the desert)\b",
        r"\b(wilderness|desert)",
        notes="Israel's wilderness wandering after the exodus. The Alchemist crosses the Sahara. 'Wandering' alone is not used (it also describes a flock).")
    add("Urim and Thummim (Ex 28:30)", "Exodus",
        r"\bUrim\b|\bThummim\b",
        r"\b(Urim|Thummim)\b",
        notes="The two stones Melchizedek gives Santiago. In KJV they are priestly lots on the breastplate.")
    add("Signs / omens", "Exodus",
        r"\bomens?\b",
        r"\b(sign|signs|wonder|wonders)\b",
        notes="Exodus repeatedly speaks of signs and wonders. The Alchemist is structured around omens (not the word 'moment', which a looser pattern would have caught). 'Sign' is a common English word.")

    # --- Leviticus (only where a real textual hook exists) ---
    add("Urim and Thummim (Lev 8:8)", "Leviticus",
        r"\bUrim\b|\bThummim\b",
        r"\b(Urim|Thummim)\b",
        notes="Leviticus 8:8 also places Urim and Thummim in the breastplate at the priests' consecration. Included only because the same two names occur in the novel.")
    add("Breastplate stones (Urim and Thummim)", "Leviticus",
        r"\bbreastplate\b|\bUrim\b|\bThummim\b",
        r"\b(breastplate|Urim|Thummim|holy garments)\b",
        notes="The novel describes Melchizedek's gold breastplate with Urim and Thummim at its center. Leviticus 8:8 is the consecration scene; 'priest' as a career the boy's parents wanted is not treated as a ritual parallel.")
    return rows


"""Distinctiveness vs general modern English (wordfreq). Inserted into compare.py."""

# Reference corpus: wordfreq 3.1.1 English, treated as a 1-billion-word collection
# (zipf is already defined as log10 of appearances per billion words).
WORDFREQ_REF_N = 1_000_000_000
DISTINCT_MIN_COUNT = 3
DISTINCT_LOG_ODDS_THRESHOLD = 4.0
# Proper-name guards: mid-verse capitals, not speech-initial after comma/stop.
# Common modern names (zipf >= 4.5) need log-odds >= 2.5 so "Jordan" (Gatsby) is out.
# Hapax names need zipf < 3.5, except a short force-include list (Salem).
NAME_ZIPF_COMMON = 4.5
NAME_COMMON_MIN_LOR = 2.5
NAME_HAPAX_ZIPF_MAX = 3.5
NAME_MIN_LENGTH = 3
FORCE_PROPER_NAMES = {
    "Genesis": frozenset({"salem", "melchizedek", "potiphar"}),
    "Exodus": frozenset(),
    "Leviticus": frozenset(),
}
NAME_DENY = STOPWORDS | {
    "god", "lord", "i", "o", "oh", "almighty", "arise", "spirit", "gather",
}


def wordfreq_scores(count: int, n_tokens: int, word: str) -> tuple[float, float, float, float]:
    """Compare a word's rate in a biblical book with general modern English.

    wordfreq supplies the English reference rate. That rate is scaled to a
    1-billion-word reference corpus (the scale zipf frequencies are defined
    on), then passed through the same smoothed log-odds function.
    Returns (log_odds, rate_ratio, wordfreq_proportion, zipf).
    """
    from wordfreq import word_frequency, zipf_frequency
    freq = word_frequency(word, "en")
    zipf = zipf_frequency(word, "en")
    c_ref = freq * WORDFREQ_REF_N
    lor = log_odds(count, n_tokens, c_ref, WORDFREQ_REF_N)
    rr = rate_ratio(count, n_tokens, c_ref, WORDFREQ_REF_N)
    return lor, rr, freq, zipf


def mid_verse_cap_counts(texts: list[str]) -> collections.Counter:
    """Count mid-verse capitalized tokens, skipping verse starts and speech starts.

    KJV often capitalizes the first word after a comma when speech begins
    ('…daughter in law, Remain a widow'), which is not a proper name.
    """
    caps: collections.Counter = collections.Counter()
    from textutil import normalize_text
    word_re = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
    for text in texts:
        t = normalize_text(text)
        words = list(word_re.finditer(t))
        for i, m in enumerate(words):
            w = m.group(0)
            if not w[0].isupper():
                continue
            if i == 0:
                continue
            prev = t[:m.start()]
            if re.search(r"[,.!?;:]\s*$", prev):
                continue
            caps[w.lower()] += 1
    return caps


def distinct_lexicon_for_book(
    book: str,
    counts: collections.Counter,
    n_tokens: int,
    texts: list[str],
) -> dict[str, dict]:
    """Words strongly over-represented in this book vs modern English, plus names."""
    caps = mid_verse_cap_counts(texts)
    words: dict[str, dict] = {}
    for w, k in counts.items():
        if w in STOPWORDS or k < DISTINCT_MIN_COUNT:
            continue
        lor, rr, freq, zipf = wordfreq_scores(k, n_tokens, w)
        if lor >= DISTINCT_LOG_ODDS_THRESHOLD:
            words[w] = {
                "reason": "log_odds",
                "count": k,
                "log_odds": lor,
                "rate_ratio": rr,
                "wordfreq": freq,
                "zipf": zipf,
                "is_proper_name": False,
            }
    force = FORCE_PROPER_NAMES.get(book, frozenset())
    name_candidates = set(caps) | set(force)
    for w in name_candidates:
        if w in NAME_DENY:
            continue
        if len(w) < NAME_MIN_LENGTH and w not in force:
            continue
        total = counts[w]
        if total == 0:
            continue
        capn = caps.get(w, 0)
        ratio = capn / total
        lor, rr, freq, zipf = wordfreq_scores(total, n_tokens, w)
        forced = w in force
        ok = False
        if forced:
            ok = True
        elif ratio >= 0.8:
            if capn >= 2 and zipf < NAME_ZIPF_COMMON:
                ok = True
            elif capn >= 2 and zipf >= NAME_ZIPF_COMMON and lor >= NAME_COMMON_MIN_LOR:
                ok = True
            elif capn >= 1 and zipf < NAME_HAPAX_ZIPF_MAX:
                ok = True
        if not ok:
            continue
        if w in words:
            words[w]["is_proper_name"] = True
            words[w]["reason"] = "both"
        else:
            words[w] = {
                "reason": "proper_name",
                "count": total,
                "log_odds": lor,
                "rate_ratio": rr,
                "wordfreq": freq,
                "zipf": zipf,
                "is_proper_name": True,
            }
    return words


def build_distinct_lists(verses: list[dict], part: dict) -> dict:
    texts_by_book = collections.defaultdict(list)
    for v in verses:
        if v["book"] in ("Genesis", "Exodus", "Leviticus"):
            texts_by_book[v["book"]].append(v["text"])
    lists = {}
    for book in ("Genesis", "Exodus", "Leviticus"):
        lists[book] = distinct_lexicon_for_book(
            book,
            part["counts"][book],
            part["totals"][book],
            texts_by_book[book],
        )
    return lists


def exclusive_distinct_bucket(word: str, lists: dict) -> str | None:
    if word in lists["Genesis"]:
        return "Genesis"
    if word in lists["Exodus"]:
        return "Exodus"
    if word in lists["Leviticus"]:
        return "Leviticus"
    return None


def distinct_usage_for_text(content_counts: collections.Counter, lists: dict) -> dict:
    type_n = {b: 0 for b in ("Genesis", "Exodus", "Leviticus")}
    tok_n = {b: 0 for b in type_n}
    used = {b: [] for b in type_n}
    for w, k in content_counts.items():
        bucket = exclusive_distinct_bucket(w, lists)
        if not bucket:
            continue
        type_n[bucket] += 1
        tok_n[bucket] += k
        used[bucket].append((w, k))
    for b in used:
        used[b].sort(key=lambda x: (-x[1], x[0]))
    return {"types": type_n, "tokens": tok_n, "used": used}


def write_distinct_chart(book_rows: list[dict], path: Path) -> None:
    """Stacked bar: distinct-Genesis/Exodus/Leviticus token rate per 10k content tokens."""
    labels = [r["label"] for r in book_rows]
    colors = {"Genesis": "#C4A35A", "Exodus": "#D97941", "Leviticus": "#8C5A3A"}
    fig, ax = plt.subplots(figsize=(10.8, 6.4))
    x = list(range(len(labels)))
    bottoms = [0.0] * len(labels)
    width = 0.62
    for bucket in ("Genesis", "Exodus", "Leviticus"):
        vals = [r["rate"][bucket] for r in book_rows]
        ax.bar(x, vals, width, bottom=bottoms, color=colors[bucket],
               edgecolor="white", linewidth=0.5, label=bucket)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    for i, total in enumerate(bottoms):
        ax.text(i, total + max(bottoms) * 0.015, f"{total:.1f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Distinct-Torah token rate per 10,000 content tokens")
    ax.set_title(
        "Words distinctively Genesis, Exodus, or Leviticus\n"
        "vs general modern English (wordfreq), rate per 10k content tokens"
    )
    ax.legend(frameon=False, loc="upper left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def run_distinctiveness(verses: list[dict], loaded: dict, part: dict) -> dict:
    """Build distinct-word lists vs wordfreq and score the four comparison texts."""
    lists = build_distinct_lists(verses, part)
    # Content-token counters for each loaded book
    order = [
        ("alchemist", "The Alchemist"),
        ("gatsby", "The Great Gatsby"),
        ("thirty_nine_steps", "The Thirty-Nine Steps"),
        ("economy", "The Economy of God"),
    ]
    usages = {}
    book_rows = []
    content_counts = {}
    content_n = {}
    for key, label in order:
        if key not in loaded:
            continue
        cc = collections.Counter(
            w for w in loaded[key]["content_tokens"]
        )
        content_counts[key] = cc
        n = len(loaded[key]["content_tokens"])
        content_n[key] = n
        usage = distinct_usage_for_text(cc, lists)
        usages[key] = usage
        rate = {b: rate_per_10k(usage["tokens"][b], n) for b in usage["tokens"]}
        book_rows.append({
            "key": key,
            "label": label,
            "n_content": n,
            "types": usage["types"],
            "tokens": usage["tokens"],
            "rate": rate,
            "total_types": sum(usage["types"].values()),
            "total_tokens": sum(usage["tokens"].values()),
            "total_rate": rate_per_10k(sum(usage["tokens"].values()), n),
        })

    # Word-level CSV: every distinct word in any of the three lists
    all_words = sorted(
        set(lists["Genesis"]) | set(lists["Exodus"]) | set(lists["Leviticus"]),
        key=lambda w: (
            {"Genesis": 0, "Exodus": 1, "Leviticus": 2}[exclusive_distinct_bucket(w, lists)],
            -max(
                lists[b][w]["count"] if w in lists[b] else 0
                for b in ("Genesis", "Exodus", "Leviticus")
            ),
            w,
        ),
    )
    count_keys = {
        "alchemist_count": "alchemist",
        "gatsby_count": "gatsby",
        "thirty_nine_steps_count": "thirty_nine_steps",
        "economy_count": "economy",
    }
    word_rows = []
    for w in all_words:
        bucket = exclusive_distinct_bucket(w, lists)
        meta = lists[bucket][w]
        row = {
            "word": w,
            "exclusive_bucket": bucket,
            "in_genesis_distinct": int(w in lists["Genesis"]),
            "in_exodus_distinct": int(w in lists["Exodus"]),
            "in_leviticus_distinct": int(w in lists["Leviticus"]),
            "included_reason": meta["reason"],
            "is_proper_name": int(meta["is_proper_name"] or any(
                lists[b][w]["is_proper_name"] for b in ("Genesis", "Exodus", "Leviticus") if w in lists[b]
            )),
            "genesis_count": part["counts"]["Genesis"].get(w, 0),
            "exodus_count": part["counts"]["Exodus"].get(w, 0),
            "leviticus_count": part["counts"]["Leviticus"].get(w, 0),
            "genesis_log_odds": "",
            "exodus_log_odds": "",
            "leviticus_log_odds": "",
            "genesis_rate_ratio": "",
            "exodus_rate_ratio": "",
            "leviticus_rate_ratio": "",
            "wordfreq": round(meta["wordfreq"], 12),
            "zipf": round(meta["zipf"], 4),
            "alchemist_count": content_counts.get("alchemist", collections.Counter())[w],
            "gatsby_count": content_counts.get("gatsby", collections.Counter())[w],
            "thirty_nine_steps_count": content_counts.get("thirty_nine_steps", collections.Counter())[w],
            "economy_count": content_counts.get("economy", collections.Counter())[w],
        }
        for book, prefix in (("Genesis", "genesis"), ("Exodus", "exodus"), ("Leviticus", "leviticus")):
            if w in lists[book]:
                row[f"{prefix}_log_odds"] = round(lists[book][w]["log_odds"], 4)
                row[f"{prefix}_rate_ratio"] = round(lists[book][w]["rate_ratio"], 4)
                # prefer the exclusive-bucket reason but note if also in other lists
        row["n_of_4_books"] = sum(
            1 for k in ("alchemist_count", "gatsby_count", "thirty_nine_steps_count", "economy_count")
            if row[k] > 0
        )
        word_rows.append(row)

    csv_path = OUT / "distinct_genesis.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fields = list(word_rows[0].keys())
        wri = csv.DictWriter(f, fieldnames=fields)
        wri.writeheader()
        wri.writerows(word_rows)

    chart_path = OUT / "alchemist_genesis_distinct.png"
    write_distinct_chart(book_rows, chart_path)

    # Top distinct-Genesis words in The Alchemist (there may be fewer than 30)
    alc_gen = []
    if "alchemist" in usages:
        for w, k in usages["alchemist"]["used"]["Genesis"]:
            alc_gen.append({
                "word": w,
                "alchemist_count": k,
                "gatsby_count": content_counts.get("gatsby", collections.Counter())[w],
                "thirty_nine_steps_count": content_counts.get("thirty_nine_steps", collections.Counter())[w],
                "economy_count": content_counts.get("economy", collections.Counter())[w],
                "genesis_log_odds": lists["Genesis"][w]["log_odds"],
                "included_reason": lists["Genesis"][w]["reason"],
                "is_proper_name": lists["Genesis"][w]["is_proper_name"],
            })

    shared = [r for r in word_rows if r["n_of_4_books"] >= 2]
    shared.sort(key=lambda r: (
        -r["n_of_4_books"],
        -(r["alchemist_count"] + r["gatsby_count"] + r["thirty_nine_steps_count"] + r["economy_count"]),
        r["word"],
    ))

    list_sizes = {
        b: {
            "n": len(lists[b]),
            "log_odds": sum(1 for v in lists[b].values() if v["reason"] in ("log_odds", "both")),
            "names_only": sum(1 for v in lists[b].values() if v["reason"] == "proper_name"),
            "both": sum(1 for v in lists[b].values() if v["reason"] == "both"),
        }
        for b in ("Genesis", "Exodus", "Leviticus")
    }

    print("DISTINCTIVENESS vs wordfreq English")
    print(f"  threshold: min count {DISTINCT_MIN_COUNT}, log-odds >= {DISTINCT_LOG_ODDS_THRESHOLD}; "
          f"plus proper names")
    for b, s in list_sizes.items():
        print(f"  {b} list: {s['n']} types (log-odds {s['log_odds']}, names-only {s['names_only']}, both {s['both']})")
    for row in book_rows:
        print(f"  {row['label']}: content={row['n_content']}")
        for b in ("Genesis", "Exodus", "Leviticus"):
            print(f"    {b}: types={row['types'][b]} tokens={row['tokens'][b]} "
                  f"rate/10k={row['rate'][b]:.2f}")
        print(f"    TOTAL types={row['total_types']} tokens={row['total_tokens']} "
              f"rate/10k={row['total_rate']:.2f}")
    print(f"  wrote {csv_path} ({len(word_rows)} words) and {chart_path}")

    return {
        "lists": lists,
        "list_sizes": list_sizes,
        "book_rows": book_rows,
        "word_rows": word_rows,
        "alc_gen_top": alc_gen,
        "shared": shared,
        "threshold": {
            "min_count": DISTINCT_MIN_COUNT,
            "log_odds": DISTINCT_LOG_ODDS_THRESHOLD,
            "ref": "wordfreq 3.1.1 English, n_ref=1e9, 0.5-smoothed log-odds and rate ratio",
        },
    }


def write_source_chart(rows_by_label: dict, path: Path) -> None:
    """Stacked bar: exclusive source buckets for non-stopword types."""
    labels = list(rows_by_label.keys())
    colors = {
        "Genesis": "#C4A35A",
        "Exodus": "#D97941",
        "Leviticus": "#8C5A3A",
        "rest of OT": "#6B8F71",
        "NT only": "#4C6A8C",
        "not in KJV": "#C9C4BB",
    }
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    x = range(len(labels))
    bottoms = [0.0] * len(labels)
    width = 0.62
    for bucket in SOURCE_LABELS:
        vals = [rows_by_label[lab]["type_bucket_pct"][bucket] for lab in labels]
        ax.bar(x, vals, width, bottom=bottoms, color=colors[bucket], edgecolor="white", linewidth=0.4, label=bucket)
        bottoms = [b + v for b, v in zip(bottoms, vals)]
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("Share of non-stopword word types (%)")
    ax.set_ylim(0, 100)
    ax.set_title("Where does the vocabulary come from?\nExclusive KJV source of each non-stopword word type")
    ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> dict:
    print("Loading KJV verses…")
    verses = load_kjv_verses()
    sets = book_token_sets(verses)
    kjv_counts, kjv_n, part = kjv_token_counts(verses)
    print(f"  KJV tokens={kjv_n:,} types={len(kjv_counts):,}  "
          f"Gen types={len(sets['Genesis'])} Exod={len(sets['Exodus'])} Lev={len(sets['Leviticus'])}")

    # ---- load books ----
    require_private_texts("alchemist.txt", "economy.txt")
    loaded = {}
    for key, meta in list(BOOKS.items()) + list(BASELINES.items()):
        if not meta["path"].exists():
            print("MISSING", meta["path"])
            continue
        text = load_book(meta["path"], meta["kind"])
        info = analyze_text(text)
        info.update(meta)
        info["key"] = key
        loaded[key] = info
        print(f"  {meta['label']}: tokens={info['n_tokens']:,} types={info['n_types']:,} "
              f"content_tokens={len(info['content_tokens']):,}")

    # Combined baseline (for log-odds)
    base_tokens = []
    base_counts = collections.Counter()
    for k in BASELINES:
        if k in loaded:
            base_tokens.extend(loaded[k]["tokens"])
            base_counts.update(loaded[k]["counts"])
    base_n = len(base_tokens)

    # ---- source classification for Alchemist + baselines ----
    source_stats = {}
    for key, info in loaded.items():
        content_types = sorted({w for w in info["counts"] if w not in STOPWORDS})
        content_toks = info["content_tokens"]
        source_stats[key] = exclusive_bucket_shares(content_toks, content_types, sets)
        source_stats[key]["label"] = info["label"]
        source_stats[key]["content_types"] = content_types

    # ---- per-word table for The Alchemist ----
    alc = loaded["alchemist"]
    gen_c, ex_c, lev_c = part["counts"]["Genesis"], part["counts"]["Exodus"], part["counts"]["Leviticus"]
    gen_n, ex_n, lev_n = part["totals"]["Genesis"], part["totals"]["Exodus"], part["totals"]["Leviticus"]

    word_rows = []
    for w, c in alc["counts"].most_common():
        if w in STOPWORDS:
            continue
        bucket = classify_word(w, sets)
        row = {
            "word": w,
            "alchemist_count": c,
            "alchemist_rate_per_10k": round(rate_per_10k(c, alc["n_tokens"]), 4),
            "source_bucket": bucket,
            "in_Genesis": int(w in sets["Genesis"]),
            "in_Exodus": int(w in sets["Exodus"]),
            "in_Leviticus": int(w in sets["Leviticus"]),
            "in_OT": int(w in sets["OT"]),
            "in_NT": int(w in sets["NT"]),
            "in_KJV": int(w in sets["KJV"]),
            "genesis_count": gen_c.get(w, 0),
            "exodus_count": ex_c.get(w, 0),
            "leviticus_count": lev_c.get(w, 0),
            "kjv_count": kjv_counts.get(w, 0),
            "baseline_count": base_counts.get(w, 0),
            "gatsby_count": loaded.get("gatsby", {}).get("counts", {}).get(w, 0),
            "thirty_nine_steps_count": loaded.get("thirty_nine_steps", {}).get("counts", {}).get(w, 0),
            "log_odds_genesis_vs_baseline": "",
            "rate_ratio_genesis_vs_baseline": "",
            "log_odds_exodus_vs_baseline": "",
            "rate_ratio_exodus_vs_baseline": "",
            "log_odds_leviticus_vs_baseline": "",
            "rate_ratio_leviticus_vs_baseline": "",
        }
        if w in sets["Genesis"]:
            row["log_odds_genesis_vs_baseline"] = round(log_odds(gen_c.get(w, 0), gen_n, base_counts.get(w, 0), base_n), 4)
            row["rate_ratio_genesis_vs_baseline"] = round(rate_ratio(gen_c.get(w, 0), gen_n, base_counts.get(w, 0), base_n), 4)
        if w in sets["Exodus"]:
            row["log_odds_exodus_vs_baseline"] = round(log_odds(ex_c.get(w, 0), ex_n, base_counts.get(w, 0), base_n), 4)
            row["rate_ratio_exodus_vs_baseline"] = round(rate_ratio(ex_c.get(w, 0), ex_n, base_counts.get(w, 0), base_n), 4)
        if w in sets["Leviticus"]:
            row["log_odds_leviticus_vs_baseline"] = round(log_odds(lev_c.get(w, 0), lev_n, base_counts.get(w, 0), base_n), 4)
            row["rate_ratio_leviticus_vs_baseline"] = round(rate_ratio(lev_c.get(w, 0), lev_n, base_counts.get(w, 0), base_n), 4)
        word_rows.append(row)

    with (OUT / "alchemist_genesis.csv").open("w", newline="", encoding="utf-8") as f:
        fields = list(word_rows[0].keys())
        wri = csv.DictWriter(f, fieldnames=fields)
        wri.writeheader()
        wri.writerows(word_rows)

    def top_distinct(flag, lor_key, n=25):
        cand = [r for r in word_rows if r[flag] and r[lor_key] != ""]
        cand.sort(key=lambda r: -float(r[lor_key]))
        return cand[:n]

    distinct = {
        "Genesis": top_distinct("in_Genesis", "log_odds_genesis_vs_baseline"),
        "Exodus": top_distinct("in_Exodus", "log_odds_exodus_vs_baseline"),
        "Leviticus": top_distinct("in_Leviticus", "log_odds_leviticus_vs_baseline"),
    }

    # ---- shared n-grams 2–5 with Gen / Exod / Lev ----
    def corpus_ngrams(token_lists: list[list[str]], ns=range(2, 6)):
        pos = collections.defaultdict(list)  # ng -> list of locations (filled by caller)
        counts = collections.Counter()
        for n in ns:
            for toks in token_lists:
                for ng in ngrams(toks, n):
                    if ngram_has_content(ng):
                        counts[ng] += 1
        return counts

    def verse_ngrams(book: str):
        counts = collections.Counter()
        locs = collections.defaultdict(list)
        for v in verses:
            if v["book"] != book:
                continue
            for n in range(2, 6):
                for ng in ngrams(v["tokens"], n):
                    if ngram_has_content(ng):
                        counts[ng] += 1
                        if len(locs[ng]) < 8:
                            locs[ng].append(v["ref"])
        return counts, locs

    alc_ng_counts = collections.Counter()
    # don't cross huge distances: use paragraph-ish chunks
    chunks = [tokenize(p) for p in re.split(r"\n\s*\n", alc["text"]) if p.strip()]
    for n in range(2, 6):
        for toks in chunks:
            for ng in ngrams(toks, n):
                if ngram_has_content(ng):
                    alc_ng_counts[ng] += 1

    shared_ng = {}
    for book in ("Genesis", "Exodus", "Leviticus"):
        bcounts, locs = verse_ngrams(book)
        items = []
        for ng, ac in alc_ng_counts.items():
            if ng in bcounts:
                items.append({
                    "ngram": " ".join(ng),
                    "n": len(ng),
                    "alchemist_count": ac,
                    "book_count": bcounts[ng],
                    "refs": "; ".join(locs[ng]),
                    "content_words": sum(1 for t in ng if t not in STOPWORDS),
                })
        # Prefer longer, then more content words, then rarer in the Bible book
        items.sort(key=lambda r: (-r["n"], -r["content_words"], r["book_count"], -r["alchemist_count"], r["ngram"]))
        shared_ng[book] = items

    parallels = build_story_parallels(alc["text"], verses)

    # ---- chart ----
    chart_data = {}
    # Order: Alchemist, then baselines
    for key in ["alchemist", "gatsby", "thirty_nine_steps"]:
        if key in source_stats:
            chart_data[source_stats[key]["label"]] = source_stats[key]
    write_source_chart(chart_data, OUT / "alchemist_genesis.png")

    # ---- distinctiveness vs general modern English (wordfreq) ----
    distinct_en = run_distinctiveness(verses, loaded, part)

    # ---- summary markdown (written later with computed numbers only) ----
    stats = {
        "loaded": loaded,
        "source_stats": source_stats,
        "word_rows": word_rows,
        "distinct": distinct,
        "shared_ng": shared_ng,
        "parallels": parallels,
        "kjv_n": kjv_n,
        "sets": sets,
        "part": part,
        "base_n": base_n,
        "verses": verses,
        "kjv_counts": kjv_counts,
        "distinct_en": distinct_en,
    }
    return stats


if __name__ == "__main__":
    stats = main()
    print("SOURCE ANALYSIS CORE DONE")
    for k, s in stats["source_stats"].items():
        c = s["cumulative"]
        print(f"== {s['label']} types={s['n_types']} content_tokens={s['n_tokens']}")
        print("  exclusive types %", {b: round(s['type_bucket_pct'][b], 2) for b in SOURCE_LABELS})
        print("  exclusive tokens %", {b: round(s['tok_bucket_pct'][b], 2) for b in SOURCE_LABELS})
        print("  cumulative types  Gen {in_Genesis_types:.2f} Ex {in_Exodus_types:.2f} Lev {in_Leviticus_types:.2f} "
              "Torah {in_GenExodLev_types:.2f} OT {in_OT_types:.2f} KJV {in_KJV_types:.2f}".format(**c))
        print("  cumulative tokens Gen {in_Genesis_tokens:.2f} Ex {in_Exodus_tokens:.2f} Lev {in_Leviticus_tokens:.2f} "
              "Torah {in_GenExodLev_tokens:.2f} OT {in_OT_tokens:.2f} KJV {in_KJV_tokens:.2f}".format(**c))
    print("Distinct Gen sample", [r["word"] for r in stats["distinct"]["Genesis"][:15]])
    print("Ngrams Gen", len(stats["shared_ng"]["Genesis"]), "Exod", len(stats["shared_ng"]["Exodus"]), "Lev", len(stats["shared_ng"]["Leviticus"]))
    print("Parallels", len(stats["parallels"]))
