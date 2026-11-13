"""Shared typography, tokenization, stopwords, and book-text cleaners."""

from __future__ import annotations

import re
from pathlib import Path

LETTER_RE = re.compile(r"[A-Za-z]+")

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
STOPWORDS.update({
    "thee", "thou", "thy", "ye", "hath", "shalt", "thine", "art", "dost",
    "doth", "wilt", "unto", "upon", "whoso", "whomsoever", "whosoever",
    "therein", "thereof", "thereby", "thereon", "therewith", "therefrom",
    "herein", "hereof", "whereby", "wherein", "whereof", "whereon",
    "wherewith", "wherewithal", "wherefore", "therefore",
    "hither", "thither", "whither", "hitherto",
    "yea", "nay", "lo",
})


def normalize_text(text: str) -> str:
    t = text.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("\u2013", "").replace("\u2014", "")
    t = t.replace("Æ", "Ae").replace("æ", "ae")
    t = t.replace("[but]", "but").replace("[", "").replace("]", "")
    t = re.sub(r"[\u0590-\u05FF]+", " ", t)
    t = re.sub(r"([A-Za-z]+)'s\b", r"\1", t)
    t = re.sub(r"([A-Za-z]+s)'\b", r"\1", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in LETTER_RE.finditer(normalize_text(text))]


def strip_gutenberg(text: str) -> str:
    start = re.search(r"\*\*\*\s*START OF (?:THE PROJECT GUTENBERG EBOOK|THIS PROJECT GUTENBERG EBOOK).*\*\*\*", text, re.I)
    end = re.search(r"\*\*\*\s*END OF (?:THE PROJECT GUTENBERG EBOOK|THIS PROJECT GUTENBERG EBOOK).*\*\*\*", text, re.I)
    if start:
        text = text[start.end():]
    if end:
        # end was searched on original; re-search on sliced text
        end2 = re.search(r"\*\*\*\s*END OF (?:THE PROJECT GUTENBERG EBOOK|THIS PROJECT GUTENBERG EBOOK).*\*\*\*", text, re.I)
        if end2:
            text = text[:end2.start()]
    # Drop a short table of contents / dedication if clearly marked
    text = re.sub(r"(?is)Table of Contents.{0,400}?(?=\n\s{0,20}[A-Z])", "\n", text, count=1)
    return text.strip()


def clean_alchemist(text: str) -> str:
    """Keep Prologue through Epilogue; drop title, TOC, 'Ten Years On' intro, and publisher back matter."""
    pages = text.split("\f")
    kept = []
    started = False
    for i, page in enumerate(pages):
        raw = page.strip()
        if not raw:
            continue
        # The contents page also mentions the prologue; skip it explicitly.
        if re.match(r"Contents\b", raw, re.I):
            continue
        if re.search(r"TRANSLATED BY ALAN R\. CLARKE", raw) and len(raw) < 200:
            continue
        if (not started) and re.search(r"\bPROLOGUE\b", raw) and re.search(
            r"Translated by Clifford|SOMEONE IN THE caravan|someone in the caravan", raw, re.I
        ):
            started = True
        if not started:
            continue
        if re.search(r"Paulo Coelho was born", raw, re.I):
            break
        if re.search(r"^International Acclaim", raw, re.I):
            break
        if re.search(r"PerfectBound", raw) and re.search(r"Copyright", raw, re.I):
            break
        if re.search(r"^About the Publisher\b", raw, re.I):
            break
        kept.append(raw)
    return "\n\n".join(kept)


def clean_economy(text: str) -> str:
    """Keep Foreword through the last chapter; drop contents list and endnotes."""
    # Start at FOREWORD
    m = re.search(r"\bFOREWORD\b", text)
    if m:
        text = text[m.start():]
    # Drop trailing scripture-quotation notes
    text = re.split(r"\n\s*\d+\s+Scripture quotations are from", text)[0]
    text = re.split(r"\n\s*All italics used in Scripture quotations", text)[0]
    # Drop form feeds
    text = text.replace("\f", "\n")
    return text.strip()


def load_book(path: Path, kind: str) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if kind == "alchemist":
        return clean_alchemist(raw)
    if kind == "economy":
        return clean_economy(raw)
    if kind == "gutenberg":
        return strip_gutenberg(raw)
    return raw


# Canonical OT / NT splits used for source tagging
OT_BOOKS = {
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther",
    "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon",
    "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
    "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum",
    "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
}
NT_BOOKS = {
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation",
}

# Mutually exclusive source labels, in stack order
SOURCE_LABELS = [
    "Genesis",
    "Exodus",
    "Leviticus",
    "rest of OT",
    "NT only",
    "not in KJV",
]


def classify_word(word: str, sets: dict[str, set[str]]) -> str:
    """Exclusive source bucket for a word type."""
    if word in sets["Genesis"]:
        return "Genesis"
    if word in sets["Exodus"]:
        return "Exodus"
    if word in sets["Leviticus"]:
        return "Leviticus"
    if word in sets["OT"]:
        return "rest of OT"
    if word in sets["NT"]:
        return "NT only"
    return "not in KJV"


# ---------------------------------------------------------------------------
# Repo paths (scripts run from any cwd; paths are relative to this file)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
PRIVATE_DIR = DATA_DIR / "private"
BASELINES_DIR = DATA_DIR / "baselines"
SOURCE_DIR = ROOT / "source"
SOURCE_CSV = SOURCE_DIR / "KJV.csv"
OUTPUT_DIR = ROOT / "output"
NEO4J_DIR = ROOT / "neo4j"


def require_private_texts(*filenames: str) -> dict[str, Path]:
    """Return paths under data/private/, or exit with a short how-to if any are missing."""
    if not filenames:
        filenames = ("alchemist.txt", "economy.txt")
    paths: dict[str, Path] = {}
    missing: list[str] = []
    for name in filenames:
        path = PRIVATE_DIR / name
        paths[name] = path
        if not path.exists():
            missing.append(str(path))
    if missing:
        raise SystemExit(
            "Missing copyrighted source text(s) (not included in this repository):\n  "
            + "\n  ".join(missing)
            + "\n\nPlace your own copies at those paths and rerun. See README.md."
        )
    return paths
