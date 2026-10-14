"""Match Results."""
import streamlit as st

from core import pipeline, repository as repo
from core.matching import DISCLAIMER, formula_text, score_band
from ui import charts, state, theme


def render() -> None:
    theme.hero("Match Results", "How well your CV text covers the job posting - and why.")
    ctx = state.current()
    if not ctx:
        theme.empty_state("No analysis yet", "Upload a CV and a job posting first.", "Go to Resume & Job Analysis",
                          "Resume & Job Analysis", key="res_empty")
        return
    match, resume, job = ctx
    d = match.details
    st.markdown(f"**Job:** {job.title}{' - ' + job.company if job.company else ''}  |  **CV:** {resume.filename}"
                f"{'  |  *synthetic sample job*' if job.is_synthetic else ''}")

    base = pipeline.baseline_match(match.candidate_id, match.resume_id, match.job_id)
    delta_note = ""
    if base is not None and base.id != match.id:
        delta_note = f"original CV: {base.final_score} ({match.final_score - base.final_score:+.1f})"
    theme.kpi_row([
        ("Final score", match.final_score, delta_note or score_band(match.final_score), theme.tone_for_score(match.final_score)),
        ("Skill match", match.skill_score, f"weight {match.skill_weight:.0%}", "indigo"),
        ("Text similarity", match.text_similarity, f"weight {match.text_weight:.0%}", "indigo"),
        ("Matched skills", len(d["matched"]), f"of {len(d['job_skills'])} in the job", "good"),
        ("Missing required", len(d["missing_required"]), "skills to learn", "warn" if d["missing_required"] else "good"),
    ])
    st.write("")
    c1, c2 = st.columns(2)
    c1.plotly_chart(charts.gauge(match.final_score), width="stretch")
    c2.plotly_chart(charts.breakdown(match.skill_score, match.text_similarity, match.skill_weight, match.text_weight,
                                     match.final_score), width="stretch")

    st.subheader("How this score was calculated")
    theme.card(
        f"<b>{formula_text(d)}</b><br><br>"
        f"<b>Skill match</b> = weighted matched job skills / weighted total job skills = {d['matched_weight']:g} / {d['total_weight']:g} "
        f"(required skills weigh 1.0, preferred skills weigh {match.preferred_weight:g}).<br>"
        f"<b>Text similarity</b> = TF-IDF cosine similarity between CV and job text = {d['tfidf_similarity']}"
        f"{'' if d.get('semantic_similarity') is None else ' averaged with semantic similarity ' + str(d['semantic_similarity'])}.<br><br>"
        f"<span style='color:#64748B'>{DISCLAIMER}</span>")
    for note in d.get("notes", []):
        st.warning(note)

    history = [m for m in repo.list_matches(match.candidate_id, match.resume_id, match.job_id)]
    if len(history) > 1:
        versions = {v.id: v for v in repo.list_cv_versions(match.resume_id)}
        labels = []
        for m in history:
            v = versions.get(m.cv_version_id)
            labels.append("Original CV" if v is None else (f"+ {v.added_skill}" if v.added_skill else f"edit v{v.version_no}"))
        st.plotly_chart(charts.score_history(labels, [m.final_score for m in history]), width="stretch")

    st.button("See the skill gaps", on_click=theme.go, args=("Skill Gap Analysis",), type="primary", key="res_gaps")
