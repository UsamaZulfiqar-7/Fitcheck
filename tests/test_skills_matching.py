import csv

import config
from core.matching import compute_match, explain_score_change, score_band
from core.skills import extract_job_skills, extract_skills, find_context, normalize_skill
from tests.sample_files import CV_TEXT, JOB_TEXT


def test_extract_basic_and_aliases():
    found = extract_skills("I use ReactJS, Node.js, C++, C#, python3 and MS Excel. SQL Server and SQL.")
    for skill in ["React", "Node.js", "C++", "C#", "Python", "Excel", "SQL Server", "SQL"]:
        assert skill in found


def test_no_false_positives_inside_words():
    assert extract_skills("excellent javascripting cassandra") == []
    assert "Java" not in extract_skills("JavaScript developer")
    assert "SQL" not in extract_skills("MySQL and NoSQL")
    assert "MySQL" in extract_skills("MySQL and NoSQL") and "NoSQL" in extract_skills("MySQL and NoSQL")


def test_case_sensitive_acronym():
    assert "Machine Learning" in extract_skills("worked on ML models")
    assert "Machine Learning" not in extract_skills("the html file")


def test_importance_required_vs_preferred():
    skills = extract_job_skills(JOB_TEXT)
    assert skills["SQL"] == "required" and skills["Python"] == "required"
    assert skills["Docker"] == "preferred" and skills["Spark"] == "preferred"


def test_inline_plus_marks_preferred():
    assert extract_job_skills("Requirements:\n- Python\n- Docker is a plus")["Docker"] == "preferred"


def test_normalize_and_context():
    assert normalize_skill("power-bi") == "Power BI"
    assert "Power BI" in find_context(JOB_TEXT, "Power BI")


def test_synthetic_dataset_is_recovered_exactly():
    with open(config.SAMPLE_JOBS_CSV, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) >= 50
    for row in rows:
        expected = {**{s: "required" for s in row["required_skills"].split("|")},
                    **{s: "preferred" for s in row["preferred_skills"].split("|")}}
        assert extract_job_skills(row["description"]) == expected, row["job_id"]
        assert row["is_synthetic"] == "True" and "(synthetic)" in row["company"]


def test_match_score_formula_and_lists():
    job = extract_job_skills(JOB_TEXT)
    res = compute_match(CV_TEXT, JOB_TEXT, extract_skills(CV_TEXT), job, skill_weight=0.7, preferred_weight=0.5)
    assert set(res.matched) == {"Python", "Excel", "Communication"}
    assert "SQL" in res.missing_required and "Power BI" in res.missing_required
    assert set(res.missing_preferred) == {"Docker", "Spark"}
    assert "Pandas" in res.additional
    # weighted: required matched 3 of 7 (SQL,Python,Power BI,Tableau,Excel,Data Visualization,Statistics,Communication?)
    expected_skill = round(res.matched_weight / res.total_weight * 100, 1)
    assert res.skill_score == expected_skill
    assert res.final_score == round(0.7 * res.skill_score + 0.3 * res.text_similarity, 1)
    assert 0 <= res.final_score <= 100


def test_better_cv_scores_higher():
    job = extract_job_skills(JOB_TEXT)
    better = CV_TEXT + "\nTechnical: SQL, Power BI, Tableau, Statistics, Data Visualization, Docker, Spark"
    low = compute_match(CV_TEXT, JOB_TEXT, extract_skills(CV_TEXT), job)
    high = compute_match(better, JOB_TEXT, extract_skills(better), job)
    assert high.final_score > low.final_score and high.skill_score == 100.0


def test_weights_change_result_and_edge_cases():
    job = extract_job_skills(JOB_TEXT)
    a = compute_match(CV_TEXT, JOB_TEXT, extract_skills(CV_TEXT), job, skill_weight=1.0)
    assert a.final_score == a.skill_score
    empty = compute_match(CV_TEXT, "no known skills here at all", extract_skills(CV_TEXT), {})
    assert empty.skill_score == 0 and empty.notes
    assert compute_match("", JOB_TEXT, [], job).text_similarity == 0


def test_explain_and_band():
    old = {"final_score": 40.0, "skill_score": 30.0, "text_similarity": 60.0}
    new = {"final_score": 50.0, "skill_score": 45.0, "text_similarity": 61.0, "preferred_weight": 0.5,
           "job_skills": {"SQL": "required"}}
    lines = explain_score_change(old, new, "SQL")
    assert any("+10.0" in l for l in lines) and any("SQL" in l for l in lines)
    assert score_band(85) == "Strong match" and score_band(10) == "Low match"
