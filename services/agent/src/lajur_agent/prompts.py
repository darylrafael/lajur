"""Prompt loader and versioning with SHA256 integrity hashing."""

from __future__ import annotations

import hashlib
from pathlib import Path


def _find_prompts_dir() -> Path:
    """Locate the root prompts directory."""
    candidates = [
        Path(__file__).resolve().parents[4] / "prompts",
        Path("prompts"),
        Path("../prompts"),
        Path("../../prompts"),
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    # Fallback to current working directory prompts
    p = Path("prompts").resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


PROMPTS_DIR = _find_prompts_dir()


def load_prompt(filename: str) -> tuple[str, str]:
    """Load prompt content and compute its SHA256 hex digest.

    Returns:
        tuple of (prompt_text, sha256_hash)
    """
    path = PROMPTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    content = path.read_text(encoding="utf-8").strip()
    prompt_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return content, prompt_hash
