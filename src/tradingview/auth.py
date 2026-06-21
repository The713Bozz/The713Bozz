"""
TradingView account authentication.

TradingView uses session cookies. We POST credentials to their sign-in endpoint
and store the resulting session token. The token is reused across requests and
refreshed automatically when it expires (HTTP 401).

Set these in your .env file:
  TV_USERNAME=your_tradingview_username
  TV_PASSWORD=your_tradingview_password
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

import requests

_SIGNIN_URL = "https://www.tradingview.com/accounts/signin/"
_SESSION_URL = "https://www.tradingview.com/accounts/profile/"
_TOKEN_CACHE = Path(__file__).parent.parent.parent / "config" / "tv_session.json"

_HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.tradingview.com/",
    "Origin": "https://www.tradingview.com",
}


class TVAuthError(Exception):
    pass


class TVAuth:
    """Holds a live TradingView session and provides authenticated requests."""

    def __init__(self, username: str = "", password: str = ""):
        self.username = username or os.environ.get("TV_USERNAME", "")
        self.password = password or os.environ.get("TV_PASSWORD", "")
        self._session_token: Optional[str] = None
        self._session_sign: Optional[str] = None
        self._expires_at: float = 0.0

        if not self.username or not self.password:
            raise TVAuthError(
                "TV_USERNAME and TV_PASSWORD must be set in environment or passed explicitly."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def connect(self) -> dict:
        """Sign in and return account profile."""
        cached = self._load_cache()
        if cached and time.time() < cached.get("expires_at", 0) - 60:
            self._session_token = cached["session_token"]
            self._session_sign = cached.get("session_sign", "")
            self._expires_at = cached["expires_at"]
        else:
            self._do_signin()

        profile = self._get_profile()
        return profile

    def session_headers(self) -> dict:
        """Return headers with auth cookies for use in any TV HTTP request."""
        if time.time() >= self._expires_at - 60:
            self._do_signin()
        cookie = f"sessionid={self._session_token}"
        if self._session_sign:
            cookie += f"; sessionid_sign={self._session_sign}"
        return {**_HEADERS, "Cookie": cookie}

    def logout(self) -> None:
        """Clear cached session."""
        self._session_token = None
        self._session_sign = None
        self._expires_at = 0.0
        if _TOKEN_CACHE.exists():
            _TOKEN_CACHE.unlink()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _do_signin(self) -> None:
        payload = {
            "username": self.username,
            "password": self.password,
            "remember": "on",
        }
        resp = requests.post(_SIGNIN_URL, data=payload, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            raise TVAuthError(
                f"TradingView sign-in failed: HTTP {resp.status_code}. "
                "Check TV_USERNAME / TV_PASSWORD."
            )

        # sessionid is in the response cookies
        cookies = resp.cookies
        session_token = cookies.get("sessionid")
        if not session_token:
            body = resp.text[:300]
            raise TVAuthError(
                f"TradingView sign-in: no sessionid in response cookies. "
                f"Response snippet: {body!r}"
            )

        self._session_token = session_token
        self._session_sign = cookies.get("sessionid_sign", "")
        self._expires_at = time.time() + 86400  # tokens last ~24 h

        self._save_cache()

    def _get_profile(self) -> dict:
        resp = requests.get(
            _SESSION_URL, headers=self.session_headers(), timeout=15
        )
        if resp.status_code == 401:
            self._do_signin()
            resp = requests.get(
                _SESSION_URL, headers=self.session_headers(), timeout=15
            )
        if resp.status_code != 200:
            raise TVAuthError(
                f"Could not fetch TradingView profile: HTTP {resp.status_code}"
            )
        try:
            data = resp.json()
        except ValueError:
            data = {}
        return {
            "username": data.get("username", self.username),
            "plan": data.get("plan", "unknown"),
            "id": data.get("id"),
            "email": data.get("email", ""),
        }

    def _load_cache(self) -> Optional[dict]:
        if not _TOKEN_CACHE.exists():
            return None
        try:
            return json.loads(_TOKEN_CACHE.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def _save_cache(self) -> None:
        _TOKEN_CACHE.parent.mkdir(parents=True, exist_ok=True)
        _TOKEN_CACHE.write_text(
            json.dumps(
                {
                    "username": self.username,
                    "session_token": self._session_token,
                    "session_sign": self._session_sign,
                    "expires_at": self._expires_at,
                },
                indent=2,
            )
        )


def connect_from_env() -> dict:
    """Convenience: authenticate using env vars and return profile dict."""
    auth = TVAuth()
    return auth.connect()
