"""Tiny registry used by the curated lesson files in this folder."""
from __future__ import annotations

CURATED: dict[str, dict] = {}


def T(key: str, title: str, content: str) -> dict:
    """A lesson topic. `content` is markdown (code blocks allowed)."""
    return {"key": key, "title": title, "content": content.strip("\n")}


def Q(question: str, hint: str, solution: str) -> dict:
    """A practice question with an optional hint and a sample solution (markdown)."""
    return {"q": question, "hint": hint, "solution": solution.strip("\n")}


def R(title: str, url: str, kind: str = "docs") -> dict:
    """A free learning resource (official docs, tutorial, interactive course...)."""
    return {"title": title, "url": url, "kind": kind}


def register(name: str, *, level: str, overview: str, why: str, prerequisites: list[str],
             stages: list[tuple[str, list[dict]]], practice: list[dict], resources: list[dict]) -> None:
    CURATED[name.lower()] = {
        "skill": name, "level": level, "overview": overview.strip(), "why": why.strip(),
        "prerequisites": prerequisites,
        "stages": [{"title": title, "topics": topics} for title, topics in stages],
        "practice": practice, "resources": resources, "curated": True,
    }
