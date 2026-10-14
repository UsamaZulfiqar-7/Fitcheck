"""Modular pipeline.

Resume + job ingestion -> raw file storage -> text extraction -> skill extraction/normalisation
-> match score -> skill-gap analysis -> personalised learning -> progress storage
-> updated CV generation -> final match score and report.

Each step is a plain function so the stages are easy to explain and to test.  Processing is
single-machine (no distributed engine is used).
"""
from __future__ import annotations

from core import cv_builder, repository as repo, storage
from core.matching import MatchResult, compute_match, explain_score_change
from core.skills import extract_job_skills, extract_skills


def default_settings() -> dict:
    import config
    return {"skill_weight": config.SKILL_WEIGHT, "preferred_weight": config.PREFERRED_WEIGHT,
            "use_semantic": config.USE_SEMANTIC}


def analyze(candidate_id: int, resume_id: int, job_id: int, settings: dict | None = None, *,
            cv_text: str | None = None, cv_version_id: int | None = None) -> tuple[int, MatchResult]:
    """Run skill extraction + scoring and store the result. Returns (match_id, MatchResult)."""
    settings = {**default_settings(), **(settings or {})}
    resume = repo.get_resume(resume_id)
    job = repo.get_job(job_id)
    if resume is None or job is None:
        raise ValueError("Resume or job posting not found in the database.")
    text = cv_text if cv_text is not None else resume.reviewed_text

    resume_skills = extract_skills(text)
    for learned in repo.learned_skills(resume_id):          # skills the user confirmed and added
        if learned not in resume_skills and cv_version_id is not None:
            resume_skills.append(learned)
    job_skills = extract_job_skills(job.text)

    if cv_version_id is None:                                # baseline analysis -> store skill mappings
        repo.set_resume_skills(resume_id, resume_skills)
        repo.set_job_skills(job_id, job_skills)

    result = compute_match(text, job.text, resume_skills, job_skills,
                           skill_weight=settings["skill_weight"], preferred_weight=settings["preferred_weight"],
                           use_semantic=settings["use_semantic"])
    match_id = repo.save_match(candidate_id, resume_id, job_id, cv_version_id, result)
    return match_id, result


def current_cv_sections(resume_id: int) -> list[cv_builder.Section]:
    """Latest saved CV version, or the reviewed original text parsed into sections."""
    latest = repo.latest_cv_version(resume_id)
    if latest is not None:
        return cv_builder.sections_from_dicts(latest.content_json)
    resume = repo.get_resume(resume_id)
    return cv_builder.parse_cv(resume.reviewed_text)


def add_skill_to_cv(candidate_id: int, resume_id: int, job_id: int, skill: str, wording: str,
                    section_name: str, settings: dict | None = None) -> dict:
    """Add a CONFIRMED skill to a new CV version, recalculate the score and explain the change.

    DOCX originals are edited in place (design kept). PDF/TXT originals are rebuilt from text.
    """
    sections = current_cv_sections(resume_id)
    if cv_builder.skill_already_in_cv(sections, wording):
        raise ValueError(f"'{wording}' already appears in your CV, so it was not added twice.")
    previous = repo.list_matches(candidate_id, resume_id=resume_id, job_id=job_id)
    old = previous[-1] if previous else None

    updated = cv_builder.add_skill(sections, wording, section_name)
    text = cv_builder.cv_to_text(updated)
    docx_bytes = None
    resume = repo.get_resume(resume_id)
    if resume.file_type == "docx" and resume.raw_path:
        original = storage.read_raw(resume.raw_path)
        if original:
            docx_bytes = cv_builder.add_skill_to_docx(original, wording, section_name)
    version = repo.create_cv_version(candidate_id, resume_id, cv_builder.sections_to_dicts(updated), text,
                                     added_skill=skill, section_name=section_name,
                                     note=f"Added '{wording}' to {section_name}", docx_bytes=docx_bytes)
    match_id, result = analyze(candidate_id, resume_id, job_id, settings, cv_text=text, cv_version_id=version.id)
    explanation = []
    if old is not None:
        old_view = {"final_score": old.final_score, "skill_score": old.skill_score,
                    "text_similarity": old.text_similarity}
        new_view = {**result.to_dict()}
        explanation = explain_score_change(old_view, new_view, skill)
    return {"version_no": version.version_no, "match_id": match_id, "old_score": old.final_score if old else None,
            "new_score": result.final_score, "old_skill": old.skill_score if old else None,
            "new_skill": result.skill_score, "explanation": explanation, "skill": skill, "section": section_name}


def save_edited_cv(candidate_id: int, resume_id: int, job_id: int, edited_text: str,
                   settings: dict | None = None) -> tuple[int, MatchResult]:
    """Save manual edits as a new CV version and recalculate the score."""
    sections = cv_builder.parse_cv(edited_text)
    text = cv_builder.cv_to_text(sections)
    version = repo.create_cv_version(candidate_id, resume_id, cv_builder.sections_to_dicts(sections), text,
                                     added_skill=None, section_name=None, note="Manual edit")
    return analyze(candidate_id, resume_id, job_id, settings, cv_text=text, cv_version_id=version.id)


def baseline_match(candidate_id: int, resume_id: int, job_id: int):
    """The first match for this resume/job pair that used the original CV (no CV version)."""
    for m in repo.list_matches(candidate_id, resume_id=resume_id, job_id=job_id):
        if m.cv_version_id is None:
            return m
    return None
