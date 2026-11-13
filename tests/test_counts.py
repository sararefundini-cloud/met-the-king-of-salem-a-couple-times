"""Hand-checkable tests for tokenization, log-odds, KJV counts, and a few Alchemist figures."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from textutil import tokenize, normalize_text, load_book, SOURCE_CSV, PRIVATE_DIR
from compare import log_odds, rate_per_10k


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

def test_en_dash_joins_kjv_place_names():
    # King James typography: Beth–el (en-dash) should be one token, Bethel.
    assert tokenize("Beth–el on the west") == ["bethel", "on", "the", "west"]


def test_possessives_reduce_to_the_base_word():
    assert tokenize("king's house") == ["king", "house"]
    assert tokenize("king’s house") == ["king", "house"]  # typographic apostrophe
    assert tokenize("the boys' tents") == ["the", "boys", "tents"]
    assert tokenize("GOD'S ECONOMY") == ["god", "economy"]


def test_em_dash_does_not_glue_words():
    # A clause dash must not produce the junk token "crystalhe".
    assert tokenize("some crystal—he was") == ["some", "crystal", "he", "was"]


def test_contractions_are_expanded():
    # "don't" must not become the junk tokens "don" and "t".
    assert tokenize("I don't know") == ["i", "do", "not", "know"]
    assert tokenize("I'm the king of Salem!") == ["i", "am", "the", "king", "of", "salem"]
    assert tokenize("It's just that I don't know") == ["it", "just", "that", "i", "do", "not", "know"]


def test_hyphen_splits_compound_words():
    assert tokenize("well-known") == ["well", "known"]


# ---------------------------------------------------------------------------
# Log-odds (toy example, worked by hand)
# ---------------------------------------------------------------------------

def test_smoothed_log_odds_on_a_toy_example():
    # Corpus A: word appears 10 times in 100 tokens.
    # Corpus B: word appears 2 times in 100 tokens.
    # log-odds = ln((10 + 0.5) / (100 - 10 + 0.5)) - ln((2 + 0.5) / (100 - 2 + 0.5))
    #          = ln(10.5 / 90.5) - ln(2.5 / 98.5)
    expected = math.log(10.5 / 90.5) - math.log(2.5 / 98.5)
    assert log_odds(10, 100, 2, 100) == pytest.approx(expected)
    # A is richer in the word, so the score should be positive.
    assert expected > 0
    # Equal rates should be about zero (smoothing is symmetric here).
    assert log_odds(10, 100, 10, 100) == pytest.approx(0.0)


def test_rate_per_10k():
    assert rate_per_10k(66, 16576) == pytest.approx(66 / 16576 * 10000)
    assert rate_per_10k(0, 1000) == 0.0
    assert rate_per_10k(5, 0) == 0.0


# ---------------------------------------------------------------------------
# KJV counts, cross-checked against kjvindex
# ---------------------------------------------------------------------------

def _kjv_token_counts():
    counts = {}
    n = 0
    with SOURCE_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            toks = tokenize(row["Text"] or row.get("text") or "")
            n += len(toks)
            for w in toks:
                counts[w] = counts.get(w, 0) + 1
    return counts, n


def test_kjv_verse_and_token_totals():
    n_verses = sum(1 for _ in SOURCE_CSV.open(encoding="utf-8")) - 1  # minus header
    assert n_verses == 31102
    counts, n_tokens = _kjv_token_counts()
    # Same running-text total recorded in source/SOURCE.md and the report.
    assert n_tokens == 790882
    # En-dash joining: Beth–el / Beer–sheba etc. Token "bethel" matches kjvindex (66).
    assert counts["bethel"] == 66


def test_kjv_lord_combined_matches_kjvindex():
    # The CSV almost never keeps small-caps LORD typography, so the fair
    # comparison is the combined case-insensitive total, which kjvindex
    # reports as 7,970 (see findings from the inventory build).
    n = 0
    with SOURCE_CSV.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n += tokenize(row["Text"] or row.get("text") or "").count("lord")
    assert n == 7970


# ---------------------------------------------------------------------------
# Alchemist figures (skipped if the copyrighted text is not present)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def alchemist_counts():
    path = PRIVATE_DIR / "alchemist.txt"
    if not path.exists():
        pytest.skip("data/private/alchemist.txt is not present")
    text = load_book(path, "alchemist")
    counts = {}
    for w in tokenize(text):
        counts[w] = counts.get(w, 0) + 1
    return counts


def test_salem_count_in_the_alchemist(alchemist_counts):
    assert alchemist_counts.get("salem", 0) == 11


def test_melchizedek_count_in_the_alchemist(alchemist_counts):
    assert alchemist_counts.get("melchizedek", 0) == 4


def test_abraham_is_named_once(alchemist_counts):
    assert alchemist_counts.get("abraham", 0) == 1


def test_abraham_cycle_excludes_camel_setting_words():
    """Camel and camels are desert-setting words, not part of the reported list."""
    from build_symbolic_genesis import SETTING_EXCLUSIONS, abraham_cycle, load_verses

    assert SETTING_EXCLUSIONS == {"camel", "camels"}
    verses = load_verses()
    empty = {"content": [], "n_content": 1}
    corpora = {"alchemist": empty, "gatsby": empty, "thirty_nine_steps": empty}
    ab = abraham_cycle(verses, corpora)
    assert "camel" not in ab["types"]
    assert "camels" not in ab["types"]
    # 165 before the exclusion; only plural "camels" qualified (singular occurs once).
    assert ab["n_types"] == 164
    assert ab["n_log_odds"] == 77
    assert ab["n_names_only"] == 87
    # Published Alchemist rate after dropping 9 camel tokens from 67 hits.
    assert rate_per_10k(58, 16576) == pytest.approx(34.99, abs=0.005)
