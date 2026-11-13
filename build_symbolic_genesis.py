#!/usr/bin/env python3
"""Count a biblical lexicon across The Alchemist, the control novels, and the KJV.

The word list is drawn mainly from Genesis, with a few terms whose King James
source is Exodus, Leviticus, Job, or 2 Samuel (marked on each row). This script
also re-checks corpus sizes and the Abraham-cycle distinctiveness rates that
appear on the report. Copyrighted books must be supplied in data/private/.
"""
from __future__ import annotations

import csv
import collections
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from textutil import (  # noqa: E402
    STOPWORDS, OUTPUT_DIR, SOURCE_CSV, load_book, tokenize, normalize_text,
    require_private_texts,
)
from compare import (  # noqa: E402
    log_odds, wordfreq_scores, mid_verse_cap_counts,
    DISTINCT_MIN_COUNT, DISTINCT_LOG_ODDS_THRESHOLD,
    NAME_ZIPF_COMMON, NAME_COMMON_MIN_LOR, NAME_HAPAX_ZIPF_MAX,
    NAME_MIN_LENGTH, NAME_DENY, BOOKS, BASELINES, rate_per_10k,
)

OUT = OUTPUT_DIR
OUT.mkdir(exist_ok=True)
VERSES_CSV = SOURCE_CSV

# ---------------------------------------------------------------------------
# Lexicon: Bible (whole Genesis) is the source of the list.
# Leviticus is added for Urim, Thummim, and the breastplate (Lev 8:8).
# Coelho gem terms that are not in Genesis are included with an honest source note.
# Lee is the interpretive key where he defines a term; not the source of the list.
# ---------------------------------------------------------------------------

# forms: lowercase token forms (already tokenized).
# regex: applied to normalize_text(text), case-insensitive.
# well uses a noun-like regex so "as well" / dialogue "Well," are excluded.
# jordan_novel: river/plain pattern, so Gatsby's Jordan Baker is not counted.
# For KJV/Economy, the token "jordan" is counted (no Jordan Baker problem).

WELL_RE = re.compile(
    r"\bwells\b|\bwell\s+of\b|"
    r"\b(?:the|a|an|this|that|his|her|their|our|your|my|its)\s+wells?\b",
    re.I,
)
# Subtract adverbial "that well yet/enough" (Alchemist), but keep noun "that well" (Genesis 29:2).
WELL_ADVERB_RE = re.compile(r"\bthat\s+well\s+(?:yet|enough)\b", re.I)
JORDAN_NOVEL_RE = re.compile(
    r"\b(?:the|this)\s+jordan\b|"
    r"\b(?:plain|side)\s+of\s+jordan\b|"
    r"\bbeyond\s+jordan\b|"
    r"\bjordan\s+river\b",
    re.I,
)
TREE_OF_LIFE_RE = re.compile(r"\btree\s+of\s+life\b", re.I)
TREE_OF_KNOWLEDGE_RE = re.compile(
    r"\btree\s+of(?:\s+the)?\s+knowledge(?:\s+of\s+good\s+and\s+evil)?\b",
    re.I,
)
PRECIOUS_STONES_RE = re.compile(r"\bprecious\s+stones?\b", re.I)
FINE_LINEN_RE = re.compile(r"\bfine\s+linen\b", re.I)
BREASTPLATE_RE = re.compile(r"\bbreast\s*plates?\b", re.I)

