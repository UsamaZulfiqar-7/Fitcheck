"""Drive the real Streamlit app with AppTest: every page renders, and the learning -> add-to-CV flow works by clicking."""
import pytest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from core import pipeline, repository as repo
from core.db import get_engine
from tests.conftest import UNIQ
from tests.sample_files import CV_TEXT, JOB_TEXT

PAGES = ["Home Dashboard", "Resume & Job Analysis", "Match Results", "Skill Gap Analysis",
         "AI Skill Assistant", "Personalized Learning Center", "My Learning Progress", "Updated CV & Downloads", "Settings"]
NAME = f"UI Tester {UNIQ}"


def new_app():
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=60)
    at.run()
    return at


def go(at, page):
    at.session_state["nav"] = page
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def set_profile(at, name):
    at.sidebar.text_input(key="profile_name").set_value(name).run()
    assert not at.exception


@pytest.fixture(scope="module", autouse=True)
def prepared():
    get_engine()
    cand = repo.get_or_create_candidate(NAME)
    rid = repo.save_resume(cand.id, "cv.txt", "txt", 100, None, "plain text", CV_TEXT, CV_TEXT)
    jid = repo.save_job(cand.id, "Data Analyst", "Example Co", "typed", None, JOB_TEXT)
    pipeline.analyze(cand.id, rid, jid)
    return cand.id


def test_all_pages_render_empty_profile():
    at = new_app()
    set_profile(at, f"Brand New Person {UNIQ}")
    for page in PAGES:
        go(at, page)
    go(at, "Home Dashboard")
    assert any("Start" in b.label for b in at.button)


def test_all_pages_render_with_analysis():
    at = new_app()
    set_profile(at, NAME)                       # latest analysis is restored from the database
    assert at.session_state["match_id"]
    for page in PAGES:
        go(at, page)
    go(at, "Match Results")
    assert any("Final score" in m.value for m in at.markdown)


def test_analysis_page_rejects_empty_run():
    at = new_app()
    set_profile(at, NAME)
    go(at, "Resume & Job Analysis")
    at.button(key="run_analysis").click().run()
    assert any("upload" in e.value.lower() for e in at.error)


def test_sample_job_loads_into_editor():
    at = new_app()
    set_profile(at, NAME)
    go(at, "Resume & Job Analysis")
    at.radio(key="job_mode").set_value("Use a synthetic sample job").run()
    at.button(key="load_sample").click().run()
    assert "Requirements" in at.session_state["job_text_area"] and at.session_state["job_title_in"]


def test_learning_flow_click_through():
    at = new_app()
    set_profile(at, NAME)
    go(at, "Skill Gap Analysis")
    # "Learn SQL" button on the gap page jumps to the learning center with SQL selected
    learn_btns = [b for b in at.button if b.key and b.key.startswith("gap_learn_missing_required_SQL")]
    assert learn_btns
    learn_btns[0].click().run()
    assert at.session_state["nav"] == "Personalized Learning Center" and at.session_state["learn_skill"] == "SQL"

    # the add-to-CV button is locked until the path is completed
    add = [b for b in at.button if b.key == "addcv_SQL"][0]
    assert add.disabled
    at.button(key="start_SQL").click().run()
    boxes = [c for c in at.checkbox if c.key and c.key.startswith("done_")]
    assert len(boxes) >= 5
    boxes[0].check().run()
    assert len(repo.completed_module_ids(at.session_state["cand_id"], "SQL")) == 1      # saved in the database at once
    complete = at.button(key="complete_SQL")
    assert complete.disabled                      # topics remain
    for box in [c for c in at.checkbox if c.key and c.key.startswith("done_")]:
        box.check()
    at.run()
    at.button(key="complete_SQL").click().run()
    assert not at.exception
    add = at.button(key="addcv_SQL")
    assert not add.disabled and add.label == "I've Learned This Skill — Add to My CV"
    add.click().run()

    # explicit confirmation is required
    save = at.button(key="save_SQL")
    assert save.disabled
    # nothing has been added yet
    assert repo.learned_skills(at.session_state["resume_id"]) == []
    at.checkbox(key="confirm_SQL").check().run()
    at.text_input(key="wording_SQL").set_value("SQL").run()
    assert not at.button(key="save_SQL").disabled
    old = repo.get_match(at.session_state["match_id"]).final_score
    at.button(key="save_SQL").click().run()
    assert not at.exception, [e.value for e in at.exception]
    change = at.session_state["cv_last_change"]
    assert change["skill"] == "SQL" and change["new_score"] > old
    assert repo.learned_skills(at.session_state["resume_id"]) == ["SQL"]

    # updated CV page shows the version and downloads exist
    go(at, "Updated CV & Downloads")
    assert any("SQL" in (t.value or "") for t in at.text_area)
    go(at, "My Learning Progress")
    assert any("SQL" in m.value for m in at.markdown)


