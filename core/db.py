"""Relational schema (SQLAlchemy 2.0) and engine management.

PostgreSQL is the primary database (set DATABASE_URL).  If the URL is empty or the server
cannot be reached, FitCheck transparently falls back to a local SQLite file.
"""
from __future__ import annotations

import datetime as dt
import logging
from contextlib import contextmanager

from sqlalchemy import (JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, LargeBinary, String, Text,
                        UniqueConstraint, create_engine, event, text)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

import config

log = logging.getLogger("fitcheck.db")


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Candidate(Base):
    """A user profile / session owner."""
    __tablename__ = "candidates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    auth_provider: Mapped[str] = mapped_column(String(40), default="local", nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_salt: Mapped[str | None] = mapped_column(String(64), nullable=True)   # hex salt for email/password auth
    google_id: Mapped[str | None] = mapped_column(String(200), nullable=True)       # Google OAuth subject
    avatar_url: Mapped[str | None] = mapped_column(String(600), nullable=True)      # Google profile picture URL
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class Resume(Base):
    """Original resume. `original_text` is never modified; `reviewed_text` is what the user confirmed."""
    __tablename__ = "resumes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    raw_path: Mapped[str | None] = mapped_column(String(600))
    extraction_method: Mapped[str] = mapped_column(String(60), nullable=False, default="unknown")
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    reviewed_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class JobPosting(Base):
    __tablename__ = "job_postings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Untitled job")
    company: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="typed")  # typed|pdf|image|txt|sample
    raw_path: Mapped[str | None] = mapped_column(String(600))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="Other")


class OnetOccupation(Base):
    """Imported O*NET occupation reference profile; never user-provided resume data."""
    __tablename__ = "onet_occupations"
    onet_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    task_statements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    essential_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    transferable_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    software_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    source_version: Mapped[str] = mapped_column(String(20), nullable=False, default="31.0")


class ResumeSkill(Base):
    __tablename__ = "resume_skills"
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)


class JobSkill(Base):
    __tablename__ = "job_skills"
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    importance: Mapped[str] = mapped_column(String(10), nullable=False, default="required")
    __table_args__ = (CheckConstraint("importance IN ('required','preferred')", name="ck_job_skills_importance"),)


class CVVersion(Base):
    """Updated CV content. Version numbers start at 1 per resume; the original is kept in `resumes`."""
    __tablename__ = "cv_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    version_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content_json: Mapped[list] = mapped_column(JSON, nullable=False)       # [{"heading":..., "lines":[...]}]
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    added_skill: Mapped[str | None] = mapped_column(String(100))
    section_name: Mapped[str | None] = mapped_column(String(100))
    note: Mapped[str | None] = mapped_column(String(255))
    docx_bytes: Mapped[bytes | None] = mapped_column(LargeBinary)          # edited original DOCX (design kept)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("resume_id", "version_no", name="uq_cv_resume_version"),)


class MatchResult(Base):
    __tablename__ = "match_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True, nullable=False)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id", ondelete="CASCADE"), index=True, nullable=False)
    cv_version_id: Mapped[int | None] = mapped_column(ForeignKey("cv_versions.id", ondelete="SET NULL"))
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    skill_score: Mapped[float] = mapped_column(Float, nullable=False)
    text_similarity: Mapped[float] = mapped_column(Float, nullable=False)
    skill_weight: Mapped[float] = mapped_column(Float, nullable=False)
    text_weight: Mapped[float] = mapped_column(Float, nullable=False)
    preferred_weight: Mapped[float] = mapped_column(Float, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    __table_args__ = (CheckConstraint("final_score >= 0 AND final_score <= 100", name="ck_match_score_range"),)


class LearningModule(Base):
    """One topic (lesson) of a skill's learning path."""
    __tablename__ = "learning_modules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True, nullable=False)
    topic_key: Mapped[str] = mapped_column(String(80), nullable=False)
    stage_no: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_title: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("skill_id", "topic_key", name="uq_module_skill_topic"),)


class LearningPath(Base):
    __tablename__ = "learning_paths"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
    last_module_id: Mapped[int | None] = mapped_column(ForeignKey("learning_modules.id", ondelete="SET NULL"))
    __table_args__ = (UniqueConstraint("candidate_id", "skill_id", name="uq_path_candidate_skill"),
                      CheckConstraint("status IN ('in_progress','completed')", name="ck_path_status"))


class LearningProgress(Base):
    __tablename__ = "learning_progress"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id", ondelete="CASCADE"), index=True, nullable=False)
    module_id: Mapped[int] = mapped_column(ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime)
    __table_args__ = (UniqueConstraint("candidate_id", "module_id", name="uq_progress_candidate_module"),)


# ---- engine management -------------------------------------------------------------
_engine = None
_session_factory = None
DB_INFO: dict = {}


def _make_engine(url: str):
    kwargs: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    engine = create_engine(url, **kwargs)
    if url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _record):          # enforce foreign keys in SQLite
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    return engine


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        url = config.DATABASE_URL
        try:
            engine = _make_engine(url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            DB_INFO.update(backend=engine.dialect.name, url=make_url(url).render_as_string(hide_password=True),
                           fallback=False, error=None)
        except Exception as exc:                  # PostgreSQL down / wrong password / driver missing
            log.warning("Database %s unavailable (%s). Falling back to SQLite.", url.split("@")[-1], exc)
            engine = _make_engine(config.SQLITE_URL)
            DB_INFO.update(backend="sqlite", url=config.SQLITE_URL, fallback=True, error=str(exc).splitlines()[0][:220])
        Base.metadata.create_all(engine)
        _engine = engine
        _migrate_quietly(engine)
        _session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    return _engine


def _migrate_quietly(engine) -> None:
    global _engine
    try:
        added = add_missing_columns()
        if added:
            log.info("Added missing columns: %s", ", ".join(added))
    except Exception as exc:
        log.warning("Could not upgrade the database schema automatically: %s", exc)


def reset_engine():
    """Used by tests and the init script to force a fresh connection."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
    DB_INFO.clear()


@contextmanager
def session_scope():
    get_engine()
    session = _session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def add_missing_columns() -> list[str]:
    """Tiny migration helper: adds columns introduced after a database was first created.

    `create_all` never alters existing tables, so an old PostgreSQL/SQLite file would miss new columns.
    Returns the list of added "table.column" names.
    """
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy import text as sa_text
    engine = get_engine()
    added = []
    insp = sa_inspect(engine)
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            continue
        existing = {c["name"] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            col_type = col.type.compile(dialect=engine.dialect)
            with engine.begin() as conn:
                conn.execute(sa_text(f'ALTER TABLE {table.name} ADD COLUMN {col.name} {col_type}'))
            added.append(f"{table.name}.{col.name}")
    return added