TERMS = [
    # --- architecture / places ---
    dict(term="city", category="architecture / places", forms=["city", "cities"],
         preferred="Genesis 4:17"),
    dict(term="tower", category="architecture / places", forms=["tower", "towers"],
         preferred="Genesis 11:4"),
    dict(term="altar", category="architecture / places", forms=["altar", "altars"],
         preferred="Genesis 12:7"),
    dict(term="tent", category="architecture / places", forms=["tent", "tents"],
         preferred="Genesis 12:8"),
    dict(term="well", category="architecture / places", regex=WELL_RE,
         preferred="Genesis 24:11"),
    dict(term="gate", category="architecture / places", forms=["gate", "gates"],
         preferred="Genesis 22:17"),
    dict(term="house", category="architecture / places", forms=["house", "houses"],
         preferred="Genesis 12:1"),
    dict(term="door", category="architecture / places", forms=["door", "doors"],
         preferred="Genesis 18:1"),
    dict(term="pillar", category="architecture / places", forms=["pillar", "pillars"],
         preferred="Genesis 28:18"),
    dict(term="garden", category="architecture / places", forms=["garden", "gardens"],
         preferred="Genesis 2:8"),
    dict(term="Salem", category="architecture / places", forms=["salem"],
         preferred="Genesis 14:18"),
    dict(term="Egypt", category="architecture / places",
         forms=["egypt", "egyptian", "egyptians"],
         preferred="Genesis 12:10"),
    dict(term="Canaan", category="architecture / places",
         forms=["canaan", "canaanite", "canaanites"],
         preferred="Genesis 12:5"),
    dict(term="Eden", category="architecture / places", forms=["eden"],
         preferred="Genesis 2:8"),
    dict(term="Ur", category="architecture / places", forms=["ur"],
         preferred="Genesis 11:31"),
    dict(term="Bethel", category="architecture / places", forms=["bethel"],
         preferred="Genesis 12:8"),
    dict(term="Jordan", category="architecture / places", forms=["jordan"],
         novel_regex=JORDAN_NOVEL_RE, preferred="Genesis 13:10"),

    # --- materials / gems ---
    dict(term="gold", category="materials / gems", forms=["gold", "golden"],
         preferred="Genesis 2:12"),
    dict(term="silver", category="materials / gems", forms=["silver"],
         preferred="Genesis 13:2"),
    dict(term="stone", category="materials / gems", forms=["stone", "stones"],
         preferred="Genesis 28:18",
         subtract_regex=PRECIOUS_STONES_RE),  # counted separately
    dict(term="brass", category="materials / gems", forms=["brass", "brazen"],
         preferred="Genesis 4:22"),
    dict(term="iron", category="materials / gems", forms=["iron"],
         preferred="Genesis 4:22"),
    dict(term="wood", category="materials / gems", forms=["wood", "woods", "wooden"],
         preferred="Genesis 22:6"),
    dict(term="linen", category="materials / gems", forms=["linen"],
         preferred="Genesis 41:42"),
    dict(term="onyx", category="materials / gems", forms=["onyx"],
         preferred="Genesis 2:12"),
    dict(term="bdellium", category="materials / gems", forms=["bdellium"],
         preferred="Genesis 2:12"),
    dict(term="jewels", category="materials / gems", forms=["jewel", "jewels"],
         preferred="Genesis 24:53"),
    dict(term="precious stones", category="materials / gems", regex=PRECIOUS_STONES_RE,
         preferred=None,  # not in Genesis
         source_note="The phrase “precious stones” does not occur in Genesis (Genesis 24:53 has “jewels of silver, and jewels of gold” and “precious things”). It occurs elsewhere in the KJV."),
    dict(term="crystal", category="materials / gems", forms=["crystal", "crystals"],
         preferred=None,
         source_note="Crystal does not occur in Genesis or Leviticus. In the KJV it appears in Job, Ezekiel, and Revelation."),
    dict(term="emerald", category="materials / gems", forms=["emerald", "emeralds"],
         preferred=None,
         source_note="Emerald does not occur in Genesis or Leviticus. It first appears in the high priest’s breastplate in Exodus 28:18 (and again in Exodus 39:11)."),
    dict(term="Urim", category="materials / gems", forms=["urim"],
         preferred=None,
         source_note="Urim is not in Genesis. Leviticus 8:8 places the Urim and the Thummim in the breastplate at Aaron’s consecration. The instructions for making them are in Exodus 28:30."),
    dict(term="Thummim", category="materials / gems", forms=["thummim"],
         preferred=None,
         source_note="Thummim is not in Genesis. Leviticus 8:8 is the splash verse; the instructions are in Exodus 28:30."),

    # --- colors ---
    dict(term="white", category="colors", forms=["white"],
         preferred="Genesis 30:35"),
    dict(term="black", category="colors", forms=["black"],
         preferred=None,
         source_note="The color word “black” does not occur in Genesis. It appears in Leviticus 13 in a skin-disease law (“black hair”), not as a gem color. Coelho describes Urim and Thummim as “a white stone and a black stone”; the King James text names the stones but does not give their colors."),
    dict(term="red", category="colors", forms=["red"],
         preferred="Genesis 25:25"),
    dict(term="speckled", category="colors", forms=["speckled"],
         preferred="Genesis 30:32"),
    dict(term="spotted", category="colors", forms=["spotted"],
         preferred="Genesis 30:32"),
    dict(term="ringstraked", category="colors", forms=["ringstraked", "ringstreaked"],
         preferred="Genesis 30:35"),
    dict(term="brown", category="colors", forms=["brown"],
         preferred="Genesis 30:32"),
    dict(term="grisled", category="colors", forms=["grisled", "grizzled"],
         preferred="Genesis 31:10"),
    dict(term="scarlet", category="colors", forms=["scarlet"],
         preferred="Genesis 38:28"),
    dict(term="green", category="colors", forms=["green"],
         preferred="Genesis 30:37"),

    # --- nature / elements ---
    dict(term="tree", category="nature / elements", forms=["tree", "trees"],
         preferred="Genesis 2:9",
         subtract_regexes=[TREE_OF_LIFE_RE, TREE_OF_KNOWLEDGE_RE]),
    dict(term="tree of life", category="nature / elements", regex=TREE_OF_LIFE_RE,
         preferred="Genesis 2:9"),
    dict(term="tree of knowledge", category="nature / elements", regex=TREE_OF_KNOWLEDGE_RE,
         preferred="Genesis 2:9"),
    dict(term="star", category="nature / elements", forms=["star", "stars"],
         preferred="Genesis 15:5"),
    dict(term="sand", category="nature / elements", forms=["sand"],
         preferred="Genesis 22:17"),
    dict(term="dust", category="nature / elements", forms=["dust"],
         preferred="Genesis 13:16"),
    dict(term="desert / wilderness", category="nature / elements",
         forms=["desert", "deserts", "wilderness", "wildernesses"],
         preferred="Genesis 16:7",
         source_note="Genesis uses “wilderness,” not “desert.” The two are counted together because The Alchemist’s setting word is “desert.”"),
    dict(term="river", category="nature / elements", forms=["river", "rivers"],
         preferred="Genesis 2:10"),
    dict(term="light", category="nature / elements", forms=["light", "lights"],
         preferred="Genesis 1:3"),
    dict(term="darkness", category="nature / elements", forms=["darkness"],
         preferred="Genesis 1:2"),
    dict(term="flood", category="nature / elements", forms=["flood", "floods"],
         preferred="Genesis 6:17"),
    dict(term="fire", category="nature / elements", forms=["fire", "fires"],
         preferred="Genesis 22:6"),
    dict(term="cloud", category="nature / elements", forms=["cloud", "clouds"],
         preferred="Genesis 9:13"),
    dict(term="mountain", category="nature / elements", forms=["mountain", "mountains"],
         preferred="Genesis 22:2"),
    dict(term="rain", category="nature / elements", forms=["rain", "rains"],
         preferred="Genesis 7:12"),
    dict(term="wind", category="nature / elements", forms=["wind", "winds"],
         preferred="Genesis 8:1"),
    dict(term="fountain", category="nature / elements", forms=["fountain", "fountains"],
         preferred="Genesis 16:7"),

    # --- objects ---
    dict(term="treasure", category="objects", forms=["treasure", "treasures"],
         preferred="Genesis 43:23"),
    dict(term="ring", category="objects", forms=["ring", "rings"],
         preferred="Genesis 41:42"),
    dict(term="coat", category="objects", forms=["coat", "coats"],
         preferred="Genesis 37:3"),
    dict(term="ark", category="objects", forms=["ark"],
         preferred="Genesis 6:14",
         source_note="In Genesis the word denotes Noah’s vessel. Witness Lee’s typological definition refers to the ark of the covenant (Exodus), a different object."),
    dict(term="cup", category="objects", forms=["cup", "cups"],
         preferred="Genesis 44:2"),
    dict(term="staff", category="objects", forms=["staff"],
         preferred="Genesis 32:10"),
    dict(term="sword", category="objects", forms=["sword", "swords"],
         preferred="Genesis 3:24"),
    dict(term="bow", category="objects", forms=["bow", "bows"],
         preferred="Genesis 9:13",
         source_note="Genesis uses “bow” both for the covenant rainbow (Genesis 9:13) and for a weapon."),
    dict(term="bracelets", category="objects", forms=["bracelet", "bracelets"],
         preferred="Genesis 24:22"),
    dict(term="earring", category="objects", forms=["earring", "earrings"],
         preferred="Genesis 24:22"),
    dict(term="vessels", category="objects", forms=["vessel", "vessels"],
         preferred="Genesis 43:11"),
    dict(term="veil", category="objects", forms=["veil", "veils", "vail", "vails"],
         preferred="Genesis 24:65"),
    dict(term="breastplate", category="objects", regex=BREASTPLATE_RE,
         preferred=None,
         source_note="Breastplate is not in Genesis. Leviticus 8:8 is the consecration scene. The construction and the twelve gemstones are described in Exodus 28:15–30."),
]

