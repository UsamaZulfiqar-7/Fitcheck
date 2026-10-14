"""All database reads/writes used by the application (safe, parameterised ORM operations)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, func, select

from core.db import (Candidate, CVVersion, JobPosting, JobSkill, LearningModule, LearningPath, LearningProgress,
                     MatchResult, Resume, ResumeSkill, Skill, session_scope, utcnow)
from core.skills import skill_category


# ---- candidates ---------------------------------------------------------------------
def get_or_create_candidate(name: str) -> Candidate:
    name = (name or "").strip()[:120] or "Guest"
    with session_scope() as s:
        row = s.scalar(select(Candidate).where(func.lower(Candidate.display_name) == name.lower()))
        if row is None:
            row = Candidate(display_name=name)
            s.add(row)
            s.flush()
        return row


# ---- skills ------------------------------------------------------------------------------
def _skill_ids(s, names, categories: dict | None = None) -> dict[str, int]:
    ids: dict[str, int] = {}
    for name in dict.fromkeys(names):
        row = s.scalar(select(Skill).where(Skill.name == name))
        if row is None:
            row = Skill(name=name, category=(categories or {}).get(name) or skill_category(name))
            s.add(row)
            s.flush()
        ids[name] = row.id
    return ids


# ---- resumes / jobs ------------------------------------------------------------------------
def save_resume(candidate_id: int, filename: str, file_type: str, size: int, raw_path: str | None,
                method: str, original_text: str, reviewed_text: str) -> int:
    with session_scope() as s:
        row = Resume(candidate_id=candidate_id, filename=filename[:255], file_type=file_type[:10],
                     file_size_bytes=size, raw_path=raw_path, extraction_method=method[:60],
                     original_text=original_text, reviewed_text=reviewed_text)
        s.add(row)
        s.flush()
        return row.id


def get_resume(resume_id: int) -> Resume | None:
    with session_scope() as s:
        return s.get(Resume, resume_id)


def save_job(candidate_id: int | None, title: str, company: str | None, source: str, raw_path: str | None,
             text: str, is_synthetic: bool = False) -> int:
    with session_scope() as s:
        row = JobPosting(candidate_id=candidate_id, title=(title or "Untitled job")[:200],
                         company=(company or None), source=source, raw_path=raw_path, text=text,
                         is_synthetic=is_synthetic)
        s.add(row)
        s.flush()
        return row.id


def get_job(job_id: int) -> JobPosting | None:
    with session_scope() as s:
        return s.get(JobPosting, job_id)


def set_resume_skills(resume_id: int, names: list[str]) -> None:
    with session_scope() as s:
        ids = _skill_ids(s, names)
        s.execute(delete(ResumeSkill).where(ResumeSkill.resume_id == resume_id))
        for sid in ids.values():
            s.add(ResumeSkill(resume_id=resume_id, skill_id=sid))


def set_job_skills(job_id: int, importance: dict[str, str]) -> None:
    with session_scope() as s:
        ids = _skill_ids(s, list(importance))
        s.execute(delete(JobSkill).where(JobSkill.job_id == job_id))
        for name, sid in ids.items():
            s.add(JobSkill(job_id=job_id, skill_id=sid, importance=importance[name]))


# ---- match results -------------------------------------------------------------------------------
def save_match(candidate_id: int, resume_id: int, job_id: int, cv_version_id: int | None, result) -> int:
    with session_scope() as s:
        row = MatchResult(candidate_id=candidate_id, resume_id=resume_id, job_id=job_id,
                          cv_version_id=cv_version_id, final_score=result.final_score,
                          skill_score=result.skill_score, text_similarity=result.text_similarity,
                          skill_weight=result.skill_weight, text_weight=result.text_weight,
                          preferred_weight=result.preferred_weight, details=result.to_dict())
        s.add(row)
        s.flush()
        return row.id


def get_match(match_id: int) -> MatchResult | None:
    with session_scope() as s:
        return s.get(MatchResult, match_id)


def list_matches(candidate_id: int, resume_id: int | None = None, job_id: int | None = None) -> list[MatchResult]:
    with session_scope() as s:
        q = select(MatchResult).where(MatchResult.candidate_id == candidate_id)
        if resume_id:
            q = q.where(MatchResult.resume_id == resume_id)
        if job_id:
            q = q.where(MatchResult.job_id == job_id)
        return list(s.scalars(q.order_by(MatchResult.id)))


def latest_match(candidate_id: int) -> MatchResult | None:
    with session_scope() as s:
        return s.scalar(select(MatchResult).where(MatchResult.candidate_id == candidate_id)
                        .order_by(MatchResult.id.desc()).limit(1))


def count_matches(candidate_id: int) -> int:
    with session_scope() as s:
        return s.scalar(select(func.count()).select_from(MatchResult).where(MatchResult.candidate_id == candidate_id)) or 0


def list_analyses(candidate_id: int) -> list[dict]:
    """Latest match per (resume, job) pair with job title - used by 'load previous analysis'."""
    with session_scope() as s:
        rows = s.execute(
            select(MatchResult, JobPosting.title, JobPosting.company, Resume.filename)
            .join(JobPosting, JobPosting.id == MatchResult.job_id)
            .join(Resume, Resume.id == MatchResult.resume_id)
            .where(MatchResult.candidate_id == candidate_id).order_by(MatchResult.id.desc())).all()
    seen, out = set(), []
    for match, title, company, filename in rows:
        key = (match.resume_id, match.job_id)
        if key in seen:
            continue
        seen.add(key)
        out.append({"match_id": match.id, "resume_id": match.resume_id, "job_id": match.job_id,
                    "title": title, "company": company, "filename": filename,
                    "score": match.final_score, "created_at": match.created_at})
    return out


# ---- CV versions ---------------------------------------------------------------------------------------
def create_cv_version(candidate_id: int, resume_id: int, sections: list[dict], text: str,
                      added_skill: str | None, section_name: str | None, note: str | None = None,
                      docx_bytes: bytes | None = None) -> CVVersion:
    with session_scope() as s:
        last = s.scalar(select(func.max(CVVersion.version_no)).where(CVVersion.resume_id == resume_id)) or 0
        row = CVVersion(candidate_id=candidate_id, resume_id=resume_id, version_no=last + 1,
                        content_json=sections, content_text=text, added_skill=added_skill,
                        section_name=section_name, note=note, docx_bytes=docx_bytes)
        s.add(row)
        s.flush()
        return row


def list_cv_versions(resume_id: int) -> list[CVVersion]:
    with session_scope() as s:
        return list(s.scalars(select(CVVersion).where(CVVersion.resume_id == resume_id).order_by(CVVersion.version_no)))


def latest_cv_version(resume_id: int) -> CVVersion | None:
    with session_scope() as s:
        return s.scalar(select(CVVersion).where(CVVersion.resume_id == resume_id)
                        .order_by(CVVersion.version_no.desc()).limit(1))


def learned_skills(resume_id: int) -> list[str]:
    """Skills the user confirmed and added to this resume's CV versions."""
    return [v.added_skill for v in list_cv_versions(resume_id) if v.added_skill]


