"""FitCheck - AI-powered Resume and Job Skill Gap Analyzer.   Run with:  streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="FitCheck", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")

from ui import state, theme  # noqa: E402
from ui.pages import analysis, cv_page, gaps, home, learning, progress, results, settings_page  # noqa: E402

ROUTES = {
    "Home Dashboard": home.render,
    "Resume & Job Analysis": analysis.render,
    "Match Results": results.render,
    "Skill Gap Analysis": gaps.render,
    "Personalized Learning Center": learning.render,
    "My Learning Progress": progress.render,
    "Updated CV & Downloads": cv_page.render,
    "Settings": settings_page.render,
}


def main() -> None:
    theme.inject_css()
    state.init()
    # jump requested by a button callback (must be applied before the radio widget is created)
    target = st.session_state.pop("nav_target", None)
    if target in ROUTES:
        st.session_state["nav"] = target
    st.session_state.setdefault("nav", "Home Dashboard")

    with st.sidebar:
        st.markdown('<div class="brand">Fit<span>Check</span></div>', unsafe_allow_html=True)
        st.caption("Resume & job skill gap analyzer")
        name = st.text_input("Your profile name", value=st.session_state.get("cand_name") or "Guest", key="profile_name",
                             help="Your progress is saved under this name, so you can continue after restarting.")
        try:
            state.switch_candidate(name)
        except Exception as exc:
            st.error(f"Database error: {exc}")
            st.stop()
        st.radio("Navigation", list(ROUTES), key="nav", label_visibility="collapsed")
        st.divider()
        st.caption("Workflow")
        for label, done in state.workflow_status():
            st.markdown(f"{'✅' if done else '⬜'} {label}")

    try:
        ROUTES[st.session_state["nav"]]()
    except Exception as exc:                           # friendly message instead of a stack trace
        st.error(f"Something unexpected happened on this page ({type(exc).__name__}). "
                 "Try again, or open Settings to check the system status.")
        with st.expander("Technical details"):
            st.exception(exc)


main()
