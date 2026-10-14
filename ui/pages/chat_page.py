"""AI Skill Gap & Career Assistant Page.

Provides an interactive chat interface for candidates to query their specific skill gaps,
get tailored interview questions, enterprise project architectures, and CV optimization advice.
"""
from __future__ import annotations

import streamlit as st

from core import chat
from ui import state, theme

DEFAULT_WELCOME = (
    "👋 Hello! I am your **FitCheck AI Technical Career Coach**.\n\n"
    "I have analyzed your resume against your target job posting. I can help you:\n"
    "- 🎯 **Prioritize which missing skills to learn first**\n"
    "- 💼 **Prepare for technical interview questions** on your gap areas\n"
    "- 🛠️ **Design hands-on enterprise projects** to prove your capabilities\n"
    "- ✍️ **Craft high-impact CV bullet points** using the Google XYZ formula\n"
    "- 🏢 **Tailor your technical pitch for NetSol Technologies**\n\n"
    "Select one of the quick prompts below or type any question to begin!"
)


def render() -> None:
    theme.hero(
        "AI Skill Gap & Career Assistant",
        "Interactive AI coaching tailored to your target job, skill gaps, interview preparation, and CV formulation.",
        badge_text="NetSol Enterprise AI",
    )

    ctx = state.current()
    if not ctx:
        theme.empty_state(
            "No Active Analysis",
            "Upload your CV and a job posting first so the AI assistant has full context about your profile and skill gaps.",
            "Start Analysis",
            "Resume & Job Analysis",
            key="chat_empty",
        )
        return

    match, resume, job = ctx
    d = match.details
    cand_name = st.session_state.get("cand_name") or "Candidate"

    # Context Bar
    missing_req = d.get("missing_required", [])
    missing_pref = d.get("missing_preferred", [])
    all_missing = missing_req + missing_pref

    # Compact KPI / Context summary
    cols = st.columns([3, 2, 2, 3])
    cols[0].markdown(f"**Target Role:** `{job.title}`")
    cols[1].markdown(f"**Company:** `{job.company or 'NetSol'}`")
    cols[2].markdown(f"**Score:** `{match.final_score}/100`")
    gaps_display = ", ".join(all_missing[:3]) if all_missing else "None! (All matched)"
    cols[3].markdown(f"**Top Gaps:** `{gaps_display}`")

    st.write("")

    # Initialize chat history
    if "chat_history" not in st.session_state or not st.session_state["chat_history"]:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": DEFAULT_WELCOME}
        ]

    # Quick prompt actions
    st.markdown("##### ⚡ Quick Prompt Suggestions:")
    p_cols = st.columns(4)
    quick_query = None

    if p_cols[0].button("🎯 Prioritize My Gaps", key="qp_priority", width="stretch"):
        quick_query = "Which missing skills should I prioritize learning first for this job and why?"
    if p_cols[1].button("💼 Interview Questions", key="qp_interview", width="stretch"):
        top_skill = missing_req[0] if missing_req else (all_missing[0] if all_missing else "System Design")
        quick_query = f"Give me 3 senior technical interview questions and answers for {top_skill}."
    if p_cols[2].button("🛠️ Enterprise Projects", key="qp_projects", width="stretch"):
        top_skill = missing_req[0] if missing_req else (all_missing[0] if all_missing else "Data Engineering")
        quick_query = f"Suggest an enterprise-level portfolio project for {top_skill} to showcase on my CV."
    if p_cols[3].button("🏢 NetSol Prep Strategy", key="qp_netsol", width="stretch"):
        quick_query = "How should I present my technical skills and architecture mindset to NetSol interviewers?"

    # Context dictionary for the AI engine
    ai_context = {
        "candidate_name": cand_name,
        "job_title": job.title,
        "job_company": job.company or "NetSol Technologies",
        "final_score": match.final_score,
        "skill_score": match.skill_score,
        "text_similarity": match.text_similarity,
        "matched": d.get("matched", []),
        "missing_required": missing_req,
        "missing_preferred": missing_pref,
        "job_text": job.text,
        "resume_text": resume.reviewed_text,
    }

    # Render Chat History
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state["chat_history"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Handle user message input (either from chat input or quick prompt)
    user_input = st.chat_input("Ask a question about your skill gaps, interview prep, or CV phrasing...")
    active_prompt = quick_query or user_input

    if active_prompt:
        # Append User Message
        st.session_state["chat_history"].append({"role": "user", "content": active_prompt})
        with st.chat_message("user"):
            st.markdown(active_prompt)

        # Generate Assistant Response
        with st.chat_message("assistant"):
            with st.spinner("AI Coach is formulating technical recommendation..."):
                reply = chat.ask_skill_assistant(active_prompt, ai_context)
                st.markdown(reply)

        # Append Assistant Message
        st.session_state["chat_history"].append({"role": "assistant", "content": reply})
        st.rerun()

    # Footer Action: Clear Chat
    st.write("")
    c1, _, c2 = st.columns([2, 5, 2])
    if c1.button("🗑️ Clear Chat History", key="clear_chat", width="stretch"):
        st.session_state["chat_history"] = [{"role": "assistant", "content": DEFAULT_WELCOME}]
        st.rerun()
    if c2.button("🚀 Go to Learning Center", key="chat_to_learn", type="primary", width="stretch"):
        theme.go("Personalized Learning Center")
        st.rerun()
