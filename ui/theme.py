"""Look and feel: VIP Enterprise SaaS style, reusable HTML components for NetSol presentation."""
from __future__ import annotations

from html import escape

import streamlit as st

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

:root {
  --ink: #0F172A;
  --ink-secondary: #334155;
  --muted: #64748B;
  --line: #E2E8F0;
  --line-strong: #CBD5E1;
  --indigo: #4F46E5;
  --blue: #2563EB;
  --blue-light: #38BDF8;
  --soft: #EEF2FF;
  --good: #059669;
  --warn: #D97706;
  --bad: #DC2626;
  --bg-page: #F8FAFC;
}

html, body, [class*="css"] {
  font-family: "Plus Jakarta Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--ink);
}

.block-container {
  padding-top: 1.5rem;
  padding-bottom: 3.5rem;
  max-width: 1220px;
}

/* Headings */
h1, h2, h3, h4 {
  font-family: "Plus Jakarta Sans", "Inter", sans-serif;
  color: var(--ink);
  letter-spacing: -0.02em;
  font-weight: 700;
}

/* Sidebar Styling - VIP Dark Executive Navy */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #090D16 0%, #0F172A 50%, #111827 100%) !important;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}
[data-testid="stSidebar"] * {
  color: #E2E8F0 !important;
}
[data-testid="stSidebar"] input {
  color: #0F172A !important;
  background-color: #FFFFFF !important;
  border-radius: 10px !important;
}
[data-testid="stSidebar"] [role="radiogroup"] {
  gap: 0.35rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: 0.5rem 0.8rem;
  border-radius: 12px;
  transition: all 0.2s ease;
  font-weight: 500;
  font-size: 0.92rem;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(3px);
}
[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.25) 0%, rgba(99, 102, 241, 0.3) 100%);
  border: 1px solid rgba(99, 102, 241, 0.4);
}

/* Brand Logo & Presentation Edition Badge */
.brand-container {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.2rem;
}
.brand {
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  color: #FFFFFF;
}
.brand span {
  color: #60A5FA;
  text-shadow: 0 0 16px rgba(96, 165, 250, 0.4);
}
.vip-badge {
  display: inline-block;
  background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
  color: #E0E7FF;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  border: 1px solid rgba(147, 197, 253, 0.3);
  text-transform: uppercase;
}

/* Hero Banner - Sleek High-Impact Gradient */
.hero {
  position: relative;
  background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #2563EB 100%);
  color: #FFFFFF;
  padding: 1.8rem 2.2rem;
  border-radius: 20px;
  margin-bottom: 1.25rem;
  box-shadow: 0 16px 36px -8px rgba(30, 58, 138, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.12);
  overflow: hidden;
}
.hero::before {
  content: "";
  position: absolute;
  top: -50px;
  right: -50px;
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.25) 0%, rgba(255, 255, 255, 0) 70%);
  border-radius: 50%;
  pointer-events: none;
}
.hero h1 {
  color: #FFFFFF;
  margin: 0 0 0.4rem 0;
  font-size: 2.05rem;
  font-weight: 800;
  letter-spacing: -0.025em;
}
.hero p {
  color: #E0E7FF;
  margin: 0;
  font-size: 1.05rem;
  line-height: 1.55;
  max-width: 820px;
}
.hero .hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(8px);
  color: #DBEAFE;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.25rem 0.7rem;
  border-radius: 999px;
  margin-bottom: 0.65rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* Executive KPI Tiles */
.kpi {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.15rem 1.25rem;
  height: 100%;
  box-shadow: 0 4px 12px -2px rgba(15, 23, 42, 0.05), 0 1px 3px rgba(15, 23, 42, 0.03);
  transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  position: relative;
  overflow: hidden;
}
.kpi:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 28px -4px rgba(15, 23, 42, 0.09), 0 2px 6px rgba(15, 23, 42, 0.04);
  border-color: var(--line-strong);
}
.kpi::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--indigo);
  border-top-left-radius: 18px;
  border-bottom-left-radius: 18px;
}
.kpi.good::after { background: var(--good); }
.kpi.warn::after { background: var(--warn); }
.kpi.bad::after { background: var(--bad); }

.kpi .label {
  color: var(--muted);
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 700;
}
.kpi .value {
  color: var(--ink);
  font-size: 2.05rem;
  font-weight: 800;
  line-height: 1.15;
  margin-top: 0.25rem;
  letter-spacing: -0.02em;
}
.kpi.good .value { color: var(--good); }
.kpi.warn .value { color: var(--warn); }
.kpi.bad .value { color: var(--bad); }
.kpi.indigo .value { color: var(--indigo); }
.kpi .sub {
  color: var(--muted);
  font-size: 0.82rem;
  margin-top: 0.25rem;
  font-weight: 500;
}