# ---- learning -------------------------------------------------------------------------------------------------
def ensure_modules(skill_name: str, category: str | None, stages: list[dict]) -> list[dict]:
    """Make sure every topic of a learning path exists in `learning_modules`; returns ordered module dicts."""
    out = []
    with session_scope() as s:
        skill_id = _skill_ids(s, [skill_name], {skill_name: category})[skill_name]
        existing = {m.topic_key: m for m in s.scalars(select(LearningModule).where(LearningModule.skill_id == skill_id))}
        position = 0
        for stage_no, stage in enumerate(stages, start=1):
            for topic in stage["topics"]:
                position += 1
                row = existing.get(topic["key"])
                if row is None:
                    row = LearningModule(skill_id=skill_id, topic_key=topic["key"], stage_no=stage_no,
                                         stage_title=stage["title"][:120], title=topic["title"][:200], position=position)
                    s.add(row)
                    s.flush()
                out.append({"id": row.id, "key": row.topic_key, "title": row.title, "stage_no": stage_no,
                            "stage_title": stage["title"], "position": position})
    return out


def _skill_id(s, skill_name: str) -> int | None:
    return s.scalar(select(Skill.id).where(Skill.name == skill_name))


def get_path(candidate_id: int, skill_name: str) -> dict | None:
    with session_scope() as s:
        sid = _skill_id(s, skill_name)
        if sid is None:
            return None
        row = s.scalar(select(LearningPath).where(LearningPath.candidate_id == candidate_id, LearningPath.skill_id == sid))
        if row is None:
            return None
        return {"status": row.status, "started_at": row.started_at, "completed_at": row.completed_at,
                "last_module_id": row.last_module_id}