# Fallback Bible refs when the term is not in Genesis
FALLBACK_REF = {
    "Urim": "Leviticus 8:8",
    "Thummim": "Leviticus 8:8",
    "breastplate": "Leviticus 8:8",
    "emerald": "Exodus 28:18",
    "crystal": "Job 28:17",  # verify
    "precious stones": "2 Samuel 12:30",  # verify first occurrence
    "black": "Leviticus 13:31",
}

# Existing Lee quotes (term display -> meaning, quote, chapter) from the prior Economy of God pass.
# Only used if the quote still matches the text; new terms are searched in economy.txt.
LEE_KNOWN = {
    "treasure": (
        "The image of Christ as the treasure held in earthen vessels.",
        "This very image of Christ is the treasure in the earthen vessels.",
        "5",
    ),
    "gold": (
        "Typifies divinity, the divine nature wrought into and upon humanity.",
        "the gold overlaying the boards signifies divinity, the divine nature.",
        "21",
    ),
    "Egypt": (
        "The worldly starting place, corresponding to the outer court, before the Passover deliverance.",
        "Are we in Egypt? in the wilderness? or in Canaan?",
        "18",
    ),
    "well": (
        "Typifies Christ within us, the well of living water that must be dug.",
        "While the rock is Christ on the cross, the well is Christ within us (John 4:14).",
        "10",
    ),
    "white": (
        "The court linen’s testimony: inside the church’s line, everything is purged and white.",
        "Outside this line everything is black, but within this line everything is white.",
        "21",
    ),
    "light": (
        "The lampstand typifies Christ as the light of life, shining within.",
        "The candlestick, or the lampstand, typifies Christ as the light of life.",
        "21",
    ),
    "red": (
        "The color of the rams’ skins: the shedding of blood in redemption.",
        "The color red means the shedding of blood in Christ’s redemptive work.",
        "22",
    ),
    "silver": (
        "Typifies redemption, the joining and covering of God’s building.",
        "Silver typifies redemption.",
        "21",
    ),
    "veil": (
        "Typifies the flesh, which must be riven to enter the Holiest.",
        "the veil, which typifies the flesh (Heb. 10:20), must be riven and broken.",
        "3",
    ),
    "linen": (
        "Fine linen symbolizes the humanity of Christ: fine, strong, without crudeness.",
        "the fine linen, which symbolizes the humanity of Christ with all His fine characteristics",
        "22",
    ),
    "tree of life": (
        "Signifies God Himself in Christ as our life.",
        "the tree of life signifies God Himself in Christ as our life.",
        "12",
    ),
    "tree of knowledge": (
        "Represents Satan, the source of death.",
        "This tree represents nothing else than Satan, the source of death.",
        "12",
    ),
    "desert / wilderness": (
        "Typifies wandering in the soul after salvation, short of entering the spirit.",
        "What does this typify? It means that many Christians after being saved are simply wandering in the soul.",
        "3",
    ),
    "Canaan": (
        "The land of rest, a type of the all-inclusive Christ in our spirit.",
        "Christ is the good land of Canaan, and He is our rest.",
        "3",
    ),
    "altar": (
        "In the outer court, typifies the cross of Christ and His all-inclusive death.",
        "In the outer court there is the altar, which typifies the cross of Christ",
        "21",
    ),
    "ark": (
        "The type of Christ Himself, hidden in the Holiest of all (the ark of the covenant, not Noah’s ark).",
        "The Holiest of all contains one thing, the ark, the type of Christ Himself.",
        "21",
    ),
    "wood": (
        "Signifies humanity, the human nature of the tabernacle boards.",
        "The wood of the boards (Exo. 26:15) signifies humanity, the human nature.",
        "21",
    ),
    "pillar": (
        "The church as the pillar and ground of the truth.",
        "the house of God, which is the church of the living God, the pillar and ground of the truth.",
        "23",
    ),
    "scarlet": (
        "The tabernacle color that stands for redemption.",
        "Blue means heavenly, purple means royalty, and scarlet stands for redemption.",
        "22",
    ),
}


