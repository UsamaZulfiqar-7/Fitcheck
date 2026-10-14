"""Personalized Learning Center: lessons, practice, resources, progress and the Add-to-CV flow."""
from __future__ import annotations

import streamlit as st

from core import ai, cv_builder, pipeline, repository as repo
from core import learning_content as lc
from core.skills import skill_category
from ui import state, theme

ADD_BUTTON = "I've Learned This Skill — Add to My CV"
NEW_SECTION = "Create a new section..."


# ---- callbacks (run before the next script run, so state is current on rerun) ------------------------
def _toggle(cand: int, skill: str, module_id: int, key: str) -> None:
    repo.set_topic_completed(cand, skill, module_id, bool(st.session_state[key]))


def _start(cand: int, skill: str) -> None:
    repo.start_path(cand, skill)


def _complete_path(cand: int, skill: str) -> None:
    repo.mark_path_completed(cand, skill)


def _open_cv_flow(skill: str) -> None:
    st.session_state["cv_flow"] = skill
    st.session_state["cv_last_change"] = None


def _cancel_cv_flow() -> None:
    st.session_state["cv_flow"] = None


def _confirm_add(cand: int, resume_id: int, job_id: int, skill: str, wording: str, section: str) -> None:
    try:
        change = pipeline.add_skill_to_cv(cand, resume_id, job_id, skill, wording, section, state.settings())
    except ValueError as exc:
        st.session_state["cv_error"] = str(exc)
        return
    except Exception as exc:
        st.session_state["cv_error"] = f"Could not update the CV ({type(exc).__name__}: {exc})."
        return
    st.session_state.update(cv_error=None, cv_last_change=change, cv_flow=None, match_id=change["match_id"])


