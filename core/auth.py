"""Authentication module for FitCheck.

Supports:
  - Email / password login (hashed with hashlib SHA-256 + salt stored in SQLite/Postgres via SQLAlchemy)
  - Google OAuth 2.0 (Sign in with Google)
  - Session management through Streamlit session_state

Google OAuth setup:
  1. Go to https://console.cloud.google.com/
  2. Create a project → Enable "Google+ API" / "People API"
  3. OAuth consent screen → External → fill app name/email
  4. Credentials → Create OAuth client ID → Web application
     - Authorised JavaScript origins: http://localhost:8501
     - Authorised redirect URIs: http://localhost:8501/oauth2callback
  5. Copy Client ID and Client Secret to your .env as:
       GOOGLE_CLIENT_ID=...
       GOOGLE_CLIENT_SECRET=...
       GOOGLE_REDIRECT_URI=http://localhost:8501/oauth2callback
"""
from __future__ import annotations

import hashlib
import os
import secrets
import urllib.parse
from typing import Optional

import config

# ---------------------------------------------------------------------------
# Password hashing (offline, no dependency beyond stdlib)
# ---------------------------------------------------------------------------

def _hash_password(password: str, salt: str) -> str:
    """Return hex-encoded SHA-256(salt + password)."""
    return hashlib.sha256((salt + password).encode()).hexdigest()


def make_password(password: str) -> tuple[str, str]:
    """Generate a (salt, hashed_password) pair for storage."""
    salt = secrets.token_hex(16)
    return salt, _hash_password(password, salt)


def check_password(password: str, salt: str, hashed: str) -> bool:
    """Verify a plain-text password against the stored hash."""
    return _hash_password(password, salt) == hashed


# ---------------------------------------------------------------------------
# Google OAuth 2.0 helpers (uses only urllib – no extra library needed)
# ---------------------------------------------------------------------------

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def google_is_configured() -> bool:
    """Return True if Google OAuth credentials are set in the environment."""
    return bool(
        os.getenv("GOOGLE_CLIENT_ID", "").strip()
        and os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    )


def google_auth_url(state_token: str) -> str:
    """Build the Google OAuth consent-page URL."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8501/oauth2callback"
    ).strip()
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state_token,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)


def google_exchange_code(code: str) -> Optional[dict]:
    """
    Exchange the OAuth authorisation code for user info.
    Returns a dict with keys: email, name, picture, sub (Google ID).
    Returns None on failure.
    """
    import json
    import urllib.request

    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8501/oauth2callback"
    ).strip()

    # 1. Exchange code for tokens
    token_data = urllib.parse.urlencode(
        {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    ).encode()

    try:
        req = urllib.request.Request(
            GOOGLE_TOKEN_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            tokens = json.loads(resp.read())
    except Exception:
        return None

    access_token = tokens.get("access_token")
    if not access_token:
        return None

    # 2. Fetch user info
    try:
        req2 = urllib.request.Request(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            return json.loads(resp2.read())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Session helpers (used by app.py + login_page.py)
# ---------------------------------------------------------------------------

AUTH_KEY = "_fitcheck_auth"


def is_authenticated() -> bool:
    """Return True if the current Streamlit session has a logged-in user."""
    try:
        import streamlit as st
        return bool(st.session_state.get(AUTH_KEY))
    except Exception:
        return False


def current_user() -> Optional[dict]:
    """Return the auth payload dict or None."""
    try:
        import streamlit as st
        return st.session_state.get(AUTH_KEY)
    except Exception:
        return None


def set_authenticated(user_payload: dict) -> None:
    """Store the auth payload in session state."""
    import streamlit as st
    st.session_state[AUTH_KEY] = user_payload


def logout() -> None:
    """Clear authentication from session state."""
    import streamlit as st
    st.session_state.pop(AUTH_KEY, None)
    # Also clear candidate session data so next login starts fresh
    for k in ["cand_id", "cand_name", "resume_id", "job_id", "match_id",
              "cv_flow", "cv_last_change", "ai_notes", "chat_history", "nav"]:
        st.session_state.pop(k, None)