def load_verses() -> list[dict]:
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
            })
    return verses


def load_corpora() -> dict:
    require_private_texts("alchemist.txt", "economy.txt")
    out = {}
    specs = {**BOOKS, **BASELINES}
    for key, spec in specs.items():
        if not spec["path"].exists():
            raise SystemExit(f"Missing required text: {spec['path']}")
        text = load_book(spec["path"], spec["kind"])
        tokens = tokenize(text)
        content = [t for t in tokens if t not in STOPWORDS]
        out[key] = {
            "label": spec["label"],
            "text": text,
            "norm": normalize_text(text),
            "tokens": tokens,
            "content": content,
            "n_tokens": len(tokens),
            "n_content": len(content),
            "counts": collections.Counter(tokens),
        }
    return out


def match_space(text: str) -> str:
    """Normalize for term matching: treat dashes as separators so
    'crystal—he' counts as crystal, unlike tokenize() which deletes em-dashes
    and would glue the words together."""
    t = text.replace("\u2019", "'").replace("\u2018", "'")
    # En-dashes join KJV names (Beth–el → Bethel). Em-dashes separate clauses (crystal—he).
    t = t.replace("\u2013", "").replace("\u2014", " ").replace("-", " ")
    t = t.replace("Æ", "Ae").replace("æ", "ae")
    t = t.replace("[but]", "but").replace("[", " ").replace("]", " ")
    t = re.sub(r"[\u0590-\u05FF]+", " ", t)
    t = re.sub(r"([A-Za-z]+)'s\b", r"\1", t)
    t = re.sub(r"([A-Za-z]+s)'\b", r"\1", t)
    t = re.sub(r"[^A-Za-z]+", " ", t)
    return t.strip()


def count_forms_in_text(text: str, forms: list[str]) -> int:
    if not forms:
        return 0
    pat = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(f) for f in sorted(forms, key=len, reverse=True)), re.I)
    return len(pat.findall(match_space(text)))


def count_regex(text: str, pat: re.Pattern) -> int:
    return len(pat.findall(match_space(text))) if pat.pattern.find("well") == -1 else len(pat.findall(re.sub(r"\s+", " ", text.replace("\u2013","").replace("\u2014"," ").replace("-"," "))))


def count_well(text: str) -> int:
    t = re.sub(r"\s+", " ", text.replace("\u2013", "").replace("\u2014", " ").replace("-", " "))
    n = len(WELL_RE.findall(t))
    n -= len(WELL_ADVERB_RE.findall(t))
    return max(0, n)


def count_term_in_text(term: dict, text: str, tokens: list[str], *, is_novel: bool) -> int:
    if term["term"] == "well":
        n = count_well(text)
    elif is_novel and term.get("novel_regex") is not None:
        t = re.sub(r"\s+", " ", text.replace("\u2013","").replace("\u2014"," ").replace("-"," "))
        n = len(term["novel_regex"].findall(t))
    elif term.get("regex") is not None:
        n = count_regex(text, term["regex"])
    else:
        n = count_forms_in_text(text, term.get("forms") or [])
    for pat in term.get("subtract_regexes") or []:
        n -= count_regex(text, pat)
    if term.get("subtract_regex") is not None:
        n -= count_regex(text, term["subtract_regex"])
    return max(0, n)


def count_term_in_verses(term: dict, verses: list[dict]) -> dict[str, int]:
    """Return raw counts for Genesis, Exodus, Leviticus, and whole KJV."""
    buckets = {"Genesis": 0, "Exodus": 0, "Leviticus": 0, "KJV": 0}
    extra_sub = [p for p in (term.get("subtract_regexes") or [])]
    if term.get("subtract_regex") is not None:
        extra_sub.append(term["subtract_regex"])
    for v in verses:
        n = count_term_in_text(term, v["text"], v["tokens"], is_novel=False)
        # For Jordan, count every KJV "jordan" token (no Baker collision).
        if term["term"] == "Jordan":
            n = count_forms_in_text(v["text"], term.get("forms") or [])
        n = max(0, n)
        if n:
            buckets["KJV"] += n
            if v["book"] in buckets:
                buckets[v["book"]] += n
    return buckets