def start_path(candidate_id: int, skill_name: str) -> None:
    with session_scope() as s:
        sid = _skill_ids(s, [skill_name])[skill_name]
        row = s.scalar(select(LearningPath).where(LearningPath.candidate_id == candidate_id, LearningPath.skill_id == sid))
        if row is None:
            s.add(LearningPath(candidate_id=candidate_id, skill_id=sid, status="in_progress"))


def completed_module_ids(candidate_id: int, skill_name: str) -> set[int]:
    with session_scope() as s:
        sid = _skill_id(s, skill_name)
        if sid is None:
            return set()
        q = (select(LearningProgress.module_id).join(LearningModule, LearningModule.id == LearningProgress.module_id)
             .where(LearningProgress.candidate_id == candidate_id, LearningProgress.completed.is_(True),
                    LearningModule.skill_id == sid))
        return set(s.scalars(q))


def set_topic_completed(candidate_id: int, skill_name: str, module_id: int, completed: bool) -> None:
    with session_scope() as s:
        sid = _skill_ids(s, [skill_name])[skill_name]
        row = s.scalar(select(LearningProgress).where(LearningProgress.candidate_id == candidate_id,
                                                      LearningProgress.module_id == module_id))
        if row is None:
            row = LearningProgress(candidate_id=candidate_id, module_id=module_id)
            s.add(row)
        row.completed = completed
        row.completed_at = utcnow() if completed else None
        path = s.scalar(select(LearningPath).where(LearningPath.candidate_id == candidate_id, LearningPath.skill_id == sid))
        if path is None:
            path = LearningPath(candidate_id=candidate_id, skill_id=sid, status="in_progress")
            s.add(path)
        if completed:
            path.last_module_id = module_id
        if not completed and path.status == "completed":      # un-ticking a topic re-opens the path
            path.status = "in_progress"
            path.completed_at = None


def mark_path_completed(candidate_id: int, skill_name: str) -> None:
    with session_scope() as s:
        sid = _skill_ids(s, [skill_name])[skill_name]
        path = s.scalar(select(LearningPath).where(LearningPath.candidate_id == candidate_id, LearningPath.skill_id == sid))
        if path is None:
            path = LearningPath(candidate_id=candidate_id, skill_id=sid)
            s.add(path)
        path.status = "completed"
        path.completed_at = utcnow()


def progress_summary(candidate_id: int) -> list[dict]:
    with session_scope() as s:
        paths = s.execute(select(LearningPath, Skill.name, Skill.category).join(Skill, Skill.id == LearningPath.skill_id)
                          .where(LearningPath.candidate_id == candidate_id).order_by(LearningPath.started_at)).all()
        out = []
        for path, name, category in paths:
            total = s.scalar(select(func.count()).select_from(LearningModule).where(LearningModule.skill_id == path.skill_id)) or 0
            done = s.scalar(select(func.count()).select_from(LearningProgress)
                            .join(LearningModule, LearningModule.id == LearningProgress.module_id)
                            .where(LearningProgress.candidate_id == candidate_id, LearningProgress.completed.is_(True),
                                   LearningModule.skill_id == path.skill_id)) or 0
            last_title = None
            if path.last_module_id:
                last_title = s.scalar(select(LearningModule.title).where(LearningModule.id == path.last_module_id))
            out.append({"skill": name, "category": category, "status": path.status, "total": total, "done": done,
                        "last_topic": last_title, "started_at": path.started_at, "completed_at": path.completed_at})
        return out


def count_synthetic_jobs() -> int:
    with session_scope() as s:
        return s.scalar(select(func.count()).select_from(JobPosting).where(JobPosting.is_synthetic.is_(True))) or 0
