"""Rule-based skill extraction and normalisation (no AI key required)."""
from __future__ import annotations

import re
from functools import lru_cache

from core.taxonomy import TAXONOMY

CATEGORY_OF = {name.lower(): cat for name, cat, _ in TAXONOMY}
CANONICAL = {name.lower(): name for name, _, _ in TAXONOMY}

_PREFERRED_HEADING = re.compile(
    r"\b(preferred|nice[- ]to[- ]have|good[- ]to[- ]have|bonus|desirable|plus|optional|advantage|an? asset)\b", re.I)
_REQUIRED_HEADING = re.compile(
    r"\b(requirements?|required|must[- ]have|qualifications?|responsibilit\w+|what you.ll|skills|you will|"
    r"about you|who you are|experience)\b", re.I)
_PREFERRED_INLINE = re.compile(
    r"(is a plus|are a plus|a plus\b|\bpreferred\b|nice to have|nice-to-have|good to have|bonus|desirable|"
    r"advantage|an asset|would be a plus)", re.I)


@lru_cache(maxsize=1)
def _patterns():
    items = []
    for canonical, _cat, aliases in TAXONOMY:
        for alias in [canonical] + list(aliases):
            case_sensitive = alias.startswith("=")
            text = alias.lstrip("=")
            body = re.escape(text).replace(r"\ ", r"\s+")
            pattern = re.compile(r"(?<![A-Za-z0-9+#])" + body + r"(?![A-Za-z+#])",
                                 0 if case_sensitive else re.I)
            items.append((len(text), pattern, canonical))
    items.sort(key=lambda x: -x[0])  # longest alias first, so "SQL Server" hides "SQL"
    return items


def extract_skills(text: str) -> list[str]:
    """Return canonical skill names found in `text`, in order of first appearance."""
    if not text:
        return []
    work = text
    found: dict[str, int] = {}
    for _length, pattern, canonical in _patterns():
        for match in pattern.finditer(work):
            found.setdefault(canonical, match.start())
        work = pattern.sub(lambda m: " " * len(m.group(0)), work)
    return [name for name, _pos in sorted(found.items(), key=lambda kv: kv[1])]


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if not stripped or len(stripped) > 70:
        return False
    if stripped.endswith(":") or (stripped.isupper() and len(stripped.split()) <= 6):
        return True
    return (len(stripped.split()) <= 5 and not stripped.endswith(".")
            and not stripped.startswith(("-", "•", "*"))
            and bool(_PREFERRED_HEADING.search(stripped) or _REQUIRED_HEADING.search(stripped))
            and not extract_skills(stripped))


def extract_job_skills(text: str) -> dict[str, str]:
    """Return {skill: 'required' | 'preferred'} for a job posting.

    A skill is *preferred* when it appears under a heading such as "Nice to have" /
    "Preferred" or on a line containing phrases such as "is a plus".  Everything else is
    treated as *required*; a skill seen in both contexts is required.
    """
    result: dict[str, str] = {}
    mode = "required"
    for line in (text or "").splitlines():
        if not line.strip():
            continue
        if _is_heading(line):
            if _PREFERRED_HEADING.search(line):
                mode = "preferred"
            elif _REQUIRED_HEADING.search(line) or line.strip().endswith(":"):
                mode = "required"
        line_mode = "preferred" if (mode == "preferred" or _PREFERRED_INLINE.search(line)) else "required"
        for skill in extract_skills(line):
            if result.get(skill) == "required" or line_mode == "required":
                result[skill] = "required"
            else:
                result[skill] = "preferred"
    return result


def skill_category(name: str) -> str:
    return CATEGORY_OF.get(name.lower(), "Other")


def normalize_skill(text: str) -> str:
    """Map user wording (e.g. 'power-bi dashboards') to a canonical name when possible."""
    cleaned = (text or "").strip()
    found = extract_skills(cleaned)
    if len(found) == 1:
        return found[0]
    return CANONICAL.get(cleaned.lower(), cleaned)


def find_context(text: str, skill: str, max_len: int = 220) -> str:
    """First line of `text` that mentions `skill` (used to explain why a skill matters)."""
    for line in (text or "").splitlines():
        if skill in extract_skills(line):
            line = line.strip(" -•*\t")
            return line if len(line) <= max_len else line[: max_len - 1] + "…"
    return ""