# ---- page ------------------------------------------------------------------------------------------------
def render() -> None:
    theme.hero("Personalized Learning Center",
               "Learn each missing skill inside FitCheck: lessons, worked examples, practice questions and free resources.")
    ctx = state.current()
    cand = st.session_state["cand_id"]
    if not ctx:
        theme.empty_state("No analysis yet", "Run an analysis to get a personalised learning plan.",
                          "Go to Resume & Job Analysis", "Resume & Job Analysis", key="learn_empty")
        return
    match, resume, job = ctx
    d = match.details
    missing = d["missing_required"] + d["missing_preferred"]
    started = [p["skill"] for p in repo.progress_summary(cand) if p["skill"] not in missing]
    options = missing + started
    if not options:
        st.success("You have no missing skills for this job. Nothing to learn right now.")
        return
    if st.session_state.get("learn_skill") not in options:
        st.session_state["learn_skill"] = options[0]

    def label(skill: str) -> str:
        importance = d["job_skills"].get(skill)
        tag = {"required": "required", "preferred": "preferred"}.get(importance, "already in CV / learned")
        return f"{skill}  ({tag})"

    skill = st.selectbox("Choose a skill to learn", options, key="learn_skill", format_func=label)
    importance = d["job_skills"].get(skill)
    category = skill_category(skill)
    path = lc.get_learning_path(skill, category)
    modules = repo.ensure_modules(skill, category, path["stages"])
    ids = {m["id"] for m in modules}
    done_ids = repo.completed_module_ids(cand, skill) & ids
    total, n_done = len(modules), len(done_ids)
    db_path = repo.get_path(cand, skill)
    next_module = next((m for m in modules if m["id"] not in done_ids), None)

    # header card
    badges = theme.badge(path["level"]) + theme.badge(category)
    if importance:
        badges += theme.badge(f"{importance} for this job")
    badges += theme.badge("full lesson" if path["curated"] else "starter path")
    theme.card(f"<h4 style='margin-bottom:.2rem'>{skill}</h4>{badges}")
    st.progress(n_done / total if total else 0.0, text=f"{n_done} of {total} topics completed")

    if db_path is None:
        st.button("Start learning this skill", type="primary", key=f"start_{skill}", on_click=_start, args=(cand, skill))
    elif db_path["status"] == "completed":
        st.success("You marked this learning path as completed.")
    elif next_module:
        last = next((m for m in modules if m["id"] == db_path["last_module_id"]), None)
        st.info(f"Resume here: **{next_module['title']}** ({next_module['stage_title']})"
                + (f"  \nLast completed: {last['title']}" if last else ""))

    tabs = st.tabs(["Overview", "Roadmap & lessons", "Practice questions", "Free resources", "Finish & add to CV"])

    # ---- overview ---------------------------------------------------------------------------------------------
    with tabs[0]:
        st.markdown("#### What is it?")
        st.write(path["overview"])
        st.markdown("#### Why it matters for this job")
        if importance:
            st.markdown(lc.why_it_matters(skill, importance, job.title, job.text))
        else:
            st.write(path["why"])
        st.markdown("#### What you should know first")
        for item in path["prerequisites"]:
            st.markdown(f"- {item}")
        st.markdown(f"#### Level: **{path['level']}**")
        st.markdown("#### Your roadmap at a glance")
        for i, stage in enumerate(path["stages"], start=1):
            st.markdown(f"{i}. **{stage['title'].split(': ', 1)[-1]}**: " + ", ".join(t["title"] for t in stage["topics"]))
        if not path["curated"]:
            st.warning("This skill does not have a fully written lesson yet - this is a structured starter path. "
                       "Enable the optional AI helper in Settings for detailed personalised notes.")
        st.markdown("#### Optional: personalised AI notes")
        if ai.available():
            if st.button("Generate AI notes for me", key=f"ai_{skill}"):
                with st.spinner("Writing notes..."):
                    try:
                        st.session_state["ai_notes"][skill] = ai.personalised_notes(skill, job.title, job.text, resume.reviewed_text)
                    except Exception as exc:
                        st.error(f"AI notes are not available right now ({type(exc).__name__}). The built-in lessons still work.")
            if st.session_state["ai_notes"].get(skill):
                st.markdown(st.session_state["ai_notes"][skill])
        else:
            st.caption("Not configured. FitCheck works fully without it; add ANTHROPIC_API_KEY to .env to enable.")

    # ---- roadmap & lessons --------------------------------------------------------------------------------
    with tabs[1]:
        by_key = {m["key"]: m for m in modules}
        for stage_no, stage in enumerate(path["stages"], start=1):
            keys = [t["key"] for t in stage["topics"]]
            has_next = next_module is not None and next_module["key"] in keys
            stage_done = sum(1 for k in keys if by_key[k]["id"] in done_ids)
            with st.expander(f"{stage['title']}  -  {stage_done}/{len(keys)} done", expanded=has_next or (next_module is None and stage_no == 1)):
                for topic in stage["topics"]:
                    mod = by_key[topic["key"]]
                    st.markdown(f"#### {topic['title']}")
                    st.markdown(topic["content"])
                    ckey = f"done_{cand}_{skill}_{mod['id']}"
                    st.checkbox("Mark this topic as completed", value=mod["id"] in done_ids, key=ckey,
                                on_change=_toggle, args=(cand, skill, mod["id"], ckey))
                    st.divider()

    # ---- practice ---------------------------------------------------------------------------------------------------
    with tabs[2]:
        st.caption("Practice questions are for learning only - there is no score or certificate. Try first, then reveal the solution.")
        for i, q in enumerate(path["practice"], start=1):
            st.markdown(f"**Q{i}. {q['q']}**")
            st.text_area("Your answer (not saved)", key=f"ans_{skill}_{i}", height=90, label_visibility="collapsed",
                         placeholder="Write your answer or code here...")
            with st.expander("💡 Hint"):
                st.write(q["hint"])
            with st.expander("✅ Show sample solution and explanation"):
                st.markdown(q["solution"])
            st.divider()

    # ---- resources ----------------------------------------------------------------------------------------------------------
    with tabs[3]:
        st.caption("Optional external links (free to open; internet needed only for these). Official documentation first.")
        for r in path["resources"]:
            st.markdown(f"- [{r['title']}]({r['url']})  `{r['kind']}`")
        if not path["curated"]:
            st.caption("Search links open a web search, not a specific course. Pick official docs or well-known free sources.")

    # ---- finish & add to CV ---------------------------------------------------------------------------------------------
    with tabs[4]:
        completed = bool(db_path and db_path["status"] == "completed")
        remaining = [m for m in modules if m["id"] not in done_ids]
        if remaining:
            st.markdown(f"**{len(remaining)} topic(s) still to do:** " + ", ".join(m["title"] for m in remaining))
        elif not completed:
            st.success("All topics are done. Mark the whole learning path as completed when you feel ready.")
        if not completed:
            st.button("Mark learning path as completed", key=f"complete_{skill}", on_click=_complete_path,
                      args=(cand, skill), disabled=bool(remaining), type="primary")
        st.divider()
        if skill not in d["missing_required"] + d["missing_preferred"]:
            st.info("This skill is already counted in your latest score (found in the job posting and your CV).")
        else:
            st.markdown("### Add this skill to your CV")
            st.caption("Only after you have really learned it. FitCheck never adds a skill automatically.")
            st.button(ADD_BUTTON, key=f"addcv_{skill}", on_click=_open_cv_flow, args=(skill,), type="primary",
                      disabled=not completed)
            if not completed:
                st.caption("Finish the topics and mark the path as completed to unlock this button.")
        if st.session_state.get("cv_flow") == skill:
            _cv_panel(cand, match, resume, skill)
        change = st.session_state.get("cv_last_change")
        if change and change["skill"] == skill:
            _show_change(change)


