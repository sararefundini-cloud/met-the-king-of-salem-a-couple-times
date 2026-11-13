#!/usr/bin/env python3
"""Build a Neo4j-ready node inventory of the KJV for Bible Stories Bingo motifs.

Reads source/KJV.csv and lexicon.csv (generated from lexicon.py if missing or
when --refresh-lexicon is passed). Writes verses, words, motifs, occurrences,
import.cypher, findings.md, README.md, and a bar chart of verse counts.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_CSV = ROOT / "source" / "KJV.csv"
INDEX_COUNTS = Path(__file__).resolve().parent / "data" / "kjvindex_counts.html"

BOOK_NAME_MAP = {
    "I Samuel": "1 Samuel",
    "II Samuel": "2 Samuel",
    "I Kings": "1 Kings",
    "II Kings": "2 Kings",
    "I Chronicles": "1 Chronicles",
    "II Chronicles": "2 Chronicles",
    "I Corinthians": "1 Corinthians",
    "II Corinthians": "2 Corinthians",
    "I Thessalonians": "1 Thessalonians",
    "II Thessalonians": "2 Thessalonians",
    "I Timothy": "1 Timothy",
    "II Timothy": "2 Timothy",
    "I Peter": "1 Peter",
    "II Peter": "2 Peter",
    "I John": "1 John",
    "II John": "2 John",
    "III John": "3 John",
    "Revelation of John": "Revelation",
}

CANONICAL_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther",
    "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum",
    "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
]
BOOK_INDEX = {b: i for i, b in enumerate(CANONICAL_BOOKS)}

# Function words and KJV grammatical particles. Content words (LORD, God, man,
# Israel, behold, come, go, king, etc.) are intentionally not listed.
STOPWORDS = set(
    """
    a an the and or but if so as than then also both either neither nor whether
    not no yes yea nay o oh
    of to in for on at by with from into onto upon unto under over out up down
    off about against among amongst between through throughout before after
    above below behind within without toward towards till until since during
    oftentimes
    i me my mine myself we us our ours ourselves
    you ye thou thee thy thine yourself yourselves thyself ye
    he him his himself she her hers herself it its itself
    they them their theirs themselves
    this that these those what which who whom whose whoever whatever
    whosoever whatsoever wherein whereby wherefore therefore there here where
    when why how whenever thence hence whence hitherto thereby therein thereon
    thereof therewith herein hereof hereon herewith heretofore hitherto
    whereof whereon wherewith
    be am is are was were being been art wast wert
    have has had having hath hast
    do does did doing done doth dost didst
    will would wilt wouldst shall shalt should shouldest shouldst
    may mayest might must can cannot could couldest
    let lest
    all any each every few more most other another some such only own same
    even ever never always often very much many still just too
    said saying saith
    into unto upon
    aught naught something nothing anything
    per via
    """.split()
)

# Additional stopwords that should definitely be flagged
STOPWORDS.update({
    "thee", "thou", "thy", "ye", "hath", "shalt", "thine", "art", "dost",
    "doth", "wilt", "unto", "upon", "whoso", "whomsoever", "whosoever",
    "therein", "thereof", "thereby", "thereon", "therewith", "therefrom",
    "herein", "hereof", "whereby", "wherein", "whereof", "whereon",
    "wherewith", "wherewithal", "wherefore", "therefore",
    "hither", "thither", "whither", "hitherto",
    "yea", "nay", "lo",
    "an", "the", "and",
})

REPEAT_EXCLUDE = set(STOPWORDS) | {
    "verily", "holy", "amen", "yea", "nay", "ha", "wo", "woe",
    "selah", "alleluia", "hallelujah",
    "that", "this", "but", "and", "the", "for", "not", "all",
}

DEATH_VIOLENCE_RE = re.compile(
    r"\b(die|died|diest|dieth|dying|dead|death|deaths|"
    r"slay|slain|slew|slayeth|kill|killed|killeth|"
    r"smote|smite|smitten|dash|dashed|perish|perished|perisheth|"
    r"destroy|destroyed|destroyeth|destroyedst)\b",
    re.I,
)

FIRSTBORN_EXCLUDE_RE = re.compile(
    r"firstborn from the dead|firstborn of every creature|church of the firstborn|"
    r"firstbegotten of the dead",
    re.I,
)

# Infant Death: named false hits and reviewed verses that are not about children dying.
INFANT_DEATH_EXCLUDE_REFS = {
    ("Genesis", "38", "7"),          # Er, adult firstborn
    ("1 Chronicles", "2", "3"),      # Er, adult firstborn
    ("Numbers", "3", "13"),          # sanctifying Israel's firstborn
    ("Numbers", "8", "17"),          # sanctifying Israel's firstborn
    ("Isaiah", "65", "20"),          # infant of days / child dies at a hundred (longevity blessing)
    ("Matthew", "18", "14"),         # not the Father's will that little ones perish
    ("Zechariah", "13", "7"),        # shepherd's little ones (the flock), not children dying
}
ER_FIRSTBORN_RE = re.compile(
    r"\bEr\b.{0,80}\bfirstborn\b|\bfirstborn of Judah\b",
    re.I | re.DOTALL,
)
SANCTIFY_FIRSTBORN_RE = re.compile(
    r"\b(hallowed|sanctified)\b.{0,100}\bfirstborn\b|\bfirstborn\b.{0,100}\b(hallowed|sanctified)\b",
    re.I | re.DOTALL,
)
INFANT_OF_DAYS_RE = re.compile(
    r"\binfant of days\b|\bchild shall die an hundred years old\b",
    re.I,
)
LITTLE_ONES_NOT_DEATH_RE = re.compile(
    r"not the will.{0,80}little ones should perish|"
    r"turn mine hand upon the little ones|"
    r"smite the shepherd.{0,80}little ones",
    re.I | re.DOTALL,
)


def infant_death_excluded(v: dict, text: str, term: str) -> bool:
    """Drop verses that are not about children dying."""
    book = str(v.get("book") or "")
    chapter = str(v.get("chapter") or "")
    verse = str(v.get("verse") or "")
    if (book, chapter, verse) in INFANT_DEATH_EXCLUDE_REFS:
        return True
    if term == r"\bfirstborn\b":
        if ER_FIRSTBORN_RE.search(text) or SANCTIFY_FIRSTBORN_RE.search(text):
            return True
    if term == r"\binfants?\b" and INFANT_OF_DAYS_RE.search(text):
        return True
    if term == r"\blittle ones\b" and LITTLE_ONES_NOT_DEATH_RE.search(text):
        return True
    return False


# "red sea" should not count as the color red
RED_SEA_RE = re.compile(r"\bred\s+sea\b", re.I)

TOKEN_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
LETTER_RE = re.compile(r"[A-Za-z]+")


def normalize_book(name: str) -> str:
    return BOOK_NAME_MAP.get(name, name)


def normalize_text(text: str) -> str:
    """Typography-normalized text used for tokenization and matching."""
    t = text.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u2013", "").replace("\u2014", "")  # Beth–el -> Bethel
    t = t.replace("Æ", "Ae").replace("æ", "ae")
    t = t.replace("[but]", "but").replace("[", "").replace("]", "")
    # Drop Hebrew letters (Psalm 119 headings)
    t = re.sub(r"[\u0590-\u05FF]+", " ", t)
    # Possessives: king's / kings' -> king  (count under the base word)
    t = re.sub(r"([A-Za-z]+)'s\b", r"\1", t)
    t = re.sub(r"([A-Za-z]+s)'\b", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def normalize_for_match(text: str) -> str:
    """Like normalize_text, but keep the words and a single space; lowercase."""
    return normalize_text(text).lower()


def tokenize(norm_text: str) -> list[str]:
    return [m.group(0).lower() for m in LETTER_RE.finditer(norm_text)]


def verse_ref(book: str, chapter: int, verse: int) -> str:
    return f"{book} {chapter}:{verse}"


def verse_id(book: str, chapter: int, verse: int) -> str:
    return f"{book}.{chapter}.{verse}"


def sort_key(book: str, chapter: int, verse: int):
    return (BOOK_INDEX[book], chapter, verse)


def load_index_counts(path: Path) -> dict[str, int]:
    counts = {}
    if not path.exists():
        return counts
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) == 2 and parts[0].isdigit():
            counts[parts[1]] = int(parts[0])
    return counts


def load_verses(path: Path) -> list[dict]:
    verses = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            book = normalize_book(row["Book"])
            if book not in BOOK_INDEX:
                raise SystemExit(f"Unexpected book name: {row['Book']!r} -> {book!r}")
            chapter = int(row["Chapter"])
            verse = int(row["Verse"])
            text = row["Text"]
            norm = normalize_text(text)
            match = normalize_for_match(text)
            verses.append({
                "verse_id": verse_id(book, chapter, verse),
                "book": book,
                "chapter": chapter,
                "verse": verse,
                "text": text,
                "norm": norm,
                "match": match,
                "tokens": tokenize(norm),
                "ref": verse_ref(book, chapter, verse),
                "order": sort_key(book, chapter, verse),
            })
    verses.sort(key=lambda v: v["order"])
    return verses


def write_lexicon_csv(path: Path, rows: list[dict]) -> None:
    fields = ["motif", "subgroup", "term", "match_type", "confidence", "notes", "report_as"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_lexicon_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def word_boundary_pattern(term: str) -> re.Pattern:
    parts = [re.escape(p) for p in term.split() if p]
    if not parts:
        raise ValueError(f"empty term: {term!r}")
    pat = r"\b" + r"\s+".join(parts) + r"\b"
    return re.compile(pat, re.I)


def compile_lexicon(rows: list[dict]) -> list[dict]:
    compiled = []
    for r in rows:
        item = dict(r)
        mt = (r.get("match_type") or "exact").strip()
        term = r["term"]
        item["match_type"] = mt
        item["confidence"] = (r.get("confidence") or "high").strip()
        item["subgroup"] = (r.get("subgroup") or "").strip()
        item["report_as"] = (r.get("report_as") or term).strip()
        if mt in {"exact", "phrase"}:
            item["pattern"] = word_boundary_pattern(term)
        elif mt == "regex":
            item["pattern"] = re.compile(term, re.I | re.DOTALL)
        elif mt == "special":
            item["pattern"] = None
        else:
            raise SystemExit(f"Unknown match_type {mt!r} for {term!r}")
        compiled.append(item)
    return compiled


def find_repeating_names(original_text: str) -> list[str]:
    """Consecutive vocative names: 'Abraham, Abraham' / 'Saul, Saul'.

    Requires a comma between the two tokens. Skips genealogy and clause
    boundaries (Noah: Noah; Phinehas, Phinehas begat) and non-names.
    """
    t = original_text.replace("\u2019", "'").replace("\u2013", "-")
    deny = set(REPEAT_EXCLUDE) | {
        "unclean", "awake", "hear", "treason", "aha", "give", "return",
        "behold", "peace", "multitudes", "alas", "stand", "ho", "grace",
        "mene", "tekel",
    }
    voc_before = re.compile(
        r"\b(said|saith|saying|say|called|call|cried|cry|crying|spake|answered)\b",
        re.I,
    )
    found, seen = [], set()
    for m in re.finditer(r"\b([A-Za-z]{2,}),\s+\1\b", t, flags=re.I):
        word = m.group(1)
        key = word.lower()
        if key in deny:
            continue
        before = t[max(0, m.start() - 40):m.start()]
        after = t[m.end():m.end() + 25]
        if re.search(r"\b(to|of|after|begat|generations of)\s+$", before, re.I):
            continue
        if re.match(r"\s+(begat|spake|built|looked|shall|was|is|dreamed|also begat)\b", after, re.I):
            continue
        followed = bool(re.match(r"\s*[:!,]", after))
        preceded = bool(voc_before.search(before) or re.search(r"\bO\s+$", before, re.I))
        if not (followed or preceded):
            continue
        display = f"{m.group(1)}, {m.group(0).split(',')[-1].strip()}"
        if key not in seen:
            found.append(display)
            seen.add(key)
    return found


def death_context(match_text: str) -> bool:
    return bool(DEATH_VIOLENCE_RE.search(match_text))


def term_matches(item: dict, v: dict) -> list[str]:
    """Return list of report terms if this lexicon item matches the verse."""
    mt = item["match_type"]
    text = v["match"]
    report = item["report_as"]

    if mt == "special":
        if item["term"] == "consecutive_repeated_name":
            return find_repeating_names(v["text"])
        return []

    if mt in {"exact", "phrase", "regex"}:
        pat = item["pattern"]
        # Colors: 'red' is exact but skip 'red sea'
        if item["motif"] == "Colors" and item["term"] == "red":
            # Mask out 'red sea' before matching
            masked = RED_SEA_RE.sub("xxx xxx", text)
            return [report] if pat.search(masked) else []

        # Infant Death contextual regexes
        if item["motif"] == "Infant Death":
            if infant_death_excluded(v, text, item["term"]):
                return []
        if item["motif"] == "Infant Death" and mt == "regex":
            if item["term"] == r"\bfirstborn\b":
                if FIRSTBORN_EXCLUDE_RE.search(text):
                    return []
                if re.search(r"firstborn of death|firstborn of the poor|brother which is dead|his firstborn, up, and slay", text, re.I):
                    return []
                if pat.search(text) and death_context(text):
                    return [report]
                return []
            if item["term"] in {r"\bsucklings?\b", r"\blittle ones\b", r"\byoung child(?:ren)?\b", r"\binfants?\b"}:
                if item["term"] == r"\blittle ones\b" and re.search(r"\b(not die|may live)\b", text, re.I) and not re.search(r"\b(slay|slew|kill|killed|dashed|destroy|smote|smite)\b", text, re.I):
                    return []
                if pat.search(text) and death_context(text):
                    return [report]
                return []

        if pat.search(text):
            return [report]
        return []

    return []


def top_n_books(counter: collections.Counter, n: int = 5) -> list[tuple[str, int]]:
    # Tie-break by canonical book order
    items = list(counter.items())
    items.sort(key=lambda kv: (-kv[1], BOOK_INDEX.get(kv[0], 999)))
    return items[:n]


def top_books_str(counter: collections.Counter, n: int = 5) -> str:
    return "; ".join(f"{b} {c}" for b, c in top_n_books(counter, n))


def first_last(verse_ids_with_order: list[tuple[tuple, str, str]]) -> tuple[str, str]:
    """verse_ids_with_order: list of (order, verse_id, ref)"""
    verse_ids_with_order.sort()
    return verse_ids_with_order[0][2], verse_ids_with_order[-1][2]


def sanity_check(verses: list[dict], index_counts: dict[str, int]) -> dict:
    """Compare tokenization against kjvindex, plus case-sensitive LORD typography."""
    # Case-sensitive letter tokens on typography-normalized text, WITHOUT
    # possessive stripping, to get closer to a printed-word count.
    def raw_tokens_keep_case(text: str):
        t = text.replace("\u2019", "'").replace("\u2018", "'")
        t = t.replace("\u2013", "").replace("\u2014", "")  # Bethel
        t = t.replace("Æ", "Ae").replace("æ", "ae")
        t = t.replace("[but]", "but")
        t = re.sub(r"[\u0590-\u05FF]+", " ", t)
        return re.findall(r"[A-Za-z]+", t)

    cs = collections.Counter()
    for v in verses:
        for w in raw_tokens_keep_case(v["text"]):
            cs[w] += 1

    def both(word):
        ours = cs.get(word, 0)
        idx = index_counts.get(word)
        return {"ours": ours, "index": idx, "delta": (ours - idx) if idx is not None else None}

    # Combined forms
    lord_ours = cs.get("LORD", 0) + cs.get("Lord", 0) + cs.get("lord", 0)
    lord_idx = sum(index_counts.get(w, 0) for w in ("LORD", "Lord", "lord"))
    god_ours = cs.get("God", 0) + cs.get("GOD", 0) + cs.get("god", 0)
    god_idx = sum(index_counts.get(w, 0) for w in ("God", "GOD", "god"))
    the_ours = cs.get("the", 0) + cs.get("The", 0) + cs.get("THE", 0)
    the_idx = sum(index_counts.get(w, 0) for w in ("the", "The", "THE"))

    # After joining en-dashes, Bethel should now exist
    return {
        "the": both("the"),
        "The": both("The"),
        "THE": both("THE"),
        "the_all_cases": {"ours": the_ours, "index": the_idx, "delta": the_ours - the_idx},
        "LORD": both("LORD"),
        "Lord": both("Lord"),
        "lord": both("lord"),
        "Lord_all_cases": {"ours": lord_ours, "index": lord_idx, "delta": lord_ours - lord_idx},
        "God": both("God"),
        "GOD": both("GOD"),
        "god": both("god"),
        "God_all_cases": {"ours": god_ours, "index": god_idx, "delta": god_ours - god_idx},
        "Bethel": both("Bethel"),
        "verse_count": len(verses),
        "unique_case_sensitive": len(cs),
        "index_entries": len(index_counts),
    }


def build(refresh_lexicon: bool = True) -> dict:
    sys.path.insert(0, str(ROOT))
    from lexicon import MOTIF_ORDER, build_lexicon

    lexicon_path = ROOT / "output" / "lexicon.csv"
    if refresh_lexicon or not lexicon_path.exists():
        lex_rows = build_lexicon()
        write_lexicon_csv(lexicon_path, lex_rows)
    else:
        lex_rows = read_lexicon_csv(lexicon_path)

    (ROOT / "output" / "inventory").mkdir(parents=True, exist_ok=True)
    (ROOT / "neo4j").mkdir(parents=True, exist_ok=True)
    compiled = compile_lexicon(lex_rows)
    verses = load_verses(SOURCE_CSV)
    index_counts = load_index_counts(INDEX_COUNTS)
    sanity = sanity_check(verses, index_counts)

    # ----- words -----
    word_counts = collections.Counter()
    word_verses = collections.defaultdict(set)  # word -> verse_ids
    word_books = collections.defaultdict(collections.Counter)
    word_first_last = collections.defaultdict(list)  # word -> [(order, vid, ref)]

    for v in verses:
        seen = set()
        for tok in v["tokens"]:
            if not tok:
                continue
            word_counts[tok] += 1
            if tok not in seen:
                word_verses[tok].add(v["verse_id"])
                word_books[tok][v["book"]] += 1
                word_first_last[tok].append((v["order"], v["verse_id"], v["ref"]))
                seen.add(tok)

    # ----- motif matching -----
    # occurrences: one row per (motif, subgroup, term, verse)
    occurrences = []  # dicts
    # motif -> set of verse_ids
    motif_verses = collections.defaultdict(set)
    motif_hits = collections.Counter()  # occurrence rows
    motif_books = collections.defaultdict(collections.Counter)
    motif_first_last = collections.defaultdict(list)
    motif_terms_used = collections.defaultdict(collections.Counter)  # term hits
    # Stones subgroups
    subgroup_verses = collections.defaultdict(set)
    subgroup_hits = collections.Counter()
    subgroup_books = collections.defaultdict(collections.Counter)
    subgroup_first_last = collections.defaultdict(list)
    subgroup_terms = collections.defaultdict(collections.Counter)

    # word -> motifs (exact terms that are single words)
    word_to_motifs = collections.defaultdict(set)

    for item in compiled:
        if item["match_type"] == "exact" and " " not in item["term"]:
            word_to_motifs[item["term"].lower()].add((item["motif"], item["subgroup"]))

    for v in verses:
        # Avoid duplicate rows for the same motif+subgroup+report_as+verse
        seen_occ = set()
        matched_motifs = set()
        matched_subs = set()
        for item in compiled:
            reports = term_matches(item, v)
            for report in reports:
                key = (item["motif"], item["subgroup"], report)
                if key in seen_occ:
                    continue
                seen_occ.add(key)
                occurrences.append({
                    "motif": item["motif"],
                    "subgroup": item["subgroup"],
                    "term": report,
                    "verse_id": v["verse_id"],
                    "book": v["book"],
                    "chapter": v["chapter"],
                    "verse": v["verse"],
                })
                motif_hits[item["motif"]] += 1
                motif_terms_used[item["motif"]][report] += 1
                matched_motifs.add(item["motif"])
                if item["subgroup"]:
                    subgroup_hits[(item["motif"], item["subgroup"])] += 1
                    subgroup_terms[(item["motif"], item["subgroup"])][report] += 1
                    matched_subs.add((item["motif"], item["subgroup"]))

        for m in matched_motifs:
            if v["verse_id"] not in motif_verses[m]:
                motif_verses[m].add(v["verse_id"])
                motif_books[m][v["book"]] += 1
                motif_first_last[m].append((v["order"], v["verse_id"], v["ref"]))
        for ms in matched_subs:
            if v["verse_id"] not in subgroup_verses[ms]:
                subgroup_verses[ms].add(v["verse_id"])
                subgroup_books[ms][v["book"]] += 1
                subgroup_first_last[ms].append((v["order"], v["verse_id"], v["ref"]))

    # Notable stone verses (for findings): first/last plus a few named ones
    # we'll pick later from occurrences

    # ----- write verses.csv -----
    verses_path = ROOT / "output" / "inventory" / "verses.csv"
    with verses_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["verse_id", "book", "chapter", "verse", "text"])
        w.writeheader()
        for v in verses:
            w.writerow({
                "verse_id": v["verse_id"],
                "book": v["book"],
                "chapter": v["chapter"],
                "verse": v["verse"],
                "text": v["text"],
            })

    # ----- write words.csv -----
    words_path = ROOT / "output" / "inventory" / "words.csv"
    word_rows = []
    for word, count in word_counts.items():
        fl = word_first_last[word]
        first, last = first_last(list(fl))
        word_rows.append({
            "word": word,
            "count": count,
            "verse_count": len(word_verses[word]),
            "is_stopword": "true" if word in STOPWORDS else "false",
            "first_appearance": first,
            "last_appearance": last,
            "top_books": top_books_str(word_books[word], 5),
            "motifs": "|".join(sorted({m for m, s in word_to_motifs.get(word, set())})),
        })
    word_rows.sort(key=lambda r: (-int(r["count"]), r["word"]))
    with words_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "word", "count", "verse_count", "is_stopword",
            "first_appearance", "last_appearance", "top_books", "motifs",
        ])
        w.writeheader()
        w.writerows(word_rows)

    # ----- word_motif.csv (exact vocabulary words + all lexicon terms) -----
    wm_path = ROOT / "output" / "inventory" / "word_motif.csv"
    wm_fields = ["term", "motif", "subgroup", "match_type", "confidence"]
    with wm_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=wm_fields)
        w.writeheader()
        seen = set()
        for item in compiled:
            key = (item["term"], item["motif"], item["subgroup"])
            if key in seen:
                continue
            seen.add(key)
            w.writerow({
                "term": item["term"],
                "motif": item["motif"],
                "subgroup": item["subgroup"],
                "match_type": item["match_type"],
                "confidence": item["confidence"],
            })

    # ----- motifs.csv -----
    motifs_path = ROOT / "neo4j" / "motifs.csv"
    motif_rows = []
    for m in MOTIF_ORDER:
        fl = motif_first_last.get(m, [])
        if fl:
            first, last = first_last(list(fl))
        else:
            first, last = "", ""
        # term list from lexicon (unique report_as / term)
        terms = []
        seen_t = set()
        for item in compiled:
            if item["motif"] != m:
                continue
            t = item["report_as"]
            if t not in seen_t:
                terms.append(t)
                seen_t.add(t)
        motif_rows.append({
            "motif": m,
            "term_count": len(terms),
            "hit_count": motif_hits.get(m, 0),
            "verse_count": len(motif_verses.get(m, set())),
            "first_appearance": first,
            "last_appearance": last,
            "top_books": top_books_str(motif_books[m], 5) if m in motif_books else "",
            "terms": " | ".join(terms),
        })
    with motifs_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "motif", "term_count", "hit_count", "verse_count",
            "first_appearance", "last_appearance", "top_books", "terms",
        ])
        w.writeheader()
        w.writerows(motif_rows)

    # ----- motif_occurrences.csv -----
    occ_path = ROOT / "output" / "inventory" / "motif_occurrences.csv"
    occurrences.sort(key=lambda r: (
        MOTIF_ORDER.index(r["motif"]) if r["motif"] in MOTIF_ORDER else 99,
        r["subgroup"],
        r["book"] if r["book"] in BOOK_INDEX else r["book"],
        BOOK_INDEX.get(r["book"], 99),
        r["chapter"],
        r["verse"],
        r["term"],
    ))
    # Re-sort properly
    occurrences.sort(key=lambda r: (
        MOTIF_ORDER.index(r["motif"]) if r["motif"] in MOTIF_ORDER else 99,
        r["subgroup"],
        BOOK_INDEX.get(r["book"], 99),
        r["chapter"],
        r["verse"],
        r["term"],
    ))
    with occ_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "motif", "subgroup", "term", "verse_id", "book", "chapter", "verse",
        ])
        w.writeheader()
        w.writerows(occurrences)

    stats = {
        "verses": verses,
        "verse_count": len(verses),
        "word_count_types": len(word_rows),
        "word_count_tokens": sum(word_counts.values()),
        "stopword_types": sum(1 for r in word_rows if r["is_stopword"] == "true"),
        "lexicon_rows": len(lex_rows),
        "occurrence_rows": len(occurrences),
        "motif_rows": motif_rows,
        "motif_verses": motif_verses,
        "motif_hits": motif_hits,
        "motif_books": motif_books,
        "motif_first_last": motif_first_last,
        "motif_terms_used": motif_terms_used,
        "subgroup_verses": subgroup_verses,
        "subgroup_hits": subgroup_hits,
        "subgroup_books": subgroup_books,
        "subgroup_first_last": subgroup_first_last,
        "subgroup_terms": subgroup_terms,
        "occurrences": occurrences,
        "sanity": sanity,
        "word_counts": word_counts,
        "compiled": compiled,
        "MOTIF_ORDER": MOTIF_ORDER,
    }
    return stats


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-lexicon", action="store_true", default=True)
    args = parser.parse_args()
    stats = build(refresh_lexicon=True)
    s = stats["sanity"]
    print("VERSES", stats["verse_count"])
    print("WORD TYPES", stats["word_count_types"], "TOKENS", stats["word_count_tokens"])
    print("STOPWORD TYPES", stats["stopword_types"])
    print("LEXICON ROWS", stats["lexicon_rows"])
    print("OCCURRENCES", stats["occurrence_rows"])
    print("SANITY the", s["the"], "LORD", s["LORD"], "Lord_all", s["Lord_all_cases"],
          "God", s["God"], "God_all", s["God_all_cases"], "Bethel", s["Bethel"])
    print("MOTIF VERSE COUNTS")
    for row in stats["motif_rows"]:
        print(f"  {row['verse_count']:5d}  hits={row['hit_count']:5d}  {row['motif']}  first={row['first_appearance']}  last={row['last_appearance']}")
