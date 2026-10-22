"""Professional Login & Registration Page for FitCheck.

Handles:
  - Email / Password sign-in and sign-up
  - Sign in with Google (OAuth 2.0)
"""
from __future__ import annotations

import streamlit as st

from core import auth, repository as repo
from ui import state


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _handle_google_callback() -> None:
    """Process the OAuth ?code=... callback that Google redirects to."""
    params = st.query_params
    code = params.get("code")
    state_token = params.get("state")

    if not code:
        return

    if not auth.consume_google_state(state_token):
        st.error("⚠️ OAuth state mismatch. Please try signing in again.")
        st.query_params.clear()
        return

    st.query_params.clear()

    with st.spinner("Completing Google sign-in…"):
        user_info = auth.google_exchange_code(code)

    if (
        not user_info
        or not user_info.get("sub")
        or not user_info.get("email")
        or user_info.get("email_verified") is not True
    ):
        st.error("❌ Google sign-in failed. Please try again.")
        return

    candidate = repo.upsert_google_user(
        google_id=user_info.get("sub", ""),
        email=user_info.get("email", ""),
        display_name=user_info.get("name") or user_info.get("email", "User"),
        avatar_url=user_info.get("picture"),
    )
    auth.set_authenticated({
        "id": candidate.id,
        "name": candidate.display_name,
        "email": candidate.email,
        "avatar": candidate.avatar_url,
        "provider": "google",
    })
    state.switch_candidate(candidate.display_name)
    st.rerun()


def _login_css() -> str:
    return """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
  font-family: "Plus Jakarta Sans", sans-serif;
  background: #060B18 !important;
}

/* Full-page gradient background */
.stApp {
  background: radial-gradient(ellipse at 20% 50%, rgba(37,99,235,0.18) 0%, transparent 60%),
              radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.15) 0%, transparent 55%),
              linear-gradient(135deg, #060B18 0%, #0D1426 50%, #0F172A 100%) !important;
  min-height: 100vh;
}

/* Hide sidebar & toolbar on login */
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
header { display: none !important; }

.block-container {
  padding-top: 0 !important;
  max-width: 480px !important;
  margin: 0 auto !important;
}

/* Login card */
.login-card {
  background: rgba(255,255,255,0.04);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 24px;
  padding: 2.8rem 2.4rem 2.4rem;
  box-shadow:
    0 32px 64px -12px rgba(0,0,0,0.6),
    0 0 0 1px rgba(255,255,255,0.06) inset;
  margin-top: 5vh;
}

/* Logo */
.login-logo {
  text-align: center;
  margin-bottom: 0.25rem;
}
.login-logo .brand {
  font-size: 2.5rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.04em;
}
.login-logo .brand span { color: #60A5FA; }
.login-logo .tagline {
  color: rgba(255,255,255,0.5);
  font-size: 0.88rem;
  margin-top: 0.25rem;
}
.login-logo .badge {
  display: inline-block;
  background: linear-gradient(135deg, #1E3A8A, #2563EB);
  color: #E0E7FF;
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  padding: 0.18rem 0.6rem;
  border-radius: 999px;
  margin-top: 0.5rem;
  text-transform: uppercase;
  border: 1px solid rgba(147,197,253,0.3);
}

/* Divider */
.auth-divider {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 1.1rem 0;
  color: rgba(255,255,255,0.3);
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
}
.auth-divider::before, .auth-divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: rgba(255,255,255,0.1);
}

/* Google button */
.google-btn-wrap a, .google-btn-wrap a:visited {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.65rem;
  background: #fff;
  color: #1F2937 !important;
  font-size: 0.95rem;
  font-weight: 700;
  padding: 0.72rem 1.2rem;
  border-radius: 14px;
  text-decoration: none !important;
  box-shadow: 0 4px 14px rgba(0,0,0,0.35);
  transition: all 0.2s ease;
}
.google-btn-wrap a:hover {
  background: #f3f3f3;
  box-shadow: 0 6px 20px rgba(0,0,0,0.45);
  transform: translateY(-1px);
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: rgba(255,255,255,0.05) !important;
  border-radius: 12px;
  padding: 4px !important;
  border: 1px solid rgba(255,255,255,0.08);
  gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 9px !important;
  color: rgba(255,255,255,0.55) !important;
  font-weight: 600 !important;
  font-size: 0.9rem !important;
  padding: 0.45rem 1.2rem !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, #2563EB, #4F46E5) !important;
  color: #fff !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }

/* Inputs on dark */
.stTextInput label, .stPasswordInput label {
  color: rgba(255,255,255,0.75) !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
}
.stTextInput input, .stPasswordInput input {
  background: rgba(255,255,255,0.07) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  color: #fff !important;
  border-radius: 12px !important;
  font-size: 0.95rem !important;
}
.stTextInput input:focus, .stPasswordInput input:focus {
  border-color: #2563EB !important;
  box-shadow: 0 0 0 3px rgba(37,99,235,0.25) !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #2563EB 0%, #4F46E5 100%) !important;
  color: #fff !important;
  border: none !important;
  border-radius: 12px !important;
  font-weight: 700 !important;
  font-size: 0.97rem !important;
  padding: 0.65rem 1.5rem !important;
  box-shadow: 0 4px 16px rgba(37,99,235,0.4) !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 6px 24px rgba(37,99,235,0.55) !important;
}

/* Secondary button */
.stButton > button:not([kind="primary"]) {
  background: rgba(255,255,255,0.06) !important;
  color: rgba(255,255,255,0.8) !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
}

.stAlert { border-radius: 12px !important; }
</style>
"""


