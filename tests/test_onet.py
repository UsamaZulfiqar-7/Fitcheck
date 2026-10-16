import csv
import io
import zipfile

from core import onet
from core.db import OnetOccupation, session_scope


def _archive() -> bytes:
    files = {
        "Occupation Data.txt": (
            ["O*NET-SOC Code", "Title", "Description"],
            [
                ["15-2051.00", "Data Scientists", "Analyze data using statistics and machine learning."],
                ["47-2152.00", "Plumbers", "Install and repair water pipes and plumbing systems."],
            ],
        ),
        "Essential Skills.txt": (
            ["O*NET-SOC Code", "Element Name", "Scale ID", "Data Value", "Recommend Suppress", "Not Relevant"],
            [
                ["15-2051.00", "Mathematics", "IM", "4.2", "N", "N"],
                ["15-2051.00", "Mathematics", "LV", "4.7", "N", "N"],
                ["15-2051.00", "Suppressed item", "IM", "3.8", "Y", "N"],
                ["47-2152.00", "Repairing", "IM", "4.1", "N", "N"],
            ],
        ),
        "Transferable Skills.txt": (
            ["O*NET-SOC Code", "Element Name", "Scale ID", "Data Value", "Recommend Suppress", "Not Relevant"],
            [["15-2051.00", "Critical Thinking", "IM", "4.0", "N", "N"]],
        ),
        "Software Skills.txt": (
            ["O*NET-SOC Code", "Workplace Example", "Element Name", "Hot Technology", "In Demand"],
            [["15-2051.00", "Python", "Object oriented software", "Y", "Y"]],
        ),
        "Task Statements.txt": (
            ["O*NET-SOC Code", "Task", "Task Type"],
            [
                ["15-2051.00", "Build statistical models from large datasets.", "Core"],
                ["47-2152.00", "Repair leaking pipes.", "Core"],
            ],
        ),
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for filename, (headers, rows) in files.items():
            text = io.StringIO()
            writer = csv.writer(text, delimiter="\t", lineterminator="\n")
            writer.writerow(headers)
            writer.writerows(rows)
            archive.writestr(f"db_31_0_text/{filename}", text.getvalue())
    return buffer.getvalue()


def test_parse_onet_archive_filters_ratings_and_groups_profiles():
    profiles = onet.parse_onet_archive(_archive())

    assert len(profiles) == 2
    scientist = profiles[0]
    assert scientist["onet_code"] == "15-2051.00"
    assert scientist["essential_skills"] == [{"name": "Mathematics", "importance": 4.2}]
    assert scientist["transferable_skills"] == [{"name": "Critical Thinking", "importance": 4.0}]
    assert scientist["software_skills"][0]["name"] == "Python"
    assert scientist["task_statements"] == ["Build statistical models from large datasets."]


def test_import_is_idempotent_and_job_text_gets_occupation_context():
    payload = _archive()

    assert onet.import_onet_archive(payload) == 2
    assert onet.import_onet_archive(payload) == 2
    profiles = onet.recommend_occupations(
        "Data scientist to build statistical models using machine learning and analyze data",
        limit=2,
    )

    assert profiles[0]["onet_code"] == "15-2051.00"
    assert profiles[0]["essential_skills"][0]["name"] == "Mathematics"
    assert profiles[0]["software_skills"][0]["name"] == "Python"
    assert profiles[0]["source_version"] == "31.0"
    with session_scope() as session:
        assert session.query(OnetOccupation).count() == 2


def test_invalid_archive_does_not_replace_imported_profiles():
    onet.import_onet_archive(_archive())

    try:
        onet.import_onet_archive(b"not a zip archive")
    except ValueError as exc:
        assert "valid ZIP" in str(exc)
    else:
        raise AssertionError("Invalid O*NET archive should be rejected.")

    profiles = onet.recommend_occupations("Build statistical models from data")
    assert profiles[0]["onet_code"] == "15-2051.00"


def test_skill_gap_page_shows_advisory_onet_context():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    from core import pipeline, repository as repo
    from tests.sample_files import CV_TEXT

    onet.import_onet_archive(_archive())
    candidate = repo.get_or_create_candidate("O*NET UI integration")
    resume_id = repo.save_resume(
        candidate.id, "onet-test.txt", "txt", 100, None, "plain text", CV_TEXT, CV_TEXT
    )
    job_text = (
        "Data scientist to build statistical models using machine learning, "
        "Python, statistics, and analyze data."
    )
    job_id = repo.save_job(candidate.id, "Data Scientist", None, "typed", None, job_text)
    pipeline.analyze(candidate.id, resume_id, job_id)

    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"))
    app.session_state["_fitcheck_auth"] = {
        "id": candidate.id,
        "name": candidate.display_name,
        "email": "",
        "provider": "email",
    }
    app.run()
    app.session_state["nav"] = "Skill Gap Analysis"
    app.run()

    assert not app.exception, [error.value for error in app.exception]
    assert any("Data Scientists" in item.value for item in app.markdown)
    assert any("does not change your match score" in item.value for item in app.caption)
