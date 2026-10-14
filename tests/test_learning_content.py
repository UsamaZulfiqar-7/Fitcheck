import pytest

from core import learning_content as lc
from core.taxonomy import TAXONOMY

REQUIRED_CURATED = ["SQL", "Python", "Excel", "Power BI", "Hadoop", "Spark", "Kafka", "Pandas", "Statistics",
                    "Machine Learning", "Git", "Docker"]


@pytest.mark.parametrize("skill", REQUIRED_CURATED)
def test_curated_paths_are_complete(skill):
    p = lc.get_learning_path(skill)
    assert p["curated"] and len(p["stages"]) == 5
    keys = [t["key"] for s in p["stages"] for t in s["topics"]]
    assert len(keys) == len(set(keys)) >= 5
    for stage in p["stages"]:
        for topic in stage["topics"]:
            assert len(topic["content"]) > 150
    assert len(p["practice"]) >= 4 and all(q["hint"] and q["solution"] for q in p["practice"])
    assert p["resources"] and all(r["url"].startswith("https://") for r in p["resources"])
    assert p["prerequisites"] and p["level"] and p["why"]


def test_sql_and_python_have_examples_and_outputs():
    sql = " ".join(t["content"] for s in lc.get_learning_path("SQL")["stages"] for t in s["topics"])
    for word in ["SELECT", "WHERE", "ORDER BY", "GROUP BY", "HAVING", "JOIN", "Result"]:
        assert word in sql
    py = " ".join(t["content"] for s in lc.get_learning_path("Python")["stages"] for t in s["topics"])
    assert "def " in py and "print(" in py and "# {'a': 3" in py


def test_every_taxonomy_skill_gets_a_path_and_roadmaps_differ():
    seen = set()
    for name, cat, _ in TAXONOMY:
        p = lc.get_learning_path(name, cat)
        assert len(p["stages"]) == 5 and p["practice"] and p["resources"]
        seen.add(p["stages"][1]["topics"][0]["content"][:60] if p["curated"] else None)
    assert len(seen) > 5
    soft = lc.get_learning_path("Communication")
    prog = lc.get_learning_path("Scala")
    assert soft["stages"][0]["title"] != prog["stages"][0]["title"]


def test_why_it_matters_uses_job_text():
    text = lc.why_it_matters("SQL", "required", "Data Analyst", "Requirements:\n- Strong SQL skills")
    assert "required" in text and "Strong SQL skills" in text


def test_python_code_samples_in_lessons_compile():
    """Every ```python block that is a self-contained snippet should at least be valid syntax."""
    import re
    bad = []
    for skill in ["Python", "Pandas", "Statistics", "Machine Learning", "Spark", "Kafka", "Hadoop"]:
        p = lc.get_learning_path(skill)
        blocks = []
        for s in p["stages"]:
            for t in s["topics"]:
                blocks += re.findall(r"```python\n(.*?)```", t["content"], re.S)
        for q in p["practice"]:
            blocks += re.findall(r"```python\n(.*?)```", q["solution"], re.S)
        for b in blocks:
            try:
                compile(b, f"<{skill}>", "exec")
            except SyntaxError as exc:
                bad.append((skill, str(exc), b[:60]))
    assert not bad, bad