def _cv_panel(cand: int, match, resume, skill: str) -> None:
    sections = pipeline.current_cv_sections(resume.id)
    st.markdown(f"#### Add “{skill}” to your CV")
    st.markdown('<div class="notice">Add only skills you have <b>genuinely learned or possess</b>. Do not add experience, '
                'projects or qualifications you do not have - employers may test you on this.</div>', unsafe_allow_html=True)
    st.write("")
    confirmed = st.checkbox("I confirm that I have genuinely learned this skill and can explain or use it.",
                            key=f"confirm_{skill}")
    options = cv_builder.skills_section_options(sections) + [NEW_SECTION]
    section = st.selectbox("Where should it go in your CV?", options, key=f"section_{skill}")
    if section == NEW_SECTION:
        section = st.text_input("Name of the new section", value="Skills", key=f"newsec_{skill}").strip()
    wording = st.text_input("Skill wording (you can edit it)", value=skill, key=f"wording_{skill}").strip()

    duplicate = bool(wording) and cv_builder.skill_already_in_cv(sections, wording)
    if duplicate:
        st.warning(f"'{wording}' already appears in your CV, so it will not be added twice.")
    ready = bool(wording and section) and not duplicate
    if ready:
        after = cv_builder.add_skill(sections, wording, section)
        p1, p2 = st.columns(2)
        p1.markdown("**Before**")
        p1.code(cv_builder.section_preview(sections, section), language=None)
        p2.markdown("**After (preview)**")
        p2.code(cv_builder.section_preview(after, section), language=None)
        st.caption("Everything else in your CV stays unchanged. The original uploaded CV is never modified.")
    if st.session_state.get("cv_error"):
        st.error(st.session_state["cv_error"])
    b1, b2 = st.columns(2)
    b1.button("Confirm and add to my CV", type="primary", disabled=not (confirmed and ready), key=f"save_{skill}",
              on_click=_confirm_add, args=(cand, resume.id, match.job_id, skill, wording, section), width="stretch")
    b2.button("Cancel", key=f"cancel_{skill}", on_click=_cancel_cv_flow, width="stretch")
    if not confirmed:
        st.caption("Tick the confirmation box to enable the button.")


def _show_change(change: dict) -> None:
    st.success(f"'{change['skill']}' was added to the “{change['section']}” section (CV version {change['version_no']}).")
    c1, c2, c3 = st.columns(3)
    c1.metric("Old score", change["old_score"])
    c2.metric("New score", change["new_score"],
              delta=None if change["old_score"] is None else round(change["new_score"] - change["old_score"], 1))
    c3.metric("Skill match", change["new_skill"],
              delta=None if change["old_skill"] is None else round(change["new_skill"] - change["old_skill"], 1))
    for line in change["explanation"]:
        st.markdown(f"- {line}")
    st.button("Open Updated CV & Downloads", on_click=theme.go, args=("Updated CV & Downloads",), key="to_cv_page",
              type="primary")
