"""Home Dashboard."""
import streamlit as st

import config
from core import repository as repo
from core.matching import DISCLAIMER
from ui import state, theme

STEPS = [
    ("Upload your CV and a job posting", "PDF/DOCX/TXT for the CV; text, PDF, image or TXT for the job."),
    ("Review the extracted text", "Fix any extraction mistakes before analysis."),
    ("See your match score and skill gaps", "Matched, missing (required / preferred) and additional skills."),
    ("Learn the missing skills inside FitCheck", "Lessons, examples, practice questions and free resources."),
    ("Add a skill you really learned to your CV", "Explicit confirmation, preview, then a new CV version and updated score."),
]


def render() -> None:
    theme.hero(
        "Close the gap between your CV and the job",
        "FitCheck compares your resume with a job posting, shows exactly which skills are missing, teaches you those "
        "skills step by step, and updates your CV only after you confirm that you learned them.",
        badge_text="NetSol Presentation Edition",
    )
    ctx = state.current()
    cand = st.session_state["cand_id"]
    status = state.workflow_status()

    if ctx:
        match, resume, job = ctx
        d = match.details
        learned = repo.learned_skills(resume.id)
        theme.kpi_row([
            ("Current match score", f"{match.final_score}", "out of 100 (estimate)", theme.tone_for_score(match.final_score)),
            ("Missing required skills", len(d["missing_required"]), f"for {job.title}", "warn" if d["missing_required"] else "good"),
            ("Learning paths started", len(repo.progress_summary(cand)), "saved in the database", "indigo"),
            ("Skills added to CV", len(learned), "confirmed by you", "indigo"),
        ])
    else:
        theme.kpi_row([("Current match score", "-", "no analysis yet", "indigo"),
                       ("Missing required skills", "-", "run an analysis", "indigo"),
                       ("Learning paths started", len(repo.progress_summary(cand)) if cand else 0, "saved in the database", "indigo"),
                       ("Skills added to CV", "-", "after you confirm", "indigo")])

    st.write("")
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("How it works")
        html = ""
        for i, (title, desc) in enumerate(STEPS, start=1):
            done = [flag for _, flag in status][i - 1]
            html += (f'<div class="step {"done" if done else ""}"><div class="num">{"✓" if done else i}</div>'
                     f'<div><div class="t">{title}</div><div class="d">{desc}</div></div></div>')
        theme.card(html)
        if ctx:
            c1, c2, c3 = st.columns(3)
            c1.button("Start new analysis", type="primary", on_click=theme.go, args=("Resume & Job Analysis",),
                      width="stretch", key="home_start")
            c2.button("🤖 AI Assistant", on_click=theme.go, args=("AI Skill Assistant",),
                      width="stretch", key="home_chat")
            c3.button("Learning Center", on_click=theme.go, args=("Personalized Learning Center",),
                      width="stretch", key="home_learn")
        else:
            c1, _ = st.columns([1, 1])
            c1.button("Start analysis", type="primary", on_click=theme.go, args=("Resume & Job Analysis",),
                      width="stretch", key="home_start")
    with right:
        st.subheader("Scoring in one minute")
        theme.card(
            "<b>Final score</b> = <b>70%</b> skill match + <b>30%</b> text similarity (weights can be changed in Settings).<br><br>"
            "<b>Skill match</b>: required skills count 1.0, preferred skills 0.5.<br>"
            "<b>Text similarity</b>: TF-IDF cosine similarity between CV and job text.<br><br>"
            f"<span style='color:#64748B;font-size:.85rem'>{DISCLAIMER}</span>")
        theme.card(f"<b>Profile:</b> {st.session_state['cand_name']}<br><b>Database:</b> see Settings<br>"
                   f"<b>Works offline:</b> yes - no AI key needed ({config.APP_NAME} uses curated lessons).")

    with st.expander("Data pipeline used by FitCheck"):
        st.markdown(
            "`Ingestion` -> `Raw file storage` -> `Text extraction` -> `Skill extraction & normalisation` -> `Match score` "
            "-> `Skill gap analysis` -> `Personalised learning` -> `Progress storage` -> `Updated CV` -> `Final score & report`\n\n"
            "It is a single-machine, modular Python pipeline (no distributed processing is claimed).")
