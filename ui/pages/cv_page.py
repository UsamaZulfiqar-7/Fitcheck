"""Updated CV & Downloads."""
import streamlit as st

from core import cv_builder, pipeline, repository as repo, storage
from core.report import build_report_pdf
from ui import state, theme


def _save_edit(cand: int, resume_id: int, job_id: int, key: str) -> None:
    text = st.session_state.get(key, "")
    if len(text.strip()) < 30:
        st.session_state["cv_edit_msg"] = ("error", "The CV text is too short to save.")
        return
    try:
        match_id, result = pipeline.save_edited_cv(cand, resume_id, job_id, text, state.settings())
        st.session_state.update(match_id=match_id, cv_edit_msg=("success", f"Saved as a new CV version. New score: {result.final_score}."))
    except Exception as exc:
        st.session_state["cv_edit_msg"] = ("error", f"Could not save ({type(exc).__name__}).")


def render() -> None:
    theme.hero("Updated CV & Downloads", "Compare your original CV with the updated version, fix wording, and download your files.")
    ctx = state.current()
    if not ctx:
        theme.empty_state("No analysis yet", "Run an analysis first.", "Go to Resume & Job Analysis",
                          "Resume & Job Analysis", key="cv_empty")
        return
    match, resume, job = ctx
    cand = match.candidate_id
    versions = repo.list_cv_versions(resume.id)
    latest = versions[-1] if versions else None
    base = pipeline.baseline_match(cand, resume.id, job.id)
    learned = repo.learned_skills(resume.id)

    theme.kpi_row([("Original CV score", base.final_score if base else "-", "before any update", "indigo"),
                   ("Current score", match.final_score, "latest CV version", theme.tone_for_score(match.final_score)),
                   ("Change", f"{match.final_score - base.final_score:+.1f}" if base else "-", "points", "good" if base and match.final_score > base.final_score else "indigo"),
                   ("CV versions", len(versions), "saved separately", "indigo")])
    st.write("")
    if resume.file_type == "docx":
        st.markdown('<div class="notice">Your CV is a Word file. Skills are added <b>inside your original document</b>, so fonts, '
                    'colours and layout stay the same. Download the DOCX to get the design.</div>', unsafe_allow_html=True)
    elif resume.file_type == "pdf":
        st.markdown('<div class="notice">Your original CV is a PDF. PDF design cannot be edited, so the updated CV is <b>rebuilt from '
                    'the extracted text</b> with a clean layout. Upload the Word (.docx) version to keep your design.</div>',
                    unsafe_allow_html=True)
        st.write("")
    if latest is None:
        st.info("You have not added any skill yet. Learn a missing skill, then use the “Add to My CV” button, or edit the text below.")

    current_text = latest.content_text if latest else cv_builder.cv_to_text(cv_builder.parse_cv(resume.reviewed_text))
    t1, t2, t3 = st.tabs(["Original vs updated", "Edit CV text", "Versions & downloads"])
    with t1:
        c1, c2 = st.columns(2)
        c1.markdown("**Original (as you reviewed it)**")
        c1.text_area("original", resume.reviewed_text, height=420, disabled=True, label_visibility="collapsed", key=f"orig_{resume.id}")
        c2.markdown(f"**Current version{f' (v{latest.version_no})' if latest else ''}**")
        c2.text_area("updated", current_text, height=420, disabled=True, label_visibility="collapsed",
                     key=f"cur_{resume.id}_{latest.id if latest else 0}")
    with t2:
        st.caption("Edit the text of the current version, then save it as a new version. The score is recalculated.")
        ekey = f"cv_edit_{resume.id}_{latest.id if latest else 0}"
        st.text_area("CV text", value=current_text, height=380, key=ekey)
        st.button("Save as new version", on_click=_save_edit, args=(cand, resume.id, job.id, ekey), type="primary", key="save_edit")
        msg = st.session_state.pop("cv_edit_msg", None)
        if msg:
            (st.success if msg[0] == "success" else st.error)(msg[1])
    with t3:
        if versions:
            rows = [{"Version": v.version_no, "Change": v.note or "-", "Skill added": v.added_skill or "-",
                     "Section": v.section_name or "-", "Created": v.created_at.strftime("%Y-%m-%d %H:%M")} for v in versions]
            st.dataframe(rows, hide_index=True, width="stretch")
        sections = cv_builder.sections_from_dicts(latest.content_json) if latest else cv_builder.parse_cv(resume.reviewed_text)
        label = f"v{latest.version_no}" if latest else "original text"
        d1, d2, d3 = st.columns(3)
        docx_data = (latest.docx_bytes if latest and latest.docx_bytes else cv_builder.to_docx(sections))
        d1.download_button(f"Updated CV (DOCX) - {label}", data=docx_data, file_name="updated_cv.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", width="stretch", key="dl_docx")
        d2.download_button(f"Updated CV (PDF) - {label}", data=cv_builder.to_pdf(sections), file_name="updated_cv.pdf",
                           mime="application/pdf", width="stretch", key="dl_pdf")
        report = build_report_pdf(st.session_state["cand_name"], job.title, job.company, match.details | {
            "skill_weight": match.skill_weight, "text_weight": match.text_weight, "preferred_weight": match.preferred_weight,
            "final_score": match.final_score, "skill_score": match.skill_score, "text_similarity": match.text_similarity},
            {"final_score": base.final_score} if base else None, learned, repo.progress_summary(cand))
        d3.download_button("Match report (PDF)", data=report, file_name="fitcheck_match_report.pdf", mime="application/pdf",
                           width="stretch", key="dl_report")
        raw = storage.read_raw(resume.raw_path)
        if raw:
            st.download_button(f"Original uploaded file ({resume.filename})", data=raw, file_name=resume.filename, key="dl_orig")
