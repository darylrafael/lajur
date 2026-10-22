"""Text normalization pipeline for speech recognition evaluation in Lajur.

Handles:
1. Lowercasing and whitespace collapsing.
2. Punctuation stripping with phonetic preservation.
3. Indonesian and English number word conversion to Arabic digits.
4. Menu item, modifier, and combo alias canonicalization against menu.json (non-overlapping).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# Indonesian number word to digit mapping (compounds handled first)
ID_NUMBER_WORDS: list[tuple[str, str]] = [
    (r"\bdua puluh satu\b", "21"),
    (r"\bdua puluh dua\b", "22"),
    (r"\bdua puluh tiga\b", "23"),
    (r"\bdua puluh empat\b", "24"),
    (r"\bdua puluh lima\b", "25"),
    (r"\bdua puluh enam\b", "26"),
    (r"\bdua puluh tujuh\b", "27"),
    (r"\bdua puluh delapan\b", "28"),
    (r"\bdua puluh sembilan\b", "29"),
    (r"\bdua puluh\b", "20"),
    (r"\bsembilan belas\b", "19"),
    (r"\bdelapan belas\b", "18"),
    (r"\btujuh belas\b", "17"),
    (r"\benam belas\b", "16"),
    (r"\blima belas\b", "15"),
    (r"\bempat belas\b", "14"),
    (r"\btiga belas\b", "13"),
    (r"\bdua belas\b", "12"),
    (r"\bsebelas\b", "11"),
    (r"\bsepuluh\b", "10"),
    (r"\bsembilan\b", "9"),
    (r"\bdelapan\b", "8"),
    (r"\btujuh\b", "7"),
    (r"\benam\b", "6"),
    (r"\blima\b", "5"),
    (r"\bempat\b", "4"),
    (r"\btiga\b", "3"),
    (r"\bdua\b", "2"),
    (r"\bsatu\b", "1"),
    (r"\bnol\b", "0"),
    (r"\bkosong\b", "0"),
]

# English number word to digit mapping
EN_NUMBER_WORDS: list[tuple[str, str]] = [
    (r"\btwenty one\b", "21"),
    (r"\btwenty two\b", "22"),
    (r"\btwenty three\b", "23"),
    (r"\btwenty four\b", "24"),
    (r"\btwenty five\b", "25"),
    (r"\btwenty six\b", "26"),
    (r"\btwenty seven\b", "27"),
    (r"\btwenty eight\b", "28"),
    (r"\btwenty nine\b", "29"),
    (r"\btwenty\b", "20"),
    (r"\bnineteen\b", "19"),
    (r"\beighteen\b", "18"),
    (r"\bseventeen\b", "17"),
    (r"\bsixteen\b", "16"),
    (r"\bfifteen\b", "15"),
    (r"\bfourteen\b", "14"),
    (r"\bthirteen\b", "13"),
    (r"\btwelve\b", "12"),
    (r"\beleven\b", "11"),
    (r"\bten\b", "10"),
    (r"\bnine\b", "9"),
    (r"\beight\b", "8"),
    (r"\bseven\b", "7"),
    (r"\bsix\b", "6"),
    (r"\bfive\b", "5"),
    (r"\bfour\b", "4"),
    (r"\bthree\b", "3"),
    (r"\btwo\b", "2"),
    (r"\bone\b", "1"),
    (r"\bzero\b", "0"),
]


class TextNormalizer:
    """Normalizes transcriptions for fair, deterministic speech recognition benchmarks."""

    def __init__(self, menu_path: Path | str | None = None) -> None:
        """Initialize the normalizer with optional menu.json path for alias canonicalization."""
        if menu_path is None:
            candidate = Path("eval/menu/menu.json")
            if not candidate.exists():
                candidate = Path(__file__).resolve().parents[2] / "eval" / "menu" / "menu.json"
            menu_path = candidate

        self.alias_to_canonical: dict[str, str] = {}
        self._compiled_alias_patterns: list[tuple[re.Pattern[str], str]] = []
        if Path(menu_path).exists():
            self._load_menu_aliases(menu_path)

    def _load_menu_aliases(self, menu_path: Path | str) -> None:
        with open(menu_path, "r", encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)

        # Map item aliases and names to lowercase name_id
        for item in data.get("items", []):
            canonical = self.basic_normalize(item["name_id"])
            if "name_en" in item:
                self.alias_to_canonical[self.basic_normalize(item["name_en"])] = canonical
            for alias in item.get("aliases", []):
                self.alias_to_canonical[self.basic_normalize(alias)] = canonical

        # Map combo aliases to lowercase name_id
        for combo in data.get("combos", []):
            canonical = self.basic_normalize(combo["name_id"])
            if "name_en" in combo:
                self.alias_to_canonical[self.basic_normalize(combo["name_en"])] = canonical
            for alias in combo.get("aliases", []):
                self.alias_to_canonical[self.basic_normalize(alias)] = canonical

        # Map modifier options
        for mod in data.get("modifiers", []):
            for opt in mod.get("options", []):
                canonical = self.basic_normalize(opt["name_id"])
                if "name_en" in opt:
                    self.alias_to_canonical[self.basic_normalize(opt["name_en"])] = canonical

        # Precompile patterns sorted by length descending (including canonical names to protect them)
        for item in data.get("items", []):
            canonical = self.basic_normalize(item["name_id"])
            self.alias_to_canonical[canonical] = canonical
        for combo in data.get("combos", []):
            canonical = self.basic_normalize(combo["name_id"])
            self.alias_to_canonical[canonical] = canonical

        sorted_aliases = sorted(self.alias_to_canonical.keys(), key=lambda s: len(s), reverse=True)
        self._compiled_alias_patterns = [
            (re.compile(rf"\b{re.escape(alias)}\b", re.IGNORECASE), self.alias_to_canonical[alias])
            for alias in sorted_aliases
            if alias
        ]

    @staticmethod
    def basic_normalize(text: str) -> str:
        """Lowercases, strips punctuation, and normalizes whitespace."""
        text = text.lower()
        # Replace hyphens and slashes with spaces (e.g. "di-upsize" -> "di upsize")
        text = re.sub(r"[-/]", " ", text)
        # Strip all other punctuation except alphanumeric and spaces
        text = re.sub(r"[^\w\s]", "", text)
        # Collapse whitespace
        return " ".join(text.split())

    @staticmethod
    def normalize_numbers(text: str) -> str:
        """Converts Indonesian and English spoken number words to numeric digits."""
        out = text
        for pattern, replacement in ID_NUMBER_WORDS:
            out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
        for pattern, replacement in EN_NUMBER_WORDS:
            out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
        return out

    def canonicalize_aliases(self, text: str) -> str:
        """Replaces known menu aliases with their canonical Indonesian menu names.

        Uses non-overlapping span matching (longest match first) to prevent cascading replacements.
        """
        if not self._compiled_alias_patterns:
            return text

        matched_spans: list[tuple[int, int, str]] = []
        occupied: set[int] = set()

        for pattern, canonical in self._compiled_alias_patterns:
            for match in pattern.finditer(text):
                start, end = match.span()
                span_range = set(range(start, end))
                if not (span_range & occupied):
                    occupied.update(span_range)
                    matched_spans.append((start, end, canonical))

        if not matched_spans:
            return text

        # Sort spans by starting index
        matched_spans.sort(key=lambda s: s[0])

        # Reconstruct string replacing matched spans
        chunks: list[str] = []
        last_idx = 0
        for start, end, canonical in matched_spans:
            chunks.append(text[last_idx:start])
            chunks.append(canonical)
            last_idx = end
        chunks.append(text[last_idx:])

        return " ".join("".join(chunks).split())

    def normalize(self, text: str, canonicalize: bool = False) -> str:
        """Full normalization pipeline: basic clean -> number conversion -> optional alias canonicalization."""
        if not text:
            return ""
        cleaned = self.basic_normalize(text)
        numbered = self.normalize_numbers(cleaned)
        if canonicalize and self._compiled_alias_patterns:
            return self.canonicalize_aliases(numbered)
        return numbered


_DEFAULT_NORMALIZER: TextNormalizer | None = None


def get_default_normalizer() -> TextNormalizer:
    global _DEFAULT_NORMALIZER
    if _DEFAULT_NORMALIZER is None:
        _DEFAULT_NORMALIZER = TextNormalizer()
    return _DEFAULT_NORMALIZER


def normalize_text(text: str, canonicalize: bool = False) -> str:
    """Convenience wrapper for text normalization."""
    return get_default_normalizer().normalize(text, canonicalize=canonicalize)
