import json
import urllib.parse
from unittest.mock import patch

from core import auth


def test_google_state_is_one_time_and_survives_session_reset():
    state = auth.create_google_state()

    assert auth.consume_google_state(state)
    assert not auth.consume_google_state(state)
    assert not auth.consume_google_state(None)


def test_google_auth_url_uses_streamlit_root_callback(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.delenv("GOOGLE_REDIRECT_URI", raising=False)

    params = urllib.parse.parse_qs(urllib.parse.urlparse(auth.google_auth_url("state")).query)

    assert params["redirect_uri"] == ["http://localhost:8501/"]
    assert params["state"] == ["state"]


def test_google_exchange_uses_bearer_token_and_same_redirect_uri(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:8501/")
    requests = []

    class Response:
        def __init__(self, payload):
            self.payload = json.dumps(payload).encode()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return self.payload

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        if len(requests) == 1:
            return Response({"access_token": "test-access-token"})
        return Response({"sub": "google-user", "email": "user@example.com"})

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        user_info = auth.google_exchange_code("auth-code")

    assert user_info == {"sub": "google-user", "email": "user@example.com"}
    assert requests[0][1] == requests[1][1] == 10
    assert requests[1][0].get_header("Authorization") == "Bearer test-access-token"
    token_request = urllib.parse.parse_qs(requests[0][0].data.decode())
    assert token_request["redirect_uri"] == ["http://localhost:8501/"]
