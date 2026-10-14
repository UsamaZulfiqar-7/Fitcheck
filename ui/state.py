"""Session state helpers shared by all pages."""
from __future__ import annotations

import streamlit as st

import config
from core import repository as repo

PAGES = ["Home Dashboard", "Resume & Job Analysis", "Match Results", "Skill Gap Analysis",
         "AI Skill Assistant", "Personalized Learning Center", "My Learning Progress", "Updated CV & Downloads", "Settings"]


def init() -> None:
    defaults = {"cand_id": None, "cand_name": None, "resume_id": None, "job_id": None, "match_id": None,
                "skill_weight": config.SKILL_WEIGHT, "preferred_weight": config.PREFERRED_WEIGHT,
                "use_semantic": config.USE_SEMANTIC, "ai_notes": {}, "cv_flow": None, "cv_last_change": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def settings() -> dict:
    s = st.session_state
    return {"skill_weight": s["skill_weight"], "preferred_weight": s["preferred_weight"],
            "use_semantic": s["use_semantic"]}


def switch_candidate(name: str) -> int:
    """Select / create the profile and restore its latest analysis (persistence across restarts)."""
    cand = repo.get_or_create_candidate(name)
    s = st.session_state
    if s["cand_id"] != cand.id:
        s.update(cand_id=cand.id, cand_name=cand.display_name, resume_id=None, job_id=None, match_id=None,
                 cv_flow=None, cv_last_change=None, ai_notes={})
        latest = repo.latest_match(cand.id)
        if latest is not None:
            s.update(resume_id=latest.resume_id, job_id=latest.job_id, match_id=latest.id)
    return cand.id


def load_analysis(match_id: int) -> None:
    match = repo.get_match(match_id)
    if match is not None:
        st.session_state.update(match_id=match.id, resume_id=match.resume_id, job_id=match.job_id,
                                cv_flow=None, cv_last_change=None)


def current():
    """(match_row, resume_row, job_row) of the active analysis, or None."""
    s = st.session_state
    if not s.get("match_id"):
        return None
    match = repo.get_match(s["match_id"])
    if match is None:
        return None
    return match, repo.get_resume(match.resume_id), repo.get_job(match.job_id)


def workflow_status() -> list[tuple[str, bool]]:
    s = st.session_state
    cand = s.get("cand_id")
    ctx = current()
    progress = repo.progress_summary(cand) if cand else []
    added = bool(ctx and repo.learned_skills(ctx[0].resume_id))
    return [("CV uploaded", bool(ctx)), ("Job added", bool(ctx)), ("Match calculated", bool(ctx)),
            ("Learning started", bool(progress)), ("Skill added to CV", added)]