def _google_sign_in_button() -> None:
    """Render a styled 'Sign in with Google' link button."""
    if not auth.google_is_configured():
        st.markdown(
            '<div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);'
            'border-radius:12px;padding:0.75rem 1rem;color:#FCA5A5;font-size:0.85rem;">'
            '⚙️ <b>Google Sign-In not configured.</b> Add <code>GOOGLE_CLIENT_ID</code> and '
            '<code>GOOGLE_CLIENT_SECRET</code> to your <code>.env</code> file to enable it.'
            '</div>',
            unsafe_allow_html=True,
        )
        return

    state_token = auth.create_google_state()
    google_url = auth.google_auth_url(state_token)

    google_icon = (
        '<svg width="20" height="20" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">'
        '<path fill="#EA4335" d="M24 9.5c3.5 0 6.6 1.2 9 3.2l6.7-6.7C35.5 2.5 30.1 0 24 0 '
        '14.7 0 6.8 5.8 3.1 14.2l7.8 6C12.8 13.5 17.9 9.5 24 9.5z"/>'
        '<path fill="#4285F4" d="M46.5 24.5c0-1.6-.1-3.1-.4-4.5H24v8.5h12.7c-.5 2.8-2.1 5.2-4.5 6.8l7 5.4'
        'C43.5 36.8 46.5 31.1 46.5 24.5z"/>'
        '<path fill="#FBBC05" d="M10.9 28.2A14.5 14.5 0 0 1 9.5 24c0-1.5.3-2.9.7-4.2l-7.8-6'
        'A23.9 23.9 0 0 0 0 24c0 3.9.9 7.5 2.5 10.8l8.4-6.6z"/>'
        '<path fill="#34A853" d="M24 48c6.1 0 11.2-2 14.9-5.5l-7-5.4c-2 1.3-4.5 2.1-7.9 2.1'
        '-6.1 0-11.3-4.1-13.1-9.7l-8.4 6.5C6.8 42.2 14.7 48 24 48z"/>'
        '<path fill="none" d="M0 0h48v48H0z"/>'
        '</svg>'
    )

    st.markdown(
        f'<div class="google-btn-wrap"><a href="{google_url}" target="_self">'
        f'{google_icon} &nbsp;Continue with Google</a></div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Main render
# ---------------------------------------------------------------------------

def render() -> None:
    """Render the login page. Returns immediately if already authenticated."""
    # Check for Google OAuth callback
    _handle_google_callback()

    # If authenticated after callback, return so app.py can proceed
    if auth.is_authenticated():
        return

    # Inject login-page CSS
    st.markdown(_login_css(), unsafe_allow_html=True)

    # ── Logo & branding ─────────────────────────────────────────────────────
    st.markdown(
        '<div class="login-card">'
        '<div class="login-logo">'
        '<div class="brand">Fit<span>Check</span></div>'
        '<div class="tagline">AI-powered Resume & Skill Gap Analyzer</div>'
        '<div class="badge">✨ NetSol Presentation Edition</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.write("")

    # ── Google Sign-In ───────────────────────────────────────────────────────
    _google_sign_in_button()

    st.markdown('<div class="auth-divider">OR CONTINUE WITH EMAIL</div>', unsafe_allow_html=True)

    # ── Sign-In / Sign-Up Tabs ───────────────────────────────────────────────
    tab_signin, tab_signup = st.tabs(["🔑  Sign In", "📝  Create Account"])

    with tab_signin:
        _render_signin()

    with tab_signup:
        _render_signup()

    st.markdown("</div>", unsafe_allow_html=True)  # close login-card


def _render_signin() -> None:
    with st.form("signin_form"):
        email_in = st.text_input("Email address", placeholder="you@example.com", key="signin_email")
        pw_in = st.text_input("Password", type="password", placeholder="••••••••", key="signin_password")
        submitted = st.form_submit_button("Sign In", type="primary", key="btn_signin")
    if submitted:
        if not email_in or not pw_in:
            st.error("Please enter your email and password.")
            return
        candidate = repo.find_by_email(email_in)
        if candidate is None or not candidate.password_hash or not candidate.password_salt:
            st.error("❌ No account found with that email. Please create one below.")
            return
        if not auth.check_password(pw_in, candidate.password_salt, candidate.password_hash):
            st.error("❌ Incorrect password. Please try again.")
            return
        # Success
        auth.set_authenticated({
            "id": candidate.id,
            "name": candidate.display_name,
            "email": candidate.email,
            "avatar": candidate.avatar_url,
            "provider": "email",
        })
        state.switch_candidate(candidate.display_name)
        st.rerun()


def _render_signup() -> None:
    with st.form("signup_form"):
        name_in = st.text_input("Full name / Display name", placeholder="Your Name", key="signup_name")
        email_in = st.text_input("Email address", placeholder="you@example.com", key="signup_email")
        pw_in = st.text_input("Password (min 8 chars)", type="password", placeholder="••••••••", key="signup_password")
        pw2_in = st.text_input("Confirm password", type="password", placeholder="••••••••", key="signup_password2")
        submitted = st.form_submit_button("Create Account", type="primary", key="btn_signup")
    if submitted:
        if not all([name_in, email_in, pw_in, pw2_in]):
            st.error("All fields are required.")
            return
        if len(pw_in) < 8:
            st.error("Password must be at least 8 characters.")
            return
        if pw_in != pw2_in:
            st.error("Passwords do not match.")
            return
        try:
            salt, hashed = auth.make_password(pw_in)
            candidate = repo.register_user(
                display_name=name_in,
                email=email_in,
                password_salt=salt,
                password_hash=hashed,
            )
        except ValueError as e:
            st.error(f"❌ {e}")
            return
        except Exception as e:
            st.error(f"Registration failed: {e}")
            return
        # Auto-login after registration
        auth.set_authenticated({
            "id": candidate.id,
            "name": candidate.display_name,
            "email": candidate.email,
            "avatar": None,
            "provider": "email",
        })
        state.switch_candidate(candidate.display_name)
        st.success(f"✅ Account created! Welcome, {candidate.display_name}!")
        st.rerun()
