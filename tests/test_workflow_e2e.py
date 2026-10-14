"""Complete workflow through the core modules:
upload CV + job -> extract -> analyse -> learn -> confirm -> add skill to CV -> new score -> download files."""
import io

import pytest

from core import cv_builder, extraction, pipeline, repository as repo, storage
from core import learning_content as lc
from core.db import DB_INFO, get_engine
from core.report import build_report_pdf
from tests.conftest import UNIQ
from tests.sample_files import CV_TEXT, JOB_TEXT, cv_docx_bytes, text_pdf_bytes


@pytest.fixture(scope="module")
def ctx():
    get_engine()
    cand = repo.get_or_create_candidate(f"E2E User {UNIQ}")
    cv = extraction.extract_text(cv_docx_bytes(), "cv.docx", extraction.RESUME_TYPES)
    raw = storage.save_raw(cv_docx_bytes(), "cv.docx", "resume")
    resume_id = repo.save_resume(cand.id, "cv.docx", "docx", 1000, raw, cv.method, cv.text, cv.text)
    job_id = repo.save_job(cand.id, "Data Analyst", "Example Co", "typed", None, JOB_TEXT)
    match_id, result = pipeline.analyze(cand.id, resume_id, job_id)
    return {"cand": cand.id, "resume": resume_id, "job": job_id, "match": match_id, "result": result, "raw": raw}


def test_database_backend_matches_configuration():
    import os
    get_engine()
    expected = "postgresql" if os.environ.get("FITCHECK_TEST_DATABASE_URL") else "sqlite"
    assert DB_INFO["backend"] == expected and DB_INFO["fallback"] is False


def test_unreachable_postgres_falls_back_to_sqlite(tmp_path):
    """Run in a clean process so the module-level engine of this test session is untouched."""
    import subprocess
    import sys
    code = ("import sys; sys.path.insert(0, %r);"
            "from core.db import get_engine, DB_INFO; get_engine();"
            "print(DB_INFO['backend'], DB_INFO['fallback'])") % str(__import__("pathlib").Path(__file__).resolve().parents[1])
    env = {**__import__("os").environ, "DATABASE_URL": "postgresql+psycopg2://x:y@127.0.0.1:1/none",
           "FITCHECK_DATA_DIR": str(tmp_path)}
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == "sqlite True", out.stderr[-400:]


def test_profile_is_persistent_and_case_insensitive():
    a = repo.get_or_create_candidate(f"Persist Me {UNIQ}")
    b = repo.get_or_create_candidate(f"persist me {UNIQ}")
    assert a.id == b.id


def test_analysis_saved(ctx):
    r = ctx["result"]
    assert "SQL" in r.missing_required and "Python" in r.matched
    stored = repo.get_match(ctx["match"])
    assert stored.final_score == r.final_score and stored.details["missing_required"] == r.missing_required
    assert repo.get_resume(ctx["resume"]).original_text == repo.get_resume(ctx["resume"]).reviewed_text
    assert storage.read_raw(ctx["raw"])                      # original file kept


