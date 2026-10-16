"""Skill Gap Analysis."""
import csv
from functools import lru_cache

import pandas as pd
import streamlit as st

import config
from core import learning_content as lc
from core.matching import category_counts
from core.onet import recommend_occupations
from core.skills import skill_category
from ui import charts, state, theme


@lru_cache(maxsize=1)
def _demand() -> dict[str, int]:
    try:
        with open(config.SKILL_MAPPINGS_CSV, newline="", encoding="utf-8") as fh:
            return {r["skill"]: int(r["sample_jobs_requiring"]) for r in csv.DictReader(fh)}
    except (OSError, ValueError):
        return {}


def _open_learning(skill: str) -> None:
    st.session_state["learn_skill"] = skill
    st.session_state["cv_flow"] = None
    theme.go("Personalized Learning Center")


def _ask_ai_skill(skill: str) -> None:
    prompt = f"How should I learn and demonstrate {skill} for this job? What interview questions might they ask?"
    if "chat_history" not in st.session_state or not st.session_state["chat_history"]:
        st.session_state["chat_history"] = []
    st.session_state["chat_history"].append({"role": "user", "content": prompt})
    theme.go("AI Skill Assistant")


def render() -> None:
    theme.hero(
        "Skill Gap Analysis",
        "What the job asks for, what your CV already shows, and what is missing.",
        badge_text="NetSol Enterprise Gap Matrix",
    )
    ctx = state.current()
    if not ctx:
        theme.empty_state("No analysis yet", "Run an analysis to see your skill gaps.", "Go to Resume & Job Analysis",
                          "Resume & Job Analysis", key="gap_empty")
        return
    match, resume, job = ctx
    d = match.details
    with st.expander("Occupation context from O*NET 31.0"):
        st.caption(
            "Advisory context based on occupation descriptions/tasks; it does not change your match score "
            "or prove that a skill is required for this specific job."
        )
        occupation_matches = recommend_occupations(job.text)
        if not occupation_matches:
            st.info(
                "O*NET profiles are not imported into the app database yet. "
                "Run `python scripts/import_onet_reference.py` after MinIO is configured."
            )
        for profile in occupation_matches:
            st.markdown(
                f"**{profile['title']}** — O*NET {profile['onet_code']} · "
                f"{profile['similarity']}% text similarity"
            )
            if profile["description"]:
                st.caption(profile["description"])
            if profile["essential_skills"]:
                skills = ", ".join(
                    f"{item['name']} ({item['importance']:g}/5)"
                    for item in profile["essential_skills"]
                )
                st.write(f"**Common essential skills:** {skills}")
            if profile["transferable_skills"]:
                skills = ", ".join(
                    f"{item['name']} ({item['importance']:g}/5)"
                    for item in profile["transferable_skills"]
                )
                st.write(f"**Transferable skills:** {skills}")
            software = [
                item["name"] + (" (in demand)" if item["in_demand"] else " (hot technology)" if item["hot"] else "")
                for item in profile["software_skills"]
            ]
            if software:
                st.write(f"**Related software examples:** {', '.join(software)}")
    theme.kpi_row([("Matched", len(d["matched"]), "skills found in both", "good"),
                   ("Missing required", len(d["missing_required"]), "highest priority", "bad" if d["missing_required"] else "good"),
                   ("Missing preferred", len(d["missing_preferred"]), "nice to have", "warn" if d["missing_preferred"] else "good"),
                   ("Additional", len(d["additional"]), "in CV, not in job", "indigo")])
    st.write("")
    if not d["job_skills"]:
        st.warning("No known skills were detected in the job description. Check the text on the analysis page.")
    else:
        counts = category_counts(d["job_skills"], d["matched"])
        st.plotly_chart(charts.required_vs_matched(counts), width="stretch")

    t1, t2, t3, t4 = st.tabs(["Matched", "Missing required", "Missing preferred", "Additional in CV"])
    with t1:
        st.markdown(theme.chips(d["matched"], "good"), unsafe_allow_html=True)
        if not d["matched"]:
            st.info("None of the job's skills were found in your CV yet.")
    with t4:
        st.markdown(theme.chips(d["additional"], "info"), unsafe_allow_html=True)
        st.caption("Extra skills in your CV that this job does not mention. They may still help for other roles.")

    demand = _demand()
    for tab, key, label in ((t2, "missing_required", "required"), (t3, "missing_preferred", "preferred")):
        with tab:
            skills = d[key]
            if not skills:
                st.success(f"No missing {label} skills.")
                continue
            rows = [{"Skill": s, "Category": skill_category(s), "Importance": label,
                     "Sample jobs requiring it": demand.get(s, 0) or "-",
                     "Lesson": "Full lesson" if lc.has_curated(s) else "Starter path"} for s in skills]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
            st.caption("'Sample jobs requiring it' counts the fictional synthetic sample jobs shipped with FitCheck (60 jobs).")
            for skill in skills:
                with st.expander(f"Why {skill} matters for this job"):
                    st.markdown(lc.why_it_matters(skill, label, job.title, job.text))
                    b1, b2 = st.columns(2)
                    b1.button(f"Learn {skill}", key=f"gap_learn_{key}_{skill}", on_click=_open_learning, args=(skill,),
                              type="primary", width="stretch")
                    b2.button(f"Ask AI Coach about {skill}", key=f"gap_ai_{key}_{skill}", on_click=_ask_ai_skill,
                              args=(skill,), width="stretch")