def first_verses_for(term: dict, verses: list[dict], limit=8) -> list[dict]:
    hits = []
    is_regex = term.get("regex") is not None
    forms = term.get("forms") or []
    for v in verses:
        if is_regex:
            ok = bool(term["regex"].search(normalize_text(v["text"])))
        else:
            ok = any(t in forms for t in v["tokens"])
        if ok:
            hits.append(v)
            if len(hits) >= 30:
                break
    return hits


def choose_ref(term: dict, verses: list[dict]) -> tuple[str, str]:
    """Return (ref, short quote). Prefer a listed Genesis verse; else first Genesis hit; else fallback."""
    preferred = term.get("preferred")
    by_ref = {v["ref"]: v for v in verses}
    if preferred and preferred in by_ref:
        v = by_ref[preferred]
        return v["ref"], short_quote(v["text"])
    # first Genesis hit
    for v in verses:
        if v["book"] != "Genesis":
            continue
        if term.get("regex") is not None:
            if term["regex"].search(normalize_text(v["text"])):
                return v["ref"], short_quote(v["text"])
        elif any(t in (term.get("forms") or []) for t in v["tokens"]):
            return v["ref"], short_quote(v["text"])
    # fallback book+ref
    fb = FALLBACK_REF.get(term["term"])
    if fb and fb in by_ref:
        v = by_ref[fb]
        return v["ref"], short_quote(v["text"])
    # first hit anywhere
    for v in verses:
        if term.get("regex") is not None:
            if term["regex"].search(normalize_text(v["text"])):
                return v["ref"], short_quote(v["text"])
        elif any(t in (term.get("forms") or []) for t in v["tokens"]):
            return v["ref"], short_quote(v["text"])
    return "", ""


_ABBREV_END = re.compile(
    r"\b(?:Exo|Exod|Gen|Lev|Num|Deut|Josh|Judg|Sam|Kgs|Chr|Neh|Esth|Psa|Ps|"
    r"Prov|Eccl|Isa|Jer|Lam|Ezek|Dan|Hos|Joel|Amos|Obad|Jonah|Mic|Nah|"
    r"Hab|Zeph|Hag|Zech|Mal|Matt|Mat|Mk|Lk|Jn|Rom|Cor|Gal|Eph|Phil|Col|"
    r"Thes|Thess|Tim|Tit|Phlm|Heb|Jas|Pet|Rev|ch|cf|vs|v)\.$",
    re.I,
)


def one_sentence(text: str, max_words: int = 22) -> str:
    """Keep a single short sentence (or a clipped clause) for fair-use snippets."""
    t = re.sub(r"\s+", " ", text).strip()
    if not t:
        return ""
    for m in re.finditer(r"[.!?]", t):
        prefix = t[: m.end()]
        if _ABBREV_END.search(prefix) or re.search(r"\b[A-Z]\.$", prefix):
            continue
        rest = t[m.end():]
        if rest == "" or rest[:1].isspace() or rest[:1] in {chr(34), chr(39), chr(0x201c), chr(0x201d), chr(0x2018), chr(0x2019)}:
            t = prefix.strip()
            break
    return short_quote(t, max_words=max_words)


def short_quote(text: str, max_words: int = 22) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    words = t.split()
    if len(words) <= max_words:
        return t
    return " ".join(words[:max_words]).rstrip(",;:") + "…"


def sentence_window(text: str, pat: re.Pattern, max_sentences=1) -> list[str]:
    """Return one short sentence containing the pattern (fair-use length)."""
    # Work on a whitespace-normalized copy, but keep indices via normalized text.
    norm = re.sub(r"\s+", " ", text)
    out = []
    for m in pat.finditer(norm):
        # expand to nearest sentence-ish bounds
        start = m.start()
        end = m.end()
        left = max(0, start - 200)
        right = min(len(norm), end + 220)
        window = norm[left:right]
        # trim to a sentence if possible
        # find start
        s = 0
        for i, ch in enumerate(window):
            if i == 0:
                continue
            if window[i-1] in ".!?””'\" " and i+1 < len(window) and window[i].isupper():
                # possible sentence start; keep last one before the match
                abs_i = left + i
                if abs_i <= start:
                    s = i
        e = len(window)
        m_in = start - left
        after = window[m_in:]
        cut = re.search(r"(?<=[.!?])\s+(?=[A-Z“\"])", after)
        if cut:
            e = m_in + cut.end()
        sent = window[s:e].strip(" “\"'\n\t")
        sent = re.sub(r"\s+", " ", sent).strip()
        # one sentence max: if still long, clip
        words = sent.split()
        if len(words) > 36:
            # center on match
            key = m.group(0).split()[0]
            idxs = [i for i, w in enumerate(words) if key.lower() in re.sub(r"[^a-z]", "", w.lower())]
            mid = idxs[0] if idxs else 0
            a = max(0, mid - 10)
            b = min(len(words), a + 28)
            a = max(0, b - 28)
            sent = " ".join(words[a:b])
        sent = one_sentence(sent, max_words=22)
        if sent and sent not in out:
            out.append(sent)
        if len(out) >= max_sentences:
            break
    return out


def term_search_pat(term: dict) -> re.Pattern:
    if term.get("regex") is not None:
        return term["regex"]
    if term.get("novel_regex") is not None:
        # still want to find Jordan in alc if any; use jordan generally for snippets
        pass
    forms = term.get("forms") or []
    if not forms:
        return re.compile(r"(?!x)x")
    # longest first
    alts = sorted(forms, key=len, reverse=True)
    return re.compile(r"\b(?:%s)\b" % "|".join(re.escape(a) for a in alts), re.I)


