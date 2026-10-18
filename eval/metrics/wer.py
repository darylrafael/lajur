"""Word Error Rate (WER) computation using Levenshtein distance."""

from __future__ import annotations

from dataclasses import dataclass

from eval.metrics.normalization import normalize_text


@dataclass(frozen=True)
class WERResult:
    """Detailed result of Word Error Rate calculation."""

    wer: float
    substitutions: int
    deletions: int
    insertions: int
    hits: int
    ref_length: int
    hyp_length: int


def calculate_wer(
    reference: str,
    hypothesis: str,
    normalize: bool = True,
    canonicalize_aliases: bool = True,
) -> WERResult:
    """Compute Word Error Rate (WER) between a reference and hypothesis transcript.

    WER = (Substitutions + Deletions + Insertions) / Total Reference Words.

    Args:
        reference: Ground truth reference transcript.
        hypothesis: Speech-to-text hypothesis transcript.
        normalize: Whether to apply text and number normalization before computing WER.
        canonicalize_aliases: Whether to canonicalize menu aliases during normalization.

    Returns:
        WERResult dataclass with error counts and rate.
    """
    if normalize:
        ref_clean = normalize_text(reference, canonicalize=canonicalize_aliases)
        hyp_clean = normalize_text(hypothesis, canonicalize=canonicalize_aliases)
    else:
        ref_clean = reference
        hyp_clean = hypothesis

    ref_words = ref_clean.split()
    hyp_words = hyp_clean.split()

    n = len(ref_words)
    m = len(hyp_words)

    if n == 0:
        if m == 0:
            return WERResult(
                wer=0.0,
                substitutions=0,
                deletions=0,
                insertions=0,
                hits=0,
                ref_length=0,
                hyp_length=0,
            )
        return WERResult(
            wer=1.0,
            substitutions=0,
            deletions=0,
            insertions=m,
            hits=0,
            ref_length=0,
            hyp_length=m,
        )

    # Dynamic programming table for Levenshtein distance: dp[i][j] = (dist, S, D, I, H)
    # Using simple matrix dp[i][j] representing minimum edit operations
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                sub = dp[i - 1][j - 1] + 1
                delete = dp[i - 1][j] + 1
                insert = dp[i][j - 1] + 1
                dp[i][j] = min(sub, delete, insert)

    # Backtrack to count exact S, D, I, H
    i = n
    j = m
    substitutions = 0
    deletions = 0
    insertions = 0
    hits = 0

    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_words[i - 1] == hyp_words[j - 1]:
            hits += 1
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            substitutions += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            deletions += 1
            i -= 1
        elif j > 0 and dp[i][j] == dp[i][j - 1] + 1:
            insertions += 1
            j -= 1
        else:
            # Fallback if multiple optimal paths exist
            if i > 0 and j > 0:
                substitutions += 1
                i -= 1
                j -= 1
            elif i > 0:
                deletions += 1
                i -= 1
            else:
                insertions += 1
                j -= 1

    total_errors = substitutions + deletions + insertions
    wer = total_errors / n

    return WERResult(
        wer=wer,
        substitutions=substitutions,
        deletions=deletions,
        insertions=insertions,
        hits=hits,
        ref_length=n,
        hyp_length=m,
    )
