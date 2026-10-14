"""Resume & Job Analysis: upload, review text, run the pipeline."""
from __future__ import annotations

import csv
import hashlib

import streamlit as st

import config
from core import extraction, pipeline, repository as repo, storage
from core.extraction import ExtractionError
from ui import state, theme


@st.cache_data(show_spinner=False)
def sample_jobs() -> list[dict]:
    try:
        with open(config.SAMPLE_JOBS_CSV, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    except OSError:
        return []


def _guess_title(text: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if 3 <= len(line) <= 80:
            return line
    return ""


def _extract_into(kind: str, uploaded, allowed: list[str], text_key: str) -> None:
    """Extract once per distinct file and put the text in the editable text area."""
    data = uploaded.getvalue()
    digest = hashlib.md5(data).hexdigest()
    draft = st.session_state.get(f"{kind}_draft")
    if draft and draft["hash"] == digest:
        return
    try:
        with st.spinner("Reading the file..."):
            result = extraction.extract_text(data, uploaded.name, allowed)
    except ExtractionError as exc:
        st.session_state[f"{kind}_draft"] = None
        st.error(str(exc))
        return
    except Exception as exc:                                     # never show a stack trace to the user
        st.session_state[f"{kind}_draft"] = None
        st.error(f"Sorry, this file could not be processed ({type(exc).__name__}). Try another file or paste the text.")
        return
    st.session_state[f"{kind}_draft"] = {"hash": digest, "name": uploaded.name, "bytes": data, "method": result.method,
                                         "warnings": result.warnings, "text": result.text}
    st.session_state[text_key] = result.text
    if kind == "job" and not st.session_state.get("job_title_in"):
        st.session_state["job_title_in"] = _guess_title(result.text)


def _load_sample(index: int) -> None:
    job = sample_jobs()[index]
    st.session_state.update(job_text_area=job["description"], job_title_in=job["title"],
                            job_company_in=job["company"], job_draft=None, job_is_sample=True)


def _show_notes(kind: str) -> None:
    draft = st.session_state.get(f"{kind}_draft")
    if draft:
        st.caption(f"Extracted with: {draft['method']}  |  {len(draft['text'])} characters")
        for w in draft["warnings"]:
            st.warning(w)


def render() -> None:
    theme.hero("Resume & Job Analysis", "Upload your CV, add the job posting, review the extracted text, then run the analysis.")
    cand = st.session_state["cand_id"]

    def _on_load_prev() -> None:
        chosen_id = st.session_state.get("load_prev")
        if chosen_id:
            state.load_analysis(chosen_id)
            theme.go("Match Results")

    previous = repo.list_analyses(cand)
    if previous:
        with st.expander(f"Load a previous analysis ({len(previous)})"):
            labels = {p["match_id"]: f"{p['title']} - score {p['score']} - {p['filename']} - {p['created_at']:%d %b %Y %H:%M}"
                      for p in previous}
            st.selectbox("Saved analyses", list(labels), format_func=labels.get, key="load_prev")
            st.button("Load this analysis", on_click=_on_load_prev, key="load_prev_btn")

    # ---- step 1: CV ---------------------------------------------------------------------------------
    st.subheader("1. Your CV")
    st.caption(f"PDF, DOCX or TXT, up to {config.MAX_UPLOAD_MB} MB. Scanned PDFs use OCR.")
    resume_file = st.file_uploader("Upload CV", type=extraction.RESUME_TYPES, key="resume_upload",
                                   label_visibility="collapsed")
    if resume_file is not None:
        _extract_into("resume", resume_file, extraction.RESUME_TYPES, "resume_text_area")
        _show_notes("resume")
        st.text_area("Extracted CV text (you can correct mistakes)", key="resume_text_area", height=260)
    else:
        st.session_state["resume_draft"] = None
        st.info("Upload your CV to continue.")

    # ---- step 2: job ----------------------------------------------------------------------------------
    st.subheader("2. Job posting")
    mode = st.radio("How do you want to add the job?", ["Paste / type text", "Upload file (PDF, JPG, PNG, TXT)",
                                                         "Use a synthetic sample job"], horizontal=True, key="job_mode")
    source = "typed"
    if mode.startswith("Upload"):
        job_file = st.file_uploader("Upload job posting", type=extraction.JOB_TYPES, key="job_upload")
        if job_file is not None:
            _extract_into("job", job_file, extraction.JOB_TYPES, "job_text_area")
            _show_notes("job")
            source = extraction.file_extension(job_file.name)
            source = "image" if source in extraction.IMAGE_TYPES else source
        else:
            st.session_state["job_draft"] = None
    elif mode.startswith("Use"):
        jobs = sample_jobs()
        if jobs:
            idx = st.selectbox("Sample job (fictional)", range(len(jobs)), key="sample_idx",
                               format_func=lambda i: f"{jobs[i]['title']} - {jobs[i]['company']} - {jobs[i]['location']}")
            st.button("Load this sample", on_click=_load_sample, args=(idx,), key="load_sample")
            source = "sample"
        else:
            st.warning("The sample dataset is missing. Run: python scripts/generate_synthetic_data.py")
    c1, c2 = st.columns(2)
    c1.text_input("Job title", key="job_title_in", placeholder="e.g. Data Analyst")
    c2.text_input("Company (optional)", key="job_company_in")
    st.text_area("Job description text (review and edit)", key="job_text_area", height=240,
                 placeholder="Paste the job requirements here...")

    # ---- step 3: run -----------------------------------------------------------------------------------
    st.subheader("3. Analyse")
    resume_text = (st.session_state.get("resume_text_area") or "").strip() if resume_file is not None else ""
    job_text = (st.session_state.get("job_text_area") or "").strip()
    if st.button("Run analysis", type="primary", key="run_analysis"):
        if len(resume_text) < 50:
            st.error("Please upload a CV that contains readable text (at least a few lines).")
        elif len(job_text) < 30:
            st.error("Please add the job description (at least a few lines).")
        else:
            _run(cand, resume_file, resume_text, job_text, source)


def _run(cand: int, resume_file, resume_text: str, job_text: str, source: str) -> None:
    s = st.session_state
    with st.status("Running the FitCheck pipeline...", expanded=True) as status:
        try:
            st.write("1. Storing the original files")
            r_draft = s.get("resume_draft")
            sig = hashlib.md5((r_draft["hash"] + resume_text).encode()).hexdigest()
            if s.get("resume_sig") == sig and s.get("resume_id"):
                resume_id = s["resume_id"]
            else:
                raw = storage.save_raw(r_draft["bytes"], r_draft["name"], "resume")
                resume_id = repo.save_resume(cand, r_draft["name"], extraction.file_extension(r_draft["name"]),
                                             len(r_draft["bytes"]), raw, r_draft["method"], r_draft["text"], resume_text)
                s["resume_sig"] = sig
            j_draft = s.get("job_draft")
            raw_job = storage.save_raw(j_draft["bytes"], j_draft["name"], "job") if (j_draft and source not in ("typed", "sample")) else None
            st.write("2. Saving the reviewed text")
            job_id = repo.save_job(cand, s.get("job_title_in") or "Untitled job", s.get("job_company_in") or None,
                                   source, raw_job, job_text, is_synthetic=(source == "sample"))
            st.write("3. Extracting skills and calculating the match score")
            match_id, result = pipeline.analyze(cand, resume_id, job_id, state.settings())
            s.update(resume_id=resume_id, job_id=job_id, match_id=match_id, cv_flow=None, cv_last_change=None)
            status.update(label=f"Done - match score {result.final_score} / 100", state="complete")
        except Exception as exc:
            status.update(label="The analysis failed", state="error")
            st.error(f"Something went wrong while analysing ({type(exc).__name__}: {exc}). "
                     "Please check the files and try again.")
            return
    st.success(f"Analysis finished: {result.final_score} / 100.")
    st.button("See match results", on_click=theme.go, args=("Match Results",), type="primary", key="to_results")
