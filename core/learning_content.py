"""Learning content access layer.

* 12 skills have fully written, skill-specific lessons (core/content/*.py).
* Every other skill gets a category-specific starter path (clearly marked as such).
* If an AI key is configured, extra personalised notes can be generated on demand (core/ai.py).
"""
from __future__ import annotations

from urllib.parse import quote_plus

from core.content import _base
from core.content import big_data, data_skills, ml_tools, programming  # noqa: F401  (registers lessons)
from core.skills import CATEGORY_OF, find_context
from core.taxonomy import BIG, CLOUD, DATA, DB, ML, PROG, SOFT, TOOLS, WEB

CURATED = _base.CURATED


def has_curated(skill: str) -> bool:
    return skill.lower() in CURATED


def curated_skills() -> list[str]:
    return sorted(v["skill"] for v in CURATED.values())


# ---- category based starter paths for skills without a full lesson ---------------------------------
def _fallback(skill: str, category: str) -> dict:
    s = skill
    soft = category == SOFT
    kind = {PROG: "programming language", DB: "database technology", DATA: "data/analytics tool or method",
            BIG: "big data technology", ML: "machine learning topic", CLOUD: "cloud/DevOps tool",
            WEB: "web technology", TOOLS: "professional practice", SOFT: "professional skill"}.get(category, "skill")

    if soft:
        stages = [
            ("Stage 1: Understand the skill", [("understand", f"What {s} means at work",
                f"**{s}** is judged by behaviour, not by tools. Write down 3 situations in your target job where {s} matters "
                "(for example a stand-up meeting, a code/report review, a deadline conflict).\n\n"
                "Then list what *good* looks like in each situation: what would a strong colleague say or do?")]),
            ("Stage 2: Learn the techniques", [("techniques", f"Core techniques for {s}",
                f"Pick two proven techniques for {s} and study them. Examples: the *STAR* method (Situation, Task, Action, "
                "Result) for describing your work, the *pyramid principle* (answer first, details after) for clear writing, "
                "and active listening (paraphrase before you reply).")]),
            ("Stage 3: See real examples", [("examples", f"Study examples of {s}",
                f"Find 3 real examples (a well written project README, a recorded talk, a clear status email). For each one "
                f"note what makes it strong and how it shows {s}.")]),
            ("Stage 4: Practise", [("practise", f"Practise {s} this week",
                f"Do one small real task that needs {s}: present your last project in 3 minutes, write a one-page summary of a "
                "dataset for a non-technical reader, or lead a short study-group session. Ask one person for honest feedback.")]),
            ("Stage 5: Reflect and revise", [("reflect", "Reflect and prepare interview stories",
                f"Write two short STAR stories that show {s}. Keep real details only; never invent experience. "
                "Review them after a week and improve them with the feedback you received.")]),
        ]
        practice = [
            _base.Q(f"Describe a real situation where you showed {s}. Use the STAR structure.",
                    "Situation -> Task -> Action -> Result. Keep each part to 1-2 sentences.",
                    "A good answer names a concrete project, your own action (not 'we'), and a measurable or visible result."),
            _base.Q(f"What would you do if a teammate disagreed with you about a technical decision? (shows {s})",
                    "Listen first, restate their point, compare using facts.",
                    "Restate their view, ask for their reasoning, compare options against the goal (cost, time, risk), "
                    "agree on a small test or decision rule, and document the outcome."),
            _base.Q(f"How will you keep improving {s} after this course?", "Name one habit and one way to measure progress.",
                    "For example: a weekly 20-minute reflection note plus feedback from a mentor every month."),
        ]
    else:
        stages = [
            ("Stage 1: Fundamentals", [("fundamentals", f"What {s} is and how to set it up",
                f"Read the official introduction or 'Getting started' page of **{s}** (a {kind}). Write 5 lines in your own words: "
                f"what problem does {s} solve, who uses it, and what are its main parts? Install or open the tool and run the "
                "simplest possible example (a 'hello world').")]),
            ("Stage 2: Core concepts", [("core", f"Core concepts of {s}",
                f"List the 5-8 concepts that every beginner meets first in {s} (the official table of contents is a good guide). "
                "Study one concept per day: read it, run one example, and change the example to see what breaks.")]),
            ("Stage 3: Practical examples", [("examples", f"Worked examples with {s}",
                f"Follow a free step-by-step tutorial that builds something small with {s}. Re-type the code instead of "
                "copy-pasting, and write a comment above each step that explains why it is there.")]),
            ("Stage 4: Hands-on exercises", [("hands-on", f"Mini project using {s}",
                f"Build a mini project related to your target job that uses {s} (for example a small dashboard, pipeline, script "
                "or API). Keep it under one weekend, store it in a Git repository and write a short README.")]),
            ("Stage 5: Revision and self-assessment", [("revision", "Revise and self-check",
                f"Without looking at notes, explain {s} to a friend in 3 minutes, then list the concepts you could not explain. "
                "Revise those, and note common errors you made so you can avoid them in interviews and at work.")]),
        ]
        practice = [
            _base.Q(f"In your own words, what problem does {s} solve and when would you NOT use it?",
                    "Think about alternatives you already know.",
                    f"A good answer states the main purpose of {s}, one typical use case, and one situation where a simpler or "
                    "different tool is better."),
            _base.Q(f"Build the smallest working example of {s} you can and describe each step.",
                    "Start from the official 'getting started' page.",
                    "Your example should run end-to-end, and each step should be explained (what it does and why)."),
            _base.Q(f"List three mistakes beginners make with {s} and how to avoid them.",
                    "Search the official docs' FAQ / troubleshooting page.",
                    "Use real errors you met while practising; for each one write the cause and the fix."),
        ]

    q = quote_plus(skill)
    resources = [
        _base.R(f"Search: {skill} official documentation", f"https://www.google.com/search?q={q}+official+documentation", "search"),
        _base.R(f"Search: {skill} free beginner tutorial", f"https://www.google.com/search?q={q}+beginner+tutorial+free", "search"),
        _base.R("freeCodeCamp (free courses and articles)", "https://www.freecodecamp.org/", "tutorial"),
    ]
    overview = (f"{s} is a {kind}. FitCheck does not have a fully written lesson for it yet, so this is a structured "
                f"starter path with {len(stages)} stages. Turn on the optional AI helper in Settings to get detailed, "
                f"personalised notes for {s}.")
    why = f"{s} is mentioned in the job posting, so employers expect at least working knowledge of it."
    stages_out = []
    for title, topics in stages:
        stages_out.append({"title": title, "topics": [
            _base.T(f"{k}", t, c) for k, t, c in topics]})
    return {"skill": s, "level": "Beginner", "overview": overview, "why": why,
            "prerequisites": ["Basic computer skills"], "stages": stages_out, "practice": practice,
            "resources": resources, "curated": False}


def get_learning_path(skill: str, category: str | None = None) -> dict:
    """Return the learning path dict for a skill (curated lessons when available)."""
    path = CURATED.get(skill.lower())
    if path is not None:
        return path
    return _fallback(skill, category or CATEGORY_OF.get(skill.lower(), "Other"))


def why_it_matters(skill: str, importance: str, job_title: str, job_text: str) -> str:
    """Explain why a missing skill matters for THIS job, quoting the job text when possible."""
    path = get_learning_path(skill)
    context = find_context(job_text, skill)
    first = (f"**{skill}** is a **{importance}** skill for *{job_title}*."
             if importance == "required" else f"**{skill}** is a **preferred** (nice to have) skill for *{job_title}*.")
    parts = [first, path["why"]]
    if context:
        parts.append(f"The job posting says: “{context}”")
    return " ".join(parts)


def total_topics(path: dict) -> int:
    return sum(len(stage["topics"]) for stage in path["stages"])
