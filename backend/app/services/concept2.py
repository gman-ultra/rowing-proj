import json
import urllib.parse
import urllib.request
from urllib.error import URLError

from app.config import settings

C2_ACCEPT_HEADER = "application/vnd.c2logbook.v1+json"


class Concept2APIError(Exception):
    pass


def _post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Accept", C2_ACCEPT_HEADER)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        raise Concept2APIError(f"Concept2 API POST failed: {e}") from e


def build_authorization_url(state: str) -> str:
    params = urllib.parse.urlencode({
        "client_id": settings.concept2_client_id,
        "scope": "results:read",
        "response_type": "code",
        "redirect_uri": settings.concept2_redirect_uri,
        "state": state,
    })
    return f"{settings.concept2_base_url}/oauth/authorize?{params}"


def exchange_code_for_token(code: str) -> dict:
    return _post_form(f"{settings.concept2_base_url}/oauth/access_token", {
        "client_id": settings.concept2_client_id,
        "client_secret": settings.concept2_client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.concept2_redirect_uri,
        "scope": "results:read",
    })


def refresh_access_token(refresh_token: str) -> dict:
    return _post_form(f"{settings.concept2_base_url}/oauth/access_token", {
        "client_id": settings.concept2_client_id,
        "client_secret": settings.concept2_client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "scope": "results:read",
    })


def fetch_results(access_token: str, updated_after: str | None = None) -> list:
    url = f"{settings.concept2_base_url}/api/users/me/results"
    if updated_after:
        url += f"?updated_after={urllib.parse.quote(updated_after)}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    req.add_header("Accept", C2_ACCEPT_HEADER)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        raise Concept2APIError(f"Concept2 API GET failed: {e}") from e