/* Polished Cards */
.card {
  background: #FFFFFF;
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 1.25rem 1.4rem;
  margin-bottom: 1rem;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.03);
}
.card h4 {
  margin: 0 0 0.45rem 0;
  color: var(--ink);
  font-size: 1.15rem;
}

/* Step Wizard */
.step {
  display: flex;
  gap: 0.9rem;
  align-items: flex-start;
  margin: 0.7rem 0;
}
.step .num {
  background: var(--soft);
  color: var(--indigo);
  font-weight: 800;
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 2.2rem;
  box-shadow: 0 2px 6px rgba(79, 70, 229, 0.15);
}
.step.done .num {
  background: linear-gradient(135deg, #059669 0%, #10B981 100%);
  color: #FFFFFF;
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.3);
}
.step .t {
  font-weight: 700;
  color: var(--ink);
  font-size: 0.98rem;
}
.step .d {
  color: var(--muted);
  font-size: 0.88rem;
  line-height: 1.4;
}

/* Badge Chips */
.chip {
  display: inline-block;
  padding: 0.28rem 0.75rem;
  margin: 0.2rem 0.3rem 0.2rem 0;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}
.chip.good { background: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; }
.chip.bad { background: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; }
.chip.warn { background: #FFFBEB; border: 1px solid #FDE68A; color: #92400E; }
.chip.info { background: #EFF6FF; border: 1px solid #BFDBFE; color: #1E40AF; }
.chip.muted { background: #F8FAFC; border: 1px solid #E2E8F0; color: #475569; }

.badge {
  display: inline-block;
  padding: 0.22rem 0.7rem;
  border-radius: 8px;
  font-size: 0.76rem;
  font-weight: 700;
  background: #EEF2FF;
  color: #3730A3;
  border: 1px solid #C7D2FE;
  margin-right: 0.35rem;
}

/* Notices & Empty States */
.notice {
  background: #F0F9FF;
  border-left: 4px solid var(--blue);
  padding: 0.85rem 1.15rem;
  border-radius: 10px;
  color: #0C4A6E;
  font-size: 0.92rem;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}
.empty {
  text-align: center;
  padding: 2.6rem 1.2rem;
  border: 2px dashed #CBD5E1;
  border-radius: 20px;
  background: #FFFFFF;
  color: var(--muted);
}
.empty h3 {
  color: var(--ink);
  margin-bottom: 0.35rem;
}

/* Primary Streamlit Buttons */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB 0%, #4F46E5 100%) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  padding: 0.55rem 1.25rem !important;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
  transform: translateY(-1px) !important;
}
.stButton > button, .stDownloadButton > button {
  border-radius: 12px !important;
  font-weight: 600 !important;
  transition: all 0.2s ease !important;
}

@media (max-width: 900px) {
  .hero { padding: 1.3rem 1.3rem; }
  .hero h1 { font-size: 1.55rem; }
  .kpi .value { font-size: 1.6rem; }
  .block-container { padding-left: 1rem; padding-right: 1rem; }
}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, badge_text: str = "NetSol Presentation Edition") -> None:
    st.markdown(
        f'<div class="hero">'
        f'<div class="hero-tag">✨ {escape(badge_text)}</div>'
        f'<h1>{escape(title)}</h1>'
        f'<p>{escape(subtitle)}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_html(label: str, value, sub: str = "", tone: str = "indigo") -> str:
    return (
        f'<div class="kpi {tone}">'
        f'<div class="label">{escape(str(label))}</div>'
        f'<div class="value">{escape(str(value))}</div>'
        f'<div class="sub">{escape(sub)}</div>'
        f'</div>'
    )


def kpi_row(items: list[tuple]) -> None:
    """items: (label, value, sub, tone)"""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, *rest = item
        col.markdown(
            kpi_html(label, value, rest[0] if rest else "", rest[1] if len(rest) > 1 else "indigo"),
            unsafe_allow_html=True,
        )


def chips(items, tone: str = "info") -> str:
    if not items:
        return '<span class="chip muted">none</span>'
    return "".join(f'<span class="chip {tone}">{escape(str(i))}</span>' for i in items)


def badge(text: str) -> str:
    return f'<span class="badge">{escape(text)}</span>'


def card(html: str) -> None:
    st.markdown(f'<div class="card">{html}</div>', unsafe_allow_html=True)


def go(page: str) -> None:
    """on_click callback: jump to another page."""
    st.session_state["nav_target"] = page


def empty_state(title: str, text: str, button: str | None = None, target: str | None = None, key: str = "empty") -> None:
    st.markdown(f'<div class="empty"><h3>{escape(title)}</h3><p>{escape(text)}</p></div>', unsafe_allow_html=True)
    if button and target:
        _, mid, _ = st.columns([1, 1, 1])
        mid.button(button, key=key, on_click=go, args=(target,), type="primary", width="stretch")


def tone_for_score(score: float) -> str:
    return "good" if score >= 80 else "warn" if score >= 50 else "bad"