def test_full_learning_and_add_to_cv(ctx):
    cand, resume_id, job_id = ctx["cand"], ctx["resume"], ctx["job"]
    skill = "SQL"
    old_score = ctx["result"].final_score

    # learning path + progress persisted
    path = lc.get_learning_path(skill)
    modules = repo.ensure_modules(skill, "Databases", path["stages"])
    assert len(modules) == sum(len(s["topics"]) for s in path["stages"])
    assert repo.ensure_modules(skill, "Databases", path["stages"]) == modules        # idempotent
    assert repo.get_path(cand, skill) is None
    repo.set_topic_completed(cand, skill, modules[0]["id"], True)
    assert repo.get_path(cand, skill)["status"] == "in_progress"
    assert repo.get_path(cand, skill)["last_module_id"] == modules[0]["id"]
    assert repo.completed_module_ids(cand, skill) == {modules[0]["id"]}
    repo.set_topic_completed(cand, skill, modules[0]["id"], False)
    assert repo.completed_module_ids(cand, skill) == set()
    for m in modules:
        repo.set_topic_completed(cand, skill, m["id"], True)
    summary = [p for p in repo.progress_summary(cand) if p["skill"] == skill][0]
    assert summary["done"] == summary["total"] == len(modules)
    repo.mark_path_completed(cand, skill)
    assert repo.get_path(cand, skill)["status"] == "completed"

    # nothing is added automatically
    assert repo.list_cv_versions(resume_id) == [] and repo.learned_skills(resume_id) == []

    # confirmed add
    change = pipeline.add_skill_to_cv(cand, resume_id, job_id, skill, "SQL", "SKILLS")
    assert change["new_score"] > old_score and change["old_score"] == old_score
    assert any("SQL" in line for line in change["explanation"])
    version = repo.latest_cv_version(resume_id)
    assert version.added_skill == "SQL" and version.version_no == 1
    assert "Python, Excel, Pandas, Data Cleaning, Communication, SQL" in version.content_text
    # original untouched
    original = repo.get_resume(resume_id)
    assert "SQL" not in original.reviewed_text.split("PROJECTS")[0]
    # new match recorded and SQL no longer missing
    new_match = repo.get_match(change["match_id"])
    assert "SQL" in new_match.details["matched"] and "SQL" not in new_match.details["missing_required"]
    assert new_match.cv_version_id == version.id

    # duplicates are refused
    with pytest.raises(ValueError, match="already"):
        pipeline.add_skill_to_cv(cand, resume_id, job_id, skill, "SQL", "SKILLS")

    # a second skill builds on the first version
    change2 = pipeline.add_skill_to_cv(cand, resume_id, job_id, "Power BI", "Power BI", "SKILLS")
    text2 = repo.latest_cv_version(resume_id).content_text
    assert "SQL, Power BI" in text2 and change2["new_score"] > change["new_score"]
    assert repo.learned_skills(resume_id) == ["SQL", "Power BI"]

    # baseline stays the first original analysis
    base = pipeline.baseline_match(cand, resume_id, job_id)
    assert base.id == ctx["match"] and base.final_score == old_score

    # downloads
    sections = cv_builder.sections_from_dicts(repo.latest_cv_version(resume_id).content_json)
    import docx
    doc = docx.Document(io.BytesIO(cv_builder.to_docx(sections)))
    assert "SQL, Power BI" in "\n".join(p.text for p in doc.paragraphs)
    assert cv_builder.to_pdf(sections).startswith(b"%PDF")
    latest = repo.list_matches(cand, resume_id=resume_id, job_id=job_id)[-1]
    report = build_report_pdf(f"E2E User {UNIQ}", "Data Analyst", "Example Co",
                              latest.details, {"final_score": old_score}, repo.learned_skills(resume_id),
                              repo.progress_summary(cand))
    assert report.startswith(b"%PDF") and len(report) > 1500


def test_manual_edit_creates_version_and_rescored(ctx):
    cand, resume_id, job_id = ctx["cand"], ctx["resume"], ctx["job"]
    current = repo.latest_cv_version(resume_id).content_text
    match_id, result = pipeline.save_edited_cv(cand, resume_id, job_id, current + "\nCERTIFICATIONS\nGoogle Data Analytics")
    assert repo.latest_cv_version(resume_id).added_skill is None
    assert repo.get_match(match_id).cv_version_id == repo.latest_cv_version(resume_id).id
    # learned skills are still counted after a manual edit
    assert "SQL" in result.matched


def test_pdf_cv_flow_marks_pdf_and_still_works():
    cand = repo.get_or_create_candidate(f"PDF User {UNIQ}")
    res = extraction.extract_text(text_pdf_bytes(), "cv.pdf", extraction.RESUME_TYPES)
    rid = repo.save_resume(cand.id, "cv.pdf", "pdf", 10, None, res.method, res.text, res.text)
    jid = repo.save_job(cand.id, "Data Analyst", None, "typed", None, JOB_TEXT)
    pipeline.analyze(cand.id, rid, jid)
    change = pipeline.add_skill_to_cv(cand.id, rid, jid, "Tableau", "Tableau", "Technical Skills")   # new section
    names = cv_builder.section_names(pipeline.current_cv_sections(rid))
    assert names[-1] == "Technical Skills" and change["new_score"] >= change["old_score"]