def verify_lee_quote(economy_text: str, quote: str) -> bool:
    if not quote:
        return False
    # loose: ignore quotes/ellipsis/case
    def n(s):
        s = s.replace("…", " ").replace("’", "'").replace("“", '"').replace("”", '"')
        return re.sub(r"\s+", " ", s).strip().lower()
    return n(quote)[:40] in n(economy_text)


def search_lee(economy_text: str, term: dict) -> tuple[str, str, str]:
    """Return (meaning, quote, chapter) or empty strings."""
    known = LEE_KNOWN.get(term["term"])
    if known and verify_lee_quote(economy_text, known[1]):
        return known
    # search for typifying language near the term
    pat = term_search_pat(term)
    cues = re.compile(
        r"\b(typifies|typify|typified|signifies|signify|signified|symbolizes|symbolize|"
        r"represents|represent|represented|means|is the type|is a type)\b",
        re.I,
    )
    norm = re.sub(r"\s+", " ", economy_text)
    # chapter markers
    # Witness Lee books often have "CHAPTER 21" etc.
    hits = []
    for m in pat.finditer(norm):
        left = max(0, m.start() - 180)
        right = min(len(norm), m.end() + 180)
        window = norm[left:right]
        if cues.search(window):
            hits.append(window)
        if len(hits) >= 5:
            break
    if not hits:
        return "", "", ""
    # return first cue window as quote, no invented meaning
    w = one_sentence(hits[0], max_words=22)
    return "", w, ""


def corpus_sizes(verses, corpora):
    kjv_tokens = []
    gen_tokens = []
    lev_tokens = []
    exo_tokens = []
    for v in verses:
        kjv_tokens.extend(v["tokens"])
        if v["book"] == "Genesis":
            gen_tokens.extend(v["tokens"])
        elif v["book"] == "Leviticus":
            lev_tokens.extend(v["tokens"])
        elif v["book"] == "Exodus":
            exo_tokens.extend(v["tokens"])
    def pack(tokens):
        content = [t for t in tokens if t not in STOPWORDS]
        return {"n_tokens": len(tokens), "n_content": len(content), "n_types": len(set(tokens))}
    sizes = {
        "KJV": {**pack(kjv_tokens), "n_verses": len(verses)},
        "Genesis": {**pack(gen_tokens), "n_verses": sum(1 for v in verses if v["book"]=="Genesis")},
        "Exodus": {**pack(exo_tokens), "n_verses": sum(1 for v in verses if v["book"]=="Exodus")},
        "Leviticus": {**pack(lev_tokens), "n_verses": sum(1 for v in verses if v["book"]=="Leviticus")},
    }
    for k, c in corpora.items():
        sizes[k] = {"n_tokens": c["n_tokens"], "n_content": c["n_content"], "n_types": len(c["counts"])}
    return sizes


def abraham_cycle(verses, corpora, log_odds_threshold=None):
    """Build the Abraham-cycle distinctive-word list and score the novels.

    The window is Genesis 11:26–25:10. A content word makes the list if it
    occurs at least three times, its log-odds versus modern English is at
    least the threshold (4.0 by default), and it is also over-represented
    against the rest of Genesis. Proper names are added separately; Melchizedek
    and Salem are kept even as hapaxes. Rates are distinctive tokens per
    10,000 content tokens in each novel.
    """
    cycle = []
    rest = []
    for v in verses:
        if v["book"] != "Genesis":
            continue
        ch, vs = v["chapter"], v["verse"]
        in_cycle = (
            (ch == 11 and vs >= 26) or
            (12 <= ch <= 24) or
            (ch == 25 and vs <= 10)
        )
        if in_cycle:
            cycle.append(v)
        else:
            rest.append(v)
    cycle_tokens = [t for v in cycle for t in v["tokens"]]
    rest_tokens = [t for v in rest for t in v["tokens"]]
    cycle_counts = collections.Counter(cycle_tokens)
    rest_counts = collections.Counter(rest_tokens)
    n_cycle = len(cycle_tokens)
    n_rest = len(rest_tokens)
    texts = [v["text"] for v in cycle]
    threshold = DISTINCT_LOG_ODDS_THRESHOLD if log_odds_threshold is None else log_odds_threshold

    # content words by log-odds vs wordfreq AND vs rest of Genesis
    words = {}
    for w, k in cycle_counts.items():
        if w in STOPWORDS or k < DISTINCT_MIN_COUNT:
            continue
        if w in {"lord", "god"}:
            continue
        lor, rr, freq, zipf = wordfreq_scores(k, n_cycle, w)
        lor_rest = log_odds(k, n_cycle, rest_counts[w], n_rest)
        if lor >= threshold and lor_rest >= 0.5:
            words[w] = {
                "reason": "log_odds",
                "count": k,
                "log_odds": lor,
                "log_odds_rest": lor_rest,
                "is_proper_name": False,
            }

    # proper names, mid-verse caps, force Salem + Melchizedek; drop lot
    caps = mid_verse_cap_counts(texts)
    force = {"salem", "melchizedek"}
    deny = NAME_DENY | {"lot", "lord", "god"}
    for w in set(caps) | force:
        if w in deny:
            continue
        if len(w) < NAME_MIN_LENGTH and w not in force:
            continue
        total = cycle_counts[w]
        if total == 0:
            continue
        capn = caps.get(w, 0)
        ratio = capn / total if total else 0
        lor, rr, freq, zipf = wordfreq_scores(total, n_cycle, w)
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
        lor_rest = log_odds(total, n_cycle, rest_counts[w], n_rest)
        # Same rest-of-Genesis bar as content words, so Egypt and Pharaoh fall out.
        # Force-includes (Salem, Melchizedek) are kept even as hapaxes.
        if (not forced) and lor_rest < 0.5:
            continue
        if w in words:
            words[w]["is_proper_name"] = True
            words[w]["reason"] = "both"
        else:
            words[w] = {
                "reason": "proper_name",
                "count": total,
                "log_odds": lor,
                "log_odds_rest": lor_rest,
                "is_proper_name": True,
            }

    types = sorted(words)
    # rates in novels (content-token denominator; count distinctive types in content tokens)
    novel_stats = {}
    for key in ("alchemist", "gatsby", "thirty_nine_steps"):
        content = corpora[key]["content"]
        c = collections.Counter(content)
        used = {w: c[w] for w in types if c[w]}
        tok = sum(used.values())
        novel_stats[key] = {
            "n_types": len(used),
            "n_tokens": tok,
            "rate": rate_per_10k(tok, corpora[key]["n_content"]),
            "used": used,
        }
    return {
        "n_verses": len(cycle),
        "n_tokens": n_cycle,
        "n_rest_tokens": n_rest,
        "n_types": len(types),
        "n_log_odds": sum(1 for w in words.values() if w["reason"] in ("log_odds", "both") and not (w["reason"]=="proper_name")),
        "n_names_only": sum(1 for w in words.values() if w["reason"] == "proper_name"),
        "n_both": sum(1 for w in words.values() if w["reason"] == "both"),
        "types": types,
        "words": words,
        "novels": novel_stats,
    }


