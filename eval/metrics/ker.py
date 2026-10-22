"""Keyword Error Rate (KER) computation for Lajur drive-thru speech evaluation.

Keywords comprise:
1. Menu item names and aliases (canonicalized to canonical item/combo ID)
2. Modifier options (e.g. spicy, no ice, dipping sauce, egg style)
3. Size specifications (regular, medium, large)
4. Quantity tokens (digits extracted after number normalization)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eval.metrics.normalization import get_default_normalizer, normalize_text


@dataclass(frozen=True)
class KeywordToken:
    """A semantic keyword extracted from a transcript."""

    category: str  # "ITEM", "MODIFIER", "SIZE", "QUANTITY"
    canonical_id: str
    original_text: str

    def __repr__(self) -> str:
        return f"{self.category}:{self.canonical_id}"


@dataclass(frozen=True)
class KERResult:
    """Detailed result of Keyword Error Rate calculation."""

    ker: float
    substitutions: int
    deletions: int
    insertions: int
    hits: int
    ref_count: int
    hyp_count: int
    ref_keywords: list[str]
    hyp_keywords: list[str]
    aligned_pairs: list[tuple[str | None, str | None, str]]  # (ref, hyp, op)


class KeywordExtractor:
    """Extracts domain-critical keyword tokens from normalized transcripts."""

    def __init__(self, menu_path: Path | str | None = None) -> None:
        if menu_path is None:
            candidate = Path("eval/menu/menu.json")
            if not candidate.exists():
                candidate = Path(__file__).resolve().parents[2] / "eval" / "menu" / "menu.json"
            menu_path = candidate

        self.patterns: list[tuple[re.Pattern[str], str, str]] = []
        self._load_patterns(menu_path)

    def _load_patterns(self, menu_path: Path | str) -> None:
        patterns_list: list[tuple[str, str, str]] = []  # (phrase, category, canonical_id)

        if Path(menu_path).exists():
            with open(menu_path, "r", encoding="utf-8") as f:
                data: dict[str, Any] = json.load(f)

            # 1. Items
            for item in data.get("items", []):
                item_id = item["id"]
                patterns_list.append((item["name_id"], "ITEM", item_id))
                if "name_en" in item:
                    patterns_list.append((item["name_en"], "ITEM", item_id))
                for alias in item.get("aliases", []):
                    patterns_list.append((alias, "ITEM", item_id))

            # 2. Combos
            for combo in data.get("combos", []):
                combo_id = combo["id"]
                patterns_list.append((combo["name_id"], "ITEM", combo_id))
                if "name_en" in combo:
                    patterns_list.append((combo["name_en"], "ITEM", combo_id))
                for alias in combo.get("aliases", []):
                    patterns_list.append((alias, "ITEM", combo_id))

            # 3. Modifiers
            for mod in data.get("modifiers", []):
                mod_id = mod["id"]
                for opt in mod.get("options", []):
                    opt_id = opt["id"]
                    canonical = f"{mod_id}:{opt_id}"
                    patterns_list.append((opt["name_id"], "MODIFIER", canonical))
                    if "name_en" in opt:
                        patterns_list.append((opt["name_en"], "MODIFIER", canonical))

        # 4. Sizes
        size_keywords = [
            ("regular", "SIZE", "size_regular"),
            ("medium", "SIZE", "size_medium"),
            ("large", "SIZE", "size_large"),
            ("kecil", "SIZE", "size_regular"),
            ("sedang", "SIZE", "size_medium"),
            ("besar", "SIZE", "size_large"),
            ("upsize", "SIZE", "size_large"),
        ]
        patterns_list.extend(size_keywords)

        # Sort patterns by length descending so multi-word entities match first
        patterns_list.sort(key=lambda x: len(x[0]), reverse=True)

        normalizer = get_default_normalizer()
        for phrase, cat, canonical_id in patterns_list:
            norm_phrase = normalizer.basic_normalize(phrase)
            if not norm_phrase:
                continue
            regex = re.compile(rf"\b{re.escape(norm_phrase)}\b", re.IGNORECASE)
            self.patterns.append((regex, cat, canonical_id))

    def extract(self, text: str) -> list[KeywordToken]:
        """Extracts keyword tokens in sequential order of appearance from text."""
        # 1. Normalize numbers and basic text
        norm_text = normalize_text(text, canonicalize=False)

        # 2. Find keyword spans
        matched_spans: list[tuple[int, int, KeywordToken]] = []
        occupied: set[int] = set()

        for regex, cat, canonical_id in self.patterns:
            for match in regex.finditer(norm_text):
                start, end = match.span()
                span_range = set(range(start, end))
                if not (span_range & occupied):
                    occupied.update(span_range)
                    token = KeywordToken(
                        category=cat,
                        canonical_id=canonical_id,
                        original_text=match.group(),
                    )
                    matched_spans.append((start, end, token))

        # 3. Find quantity tokens (digits) not covered by previous spans
        digit_regex = re.compile(r"\b\d+\b")
        for match in digit_regex.finditer(norm_text):
            start, end = match.span()
            span_range = set(range(start, end))
            if not (span_range & occupied):
                occupied.update(span_range)
                token = KeywordToken(
                    category="QUANTITY",
                    canonical_id=match.group(),
                    original_text=match.group(),
                )
                matched_spans.append((start, end, token))

        # Sort extracted tokens by character position in the original utterance
        matched_spans.sort(key=lambda s: s[0])
        return [item[2] for item in matched_spans]


_DEFAULT_EXTRACTOR: KeywordExtractor | None = None


def get_default_extractor() -> KeywordExtractor:
    global _DEFAULT_EXTRACTOR
    if _DEFAULT_EXTRACTOR is None:
        _DEFAULT_EXTRACTOR = KeywordExtractor()
    return _DEFAULT_EXTRACTOR


def calculate_ker(
    reference: str,
    hypothesis: str,
    extractor: KeywordExtractor | None = None,
) -> KERResult:
    """Compute Keyword Error Rate (KER) between reference and hypothesis transcripts.

    KER = (Substitutions + Deletions + Insertions) / Total Reference Keywords.

    Alignment rules:
    - Missed keyword (Deletion): Keyword in reference with no matching keyword in hypothesis.
    - Inserted keyword (Insertion): Keyword in hypothesis with no matching keyword in reference.
    - Substituted keyword (Substitution): Keyword in reference aligned with a different keyword in hypothesis.
    """
    ext = extractor if extractor is not None else get_default_extractor()

    ref_tokens = ext.extract(reference)
    hyp_tokens = ext.extract(hypothesis)

    ref_keys = [repr(k) for k in ref_tokens]
    hyp_keys = [repr(k) for k in hyp_tokens]

    n = len(ref_keys)
    m = len(hyp_keys)

    if n == 0:
        if m == 0:
            return KERResult(
                ker=0.0,
                substitutions=0,
                deletions=0,
                insertions=0,
                hits=0,
                ref_count=0,
                hyp_count=0,
                ref_keywords=[],
                hyp_keywords=[],
                aligned_pairs=[],
            )
        return KERResult(
            ker=1.0,
            substitutions=0,
            deletions=0,
            insertions=m,
            hits=0,
            ref_count=0,
            hyp_count=m,
            ref_keywords=[],
            hyp_keywords=hyp_keys,
            aligned_pairs=[(None, k, "INSERTION") for k in hyp_keys],
        )

    # Dynamic programming for minimum edit distance on keyword sequences
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_keys[i - 1] == hyp_keys[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                sub = dp[i - 1][j - 1] + 1
                delete = dp[i - 1][j] + 1
                insert = dp[i][j - 1] + 1
                dp[i][j] = min(sub, delete, insert)

    # Backtracking to reconstruct alignment
    i = n
    j = m
    substitutions = 0
    deletions = 0
    insertions = 0
    hits = 0
    aligned_pairs: list[tuple[str | None, str | None, str]] = []

    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_keys[i - 1] == hyp_keys[j - 1]:
            hits += 1
            aligned_pairs.append((ref_keys[i - 1], hyp_keys[j - 1], "HIT"))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            substitutions += 1
            aligned_pairs.append((ref_keys[i - 1], hyp_keys[j - 1], "SUBSTITUTION"))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            deletions += 1
            aligned_pairs.append((ref_keys[i - 1], None, "DELETION"))
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            insertions += 1
            aligned_pairs.append((None, hyp_keys[j - 1], "INSERTION"))
            j -= 1
        else:
            if i > 0 and j > 0:
                substitutions += 1
                aligned_pairs.append((ref_keys[i - 1], hyp_keys[j - 1], "SUBSTITUTION"))
                i -= 1
                j -= 1
            elif i > 0:
                deletions += 1
                aligned_pairs.append((ref_keys[i - 1], None, "DELETION"))
                i -= 1
            else:
                insertions += 1
                aligned_pairs.append((None, hyp_keys[j - 1], "INSERTION"))
                j -= 1

    aligned_pairs.reverse()
    total_errors = substitutions + deletions + insertions
    ker = total_errors / n

    return KERResult(
        ker=ker,
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
        hits=hits,
        ref_count=n,
        hyp_count=m,
        ref_keywords=ref_keys,
        hyp_keywords=hyp_keys,
        aligned_pairs=aligned_pairs,
    )