def test_progress_persists_after_restart():
    at = new_app()                                  # a brand new browser session
    set_profile(at, NAME)
    summary = repo.progress_summary(at.session_state["cand_id"])
    assert any(p["skill"] == "SQL" and p["status"] == "completed" for p in summary)
    go(at, "Personalized Learning Center")
    assert not at.exception


def test_settings_changes_weights():
    at = new_app()
    set_profile(at, NAME)
    go(at, "Settings")
    at.slider(key="sw_slider").set_value(50).run()
    assert at.session_state["skill_weight"] == 0.5


from core import extraction  # noqa: E402
from tests.sample_files import cv_docx_bytes, text_image_bytes, text_pdf_bytes  # noqa: E402


def test_upload_flow_docx_cv_and_image_job_with_ocr():
    at = new_app()
    set_profile(at, f"Upload Tester {UNIQ}")
    go(at, "Resume & Job Analysis")
    at.file_uploader(key="resume_upload").set_value(("cv.docx", cv_docx_bytes(), "application/octet-stream")).run()
    assert not at.exception and "Ayesha Khan" in at.session_state["resume_text_area"]
    at.radio(key="job_mode").set_value("Upload file (PDF, JPG, PNG, TXT)").run()
    if extraction.ocr_available():
        at.file_uploader(key="job_upload").set_value(("job.png", text_image_bytes(), "image/png")).run()
        assert not at.exception and "SQL" in at.session_state["job_text_area"]
    else:
        at.session_state["job_text_area"] = "Requirements:\n- SQL and Python\n- Power BI"
        at.run()
    at.text_input(key="job_title_in").set_value("Data Analyst").run()
    at.button(key="run_analysis").click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["match_id"]
    match = repo.get_match(at.session_state["match_id"])
    assert "SQL" in match.details["job_skills"]
    resume = repo.get_resume(at.session_state["resume_id"])
    assert resume.raw_path and resume.file_type == "docx" and resume.original_text == resume.reviewed_text
    go(at, "Match Results")
    go(at, "Skill Gap Analysis")


def test_user_can_correct_extracted_text_before_analysis():
    at = new_app()
    set_profile(at, f"Editor Tester {UNIQ}")
    go(at, "Resume & Job Analysis")
    at.file_uploader(key="resume_upload").set_value(("cv.pdf", text_pdf_bytes(), "application/pdf")).run()
    corrected = at.session_state["resume_text_area"] + "\nTechnical skills: Tableau"
    at.text_area(key="resume_text_area").set_value(corrected).run()
    at.text_area(key="job_text_area").set_value("Requirements:\n- Tableau and SQL\n- Python").run()
    at.button(key="run_analysis").click().run()
    assert not at.exception
    resume = repo.get_resume(at.session_state["resume_id"])
    assert "Tableau" in resume.reviewed_text and "Tableau" not in resume.original_text     # original kept as extracted
    assert "Tableau" in repo.get_match(at.session_state["match_id"]).details["matched"]


def test_bad_uploads_show_friendly_errors():
    at = new_app()
    set_profile(at, f"Bad Upload Tester {UNIQ}")
    go(at, "Resume & Job Analysis")
    at.file_uploader(key="resume_upload").set_value(("cv.pdf", b"this is not a pdf", "application/pdf")).run()
    assert not at.exception and any("not a valid PDF" in e.value for e in at.error)
    at.file_uploader(key="resume_upload").set_value(("empty.txt", b"", "text/plain")).run()
    assert not at.exception and any("empty" in e.value for e in at.error)