def main():
    verses = load_verses()
    corpora = load_corpora()
    economy_text = corpora["economy"]["text"]

    sizes = corpus_sizes(verses, corpora)
    print("=== CORPUS SIZES ===")
    for k, s in sizes.items():
        extra = f" verses={s['n_verses']}" if "n_verses" in s else ""
        print(f"  {k:22} tokens={s['n_tokens']:7,}  content={s['n_content']:7,}{extra}")

    print("\n=== ABRAHAM CYCLE ===")
    ab = abraham_cycle(verses, corpora)
    print(f"  verses={ab['n_verses']} tokens={ab['n_tokens']:,} rest_tokens={ab['n_rest_tokens']:,}")
    print(f"  types={ab['n_types']} log_odds_or_both={ab['n_log_odds']} names_only={ab['n_names_only']} both={ab['n_both']}")
    for k, st in ab["novels"].items():
        print(f"  {k}: types={st['n_types']} tokens={st['n_tokens']} rate={st['rate']:.2f}")
        top = sorted(st["used"].items(), key=lambda x: -x[1])[:12]
        print("    ", ", ".join(f"{w} {c}" for w,c in top))

    # Verify fallback refs exist; if not, print first occurrence
    print("\n=== FALLBACK REF CHECK ===")
    by_ref = {v["ref"]: v for v in verses}
    for term, ref in FALLBACK_REF.items():
        print(f"  {term}: {ref} exists={ref in by_ref}")
    # first occurrence of crystal / precious stones
    for needle, lab in [
        (re.compile(r"\bcrystals?\b", re.I), "crystal"),
        (re.compile(r"\bprecious\s+stones?\b", re.I), "precious stones"),
        (re.compile(r"\bemeralds?\b", re.I), "emerald"),
    ]:
        for v in verses:
            if needle.search(v["text"]):
                print(f"  first {lab}: {v['ref']}: {v['text'][:160]}")
                break

    rows = []
    for term in TERMS:
        kjv_counts = count_term_in_verses(term, verses)
        ref, quote = choose_ref(term, verses)
        meaning, lee_quote, chapter = search_lee(economy_text, term)
        lee_quote = one_sentence(lee_quote, max_words=22) if lee_quote else ""
        alc_snips = sentence_window(corpora["alchemist"]["text"], term_search_pat(term), 1)
        rec = {
            "term": term["term"],
            "category": term["category"],
            "source_note": term.get("source_note") or "",
            "ref": ref,
            "ref_quote": quote,
            "lee_meaning": meaning,
            "lee_quote": lee_quote,
            "lee_chapter": chapter,
            "coelho_candidates": alc_snips[:1],
            "counts": {
                "alchemist": count_term_in_text(term, corpora["alchemist"]["text"], corpora["alchemist"]["tokens"], is_novel=True),
                "gatsby": count_term_in_text(term, corpora["gatsby"]["text"], corpora["gatsby"]["tokens"], is_novel=True),
                "steps": count_term_in_text(term, corpora["thirty_nine_steps"]["text"], corpora["thirty_nine_steps"]["tokens"], is_novel=True),
                "economy": count_term_in_text(term, corpora["economy"]["text"], corpora["economy"]["tokens"], is_novel=False),
                "genesis": kjv_counts["Genesis"],
                "exodus": kjv_counts["Exodus"],
                "leviticus": kjv_counts["Leviticus"],
                "kjv": kjv_counts["KJV"],
            },
        }
        n_content = {
            "alchemist": corpora["alchemist"]["n_content"],
            "gatsby": corpora["gatsby"]["n_content"],
            "steps": corpora["thirty_nine_steps"]["n_content"],
            "economy": corpora["economy"]["n_content"],
            "genesis": sizes["Genesis"]["n_content"],
            "leviticus": sizes["Leviticus"]["n_content"],
            "kjv": sizes["KJV"]["n_content"],
        }
        rec["rates"] = {
            k: round(rate_per_10k(rec["counts"][k], n_content[k]), 2)
            for k in n_content
        }
        rows.append(rec)

    # category totals (sum of term counts; phrases already subtracted from general terms)
    cats = {}
    for rec in rows:
        cat = rec["category"]
        cats.setdefault(cat, collections.Counter())
        for k, n in rec["counts"].items():
            if k in ("alchemist", "gatsby", "steps", "economy", "genesis", "leviticus", "kjv"):
                cats[cat][k] += n

    cat_rates = {}
    n_content_map = {
        "alchemist": corpora["alchemist"]["n_content"],
        "gatsby": corpora["gatsby"]["n_content"],
        "steps": corpora["thirty_nine_steps"]["n_content"],
        "economy": corpora["economy"]["n_content"],
        "genesis": sizes["Genesis"]["n_content"],
        "leviticus": sizes["Leviticus"]["n_content"],
        "kjv": sizes["KJV"]["n_content"],
    }
    for cat, ctr in cats.items():
        cat_rates[cat] = {k: round(rate_per_10k(ctr[k], n_content_map[k]), 2) for k in n_content_map}

    print("\n=== CATEGORY COUNTS AND RATES /10k content ===")
    for cat in ["architecture / places", "materials / gems", "colors", "nature / elements", "objects"]:
        print(f"  {cat}")
        print("    counts", dict(cats[cat]))
        print("    rates ", cat_rates[cat])

    print("\n=== TERMS BY ALCHEMIST COUNT ===")
    for rec in sorted(rows, key=lambda r: (-r["counts"]["alchemist"], r["term"])):
        c = rec["counts"]
        print(
            f"  {c['alchemist']:4}  {rec['term']:22}  {rec['category']:24}  "
            f"gat={c['gatsby']:3} st={c['steps']:3} econ={c['economy']:3}  "
            f"gen={c['genesis']:4} lev={c['leviticus']:3} exo={c['exodus']:3} kjv={c['kjv']:4}  "
            f"ref={rec['ref']}"
        )
        if rec["source_note"]:
            print(f"        NOTE: {rec['source_note']}")
        if rec["lee_quote"]:
            print(f"        LEE ch.{rec['lee_chapter']}: {rec['lee_meaning']} | {rec['lee_quote'][:120]}")
        if rec["coelho_candidates"]:
            print(f"        COELHO: {rec['coelho_candidates'][0][:160]}")

    # by category counts of terms
    print("\n=== TERM COUNTS BY CATEGORY ===")
    bycat = collections.Counter(r["category"] for r in rows)
    for k, n in bycat.items():
        in_alc = sum(1 for r in rows if r["category"]==k and r["counts"]["alchemist"]>0)
        print(f"  {k}: {n} terms, {in_alc} in Alchemist")
    print(f"  TOTAL {len(rows)}")

    out = {
        "sizes": sizes,
        "abraham": {
            "n_verses": ab["n_verses"],
            "n_tokens": ab["n_tokens"],
            "n_rest_tokens": ab["n_rest_tokens"],
            "n_types": ab["n_types"],
            "n_log_odds": ab["n_log_odds"],
            "n_names_only": ab["n_names_only"],
            "n_both": ab["n_both"],
            "novels": {k: {kk: vv for kk, vv in st.items() if kk != "used"} | {"used": st["used"]}
                       for k, st in ab["novels"].items()},
        },
        "category_counts": {k: dict(v) for k, v in cats.items()},
        "category_rates": cat_rates,
        "rows": rows,
    }
    (OUT / "symbolic_genesis.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    # CSV
    fieldnames = [
        "term", "category",
        "alchemist_count", "alchemist_rate",
        "gatsby_count", "gatsby_rate",
        "steps_count", "steps_rate",
        "economy_count", "economy_rate",
        "genesis_count", "genesis_rate",
        "leviticus_count", "leviticus_rate",
        "exodus_count",
        "kjv_count", "kjv_rate",
        "ref", "ref_quote",
        "lee_meaning", "lee_quote", "lee_chapter",
        "source_note",
        "coelho_candidate",
    ]
    with (OUT / "symbolic_genesis.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for rec in rows:
            c, r = rec["counts"], rec["rates"]
            w.writerow({
                "term": rec["term"],
                "category": rec["category"],
                "alchemist_count": c["alchemist"],
                "alchemist_rate": r["alchemist"],
                "gatsby_count": c["gatsby"],
                "gatsby_rate": r["gatsby"],
                "steps_count": c["steps"],
                "steps_rate": r["steps"],
                "economy_count": c["economy"],
                "economy_rate": r["economy"],
                "genesis_count": c["genesis"],
                "genesis_rate": r["genesis"],
                "leviticus_count": c["leviticus"],
                "leviticus_rate": r["leviticus"],
                "exodus_count": c["exodus"],
                "kjv_count": c["kjv"],
                "kjv_rate": r["kjv"],
                "ref": rec["ref"],
                "ref_quote": rec["ref_quote"],
                "lee_meaning": rec["lee_meaning"],
                "lee_quote": rec["lee_quote"],
                "lee_chapter": rec["lee_chapter"],
                "source_note": rec["source_note"],
                "coelho_candidate": rec["coelho_candidates"][0] if rec["coelho_candidates"] else "",
            })
    print("\nWrote", OUT / "symbolic_genesis.json", "and CSV")


if __name__ == "__main__":
    main()
