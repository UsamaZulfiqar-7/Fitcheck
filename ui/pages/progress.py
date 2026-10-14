"""My Learning Progress."""
import pandas as pd
import streamlit as st

from core import repository as repo
from ui import charts, theme


def _continue(skill: str) -> None:
    st.session_state["learn_skill"] = skill
    st.session_state["cv_flow"] = None
    theme.go("Personalized Learning Center")


def render() -> None:
    theme.hero("My Learning Progress", "Everything you started learning, saved in the database so you can continue any time.")
    cand = st.session_state["cand_id"]
    summary = repo.progress_summary(cand)
    if not summary:
        theme.empty_state("Nothing started yet", "Open a missing skill in the Learning Center and tick the first topic.",
                          "Open Learning Center", "Personalized Learning Center", key="prog_empty")
        return
    topics_done = sum(p["done"] for p in summary)
    topics_total = sum(p["total"] for p in summary)
    finished = sum(1 for p in summary if p["status"] == "completed")
    theme.kpi_row([("Skills started", len(summary), "learning paths", "indigo"),
                   ("Paths completed", finished, "marked complete by you", "good" if finished else "indigo"),
                   ("Topics completed", topics_done, f"of {topics_total}", "indigo"),
                   ("Overall progress", f"{(topics_done / topics_total * 100) if topics_total else 0:.0f}%", "all started skills", "indigo")])
    st.write("")
    percents = [(p["done"] / p["total"] * 100) if p["total"] else 0 for p in summary]
    st.plotly_chart(charts.progress_bars([p["skill"] for p in summary], percents), width="stretch")

    for p, pct in zip(summary, percents):
        with st.container(border=True):
            a, b, c = st.columns([3, 3, 2])
            a.markdown(f"**{p['skill']}**  \n{theme.badge(p['category'])}{theme.badge(p['status'].replace('_', ' '))}",
                       unsafe_allow_html=True)
            b.progress(min(pct / 100, 1.0), text=f"{p['done']} of {p['total']} topics")
            if p["last_topic"]:
                b.caption(f"Last completed: {p['last_topic']}")
            c.button("Continue" if p["status"] != "completed" else "Review", key=f"cont_{p['skill']}",
                     on_click=_continue, args=(p["skill"],), width="stretch")
    df = pd.DataFrame([{"Skill": p["skill"], "Status": p["status"], "Done": p["done"], "Total": p["total"],
                        "Started": p["started_at"].strftime("%Y-%m-%d"),
                        "Completed": p["completed_at"].strftime("%Y-%m-%d") if p["completed_at"] else ""} for p in summary])
    with st.expander("Table view"):
        st.dataframe(df, hide_index=True, width="stretch")
