"""Generate the SYNTHETIC sample dataset used for development and demos.

    python scripts/generate_synthetic_data.py [--jobs-per-role 6] [--seed 42]

Outputs (all fictional, never real postings or companies):
    data/synthetic_jobs.csv    - sample job postings with required / preferred skills
    data/skill_mappings.csv    - skill -> category, aliases, co-occurring skills, demand in the sample
    data/README_DATA.md        - description of the data

The generator is deterministic for a given seed.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.taxonomy import TAXONOMY  # noqa: E402

COMPANIES = ["Northwind Analytics", "Bluebird Data Labs", "Crescent Cloud Systems", "Orchid Software House",
             "Falcon Insight Group", "Meridian Tech Partners", "Lotus Digital Works", "Summit Data Works",
             "Zenith Software Studio", "Harbor Analytics Co"]
LOCATIONS = ["Lahore, Pakistan", "Karachi, Pakistan", "Islamabad, Pakistan", "Riyadh, Saudi Arabia",
             "Jeddah, Saudi Arabia", "Remote", "Remote (EMEA)", "Dubai, UAE"]
TYPES = ["Full-time", "Full-time", "Contract", "Internship"]

ROLES = {
    "Data Analyst": {
        "summary": "Turn business data into clear insights for managers and product teams.",
        "tasks": ["Answer business questions with data and explain the findings in plain language.",
                  "Build weekly reports and keep numbers consistent across teams.",
                  "Work with stakeholders to define the metrics that matter."],
        "required": ["SQL", "Excel", "Python", "Power BI", "Tableau", "Statistics", "Data Visualization",
                     "Data Cleaning", "Pandas", "Data Analysis"],
        "preferred": ["Machine Learning", "Spark", "AWS", "Git", "Communication", "Looker"]},
    "Business Intelligence Analyst": {
        "summary": "Own the reporting layer that managers use to run the business.",
        "tasks": ["Design report layouts that executives can read in one minute.",
                  "Validate numbers against source systems before every release.",
                  "Gather reporting requirements from finance and operations."],
        "required": ["Power BI", "SQL", "Excel", "Data Modeling", "Data Warehousing", "Tableau", "ETL",
                     "Data Visualization", "Communication"],
        "preferred": ["Python", "Azure", "Snowflake", "Agile", "Statistics"]},
    "Data Engineer": {
        "summary": "Build reliable systems that move and prepare data for analysts and models.",
        "tasks": ["Keep data flowing on schedule and fix failures quickly.",
                  "Improve the speed and cost of existing jobs.",
                  "Document datasets so other teams can trust them."],
        "required": ["Python", "SQL", "ETL", "Airflow", "Spark", "Data Warehousing", "Git", "Docker",
                     "PostgreSQL", "Kafka"],
        "preferred": ["AWS", "Kubernetes", "Terraform", "Scala", "Databricks", "Snowflake"]},
    "Platform Data Engineer": {
        "summary": "Process very large datasets on distributed clusters.",
        "tasks": ["Tune long-running jobs that process terabytes of data.",
                  "Monitor cluster health and capacity.",
                  "Support analysts who query very large tables."],
        "required": ["Hadoop", "Spark", "Kafka", "Hive", "Python", "Scala", "SQL", "Linux", "Airflow"],
        "preferred": ["AWS", "Docker", "Kubernetes", "Flink", "Databricks", "Java"]},
    "Applied AI Engineer": {
        "summary": "Take predictive systems from notebook to production.",
        "tasks": ["Train, test and compare predictive approaches on real company data.",
                  "Work with engineers to ship reliable prediction services.",
                  "Monitor quality after launch and retrain when needed."],
        "required": ["Python", "Machine Learning", "Scikit-learn", "TensorFlow", "PyTorch", "Docker", "Git",
                     "MLOps", "Statistics", "Feature Engineering"],
        "preferred": ["Kubernetes", "AWS", "Spark", "NLP", "Computer Vision", "Airflow"]},
    "Data Scientist": {
        "summary": "Use data and experiments to guide product decisions.",
        "tasks": ["Frame vague business problems as measurable questions.",
                  "Run experiments and report results honestly, including uncertainty.",
                  "Present recommendations to non-technical audiences."],
        "required": ["Python", "Statistics", "Machine Learning", "Pandas", "SQL", "Data Visualization",
                     "Scikit-learn", "A/B Testing", "Communication"],
        "preferred": ["NLP", "Spark", "TensorFlow", "Tableau", "Git", "Deep Learning"]},
    "Backend Developer": {
        "summary": "Build and maintain backend services for a growing product.",
        "tasks": ["Write clean, readable and well-reviewed code.",
                  "Fix bugs reported by users and improve performance.",
                  "Take part in design discussions and code reviews."],
        "required": ["Python", "Django", "Flask", "FastAPI", "REST API", "PostgreSQL", "Git", "Docker",
                     "Unit Testing", "Linux"],
        "preferred": ["AWS", "Redis", "CI/CD", "Kubernetes", "MongoDB", "Teamwork"]},
    "Full Stack Developer": {
        "summary": "Deliver features from the database to the browser.",
        "tasks": ["Turn product designs into working screens.",
                  "Keep the application fast, secure and easy to maintain.",
                  "Review teammates' code and share knowledge."],
        "required": ["JavaScript", "React", "Node.js", "HTML", "CSS", "MongoDB", "REST API", "Git",
                     "TypeScript", "SQL"],
        "preferred": ["Docker", "AWS", "Next.js", "Tailwind CSS", "CI/CD", "Agile"]},
    "DevOps Engineer": {
        "summary": "Make software delivery fast, safe and repeatable.",
        "tasks": ["Be on call for production incidents on a rotating schedule.",
                  "Reduce the time between a code change and a safe release.",
                  "Write runbooks so incidents are solved faster."],
        "required": ["Docker", "Kubernetes", "CI/CD", "Linux", "AWS", "Terraform", "Git", "Bash", "Python"],
        "preferred": ["Azure", "GCP", "GitHub", "Redis", "Elasticsearch", "Problem Solving"]},
    "Frontend Developer": {
        "summary": "Create fast, accessible and good-looking user interfaces.",
        "tasks": ["Build reusable interface components.",
                  "Make pages work well on phones and small laptops.",
                  "Measure and improve page speed."],
        "required": ["HTML", "CSS", "JavaScript", "React", "TypeScript", "Tailwind CSS", "Git", "REST API"],
        "preferred": ["Next.js", "Vue", "Angular", "Unit Testing", "Agile", "Communication"]},
}

REQ_TEMPLATES = ["Strong working knowledge of {s}", "Hands-on experience with {s}", "Proficiency in {s}",
                 "Practical experience using {s} on real projects", "Solid understanding of {s}"]
PREF_TEMPLATES = ["{s} is a plus.", "Experience with {s} is a plus.", "Familiarity with {s} is an advantage."]


def build_jobs(jobs_per_role: int, rng: random.Random) -> list[dict]:
    rows, job_no = [], 1
    for title, spec in ROLES.items():
        for _ in range(jobs_per_role):
            n_req = rng.randint(min(5, len(spec["required"])), min(8, len(spec["required"])))
            required = rng.sample(spec["required"], n_req)
            preferred = rng.sample(spec["preferred"], rng.randint(2, min(4, len(spec["preferred"]))))
            company = f"{rng.choice(COMPANIES)} (synthetic)"
            lines = [f"{title} at {company}", "", "About the role", spec["summary"], "", "Responsibilities:"]
            lines += [f"- {t}" for t in rng.sample(spec["tasks"], 2)]
            lines += ["", "Requirements:", "- Bachelor's degree in Computer Science, IT or a related field."]
            lines += [f"- {rng.choice(REQ_TEMPLATES).format(s=s)}." for s in required]
            lines += ["", "Nice to have:"]
            lines += [f"- {rng.choice(PREF_TEMPLATES).format(s=s)}" for s in preferred]
            rows.append({"job_id": f"SYN-{job_no:03d}", "title": title, "company": company,
                         "location": rng.choice(LOCATIONS), "employment_type": rng.choice(TYPES),
                         "description": "\n".join(lines), "required_skills": "|".join(required),
                         "preferred_skills": "|".join(preferred), "is_synthetic": "True"})
            job_no += 1
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jobs-per-role", type=int, default=6)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    args.out.mkdir(parents=True, exist_ok=True)

    jobs = build_jobs(args.jobs_per_role, rng)
    write_csv(args.out / "synthetic_jobs.csv", jobs,
              ["job_id", "title", "company", "location", "employment_type", "description",
               "required_skills", "preferred_skills", "is_synthetic"])

    demand, together = Counter(), {}
    for job in jobs:
        skills = job["required_skills"].split("|")
        demand.update(skills)
        for s in skills:
            together.setdefault(s, Counter()).update([o for o in skills if o != s])
    mappings = []
    for name, category, aliases in TAXONOMY:
        related = "|".join(k for k, _ in together.get(name, Counter()).most_common(5))
        mappings.append({"skill": name, "category": category, "aliases": "|".join(a.lstrip("=") for a in aliases),
                         "co_occurring_skills": related, "sample_jobs_requiring": demand.get(name, 0)})
    write_csv(args.out / "skill_mappings.csv", mappings,
              ["skill", "category", "aliases", "co_occurring_skills", "sample_jobs_requiring"])

    (args.out / "README_DATA.md").write_text(
        "# Sample data (SYNTHETIC)\n\n"
        "All files in this folder were generated by `scripts/generate_synthetic_data.py` with a fixed random seed.\n"
        "Companies, job postings and numbers are **fictional** and exist only for development and demonstration.\n"
        "They are not real vacancies and must not be presented as real market data.\n\n"
        "- `synthetic_jobs.csv`: sample job postings (one row per job; skills separated by `|`).\n"
        "- `skill_mappings.csv`: skill taxonomy with aliases and how often each skill appears in the synthetic jobs.\n\n"
        "FitCheck does not need any real resume dataset: users upload their own resume.\n", encoding="utf-8")
    print(f"Wrote {len(jobs)} synthetic jobs and {len(mappings)} skill mappings to {args.out}")


if __name__ == "__main__":
    main()
