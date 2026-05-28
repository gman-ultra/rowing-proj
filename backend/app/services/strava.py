import json
import urllib.parse
import urllib.request
from urllib.error import URLError

from app.config import settings

REQUIRED_SCOPE = "activity:read_all"


def _auth_url() -> str:
    return f"{settings.strava_base_url}/oauth/authorize"


def _token_url() -> str:
    return f"{settings.strava_base_url}/oauth/token"


def _api_base() -> str:
    return settings.strava_api_base_url


class StravaAPIError(Exception):
    pass


def build_authorization_url(state: str) -> str:
    params = urllib.parse.urlencode({
        "client_id": settings.strava_client_id,
        "redirect_uri": settings.strava_redirect_uri,
        "response_type": "code",
        "approval_prompt": settings.strava_approval_prompt,
        "scope": REQUIRED_SCOPE,
        "state": state,
    })
    return f"{_auth_url()}?{params}"


def _post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        raise StravaAPIError(f"Strava API POST failed: {e}") from e


def exchange_code_for_token(code: str) -> dict:
    return _post_form(_token_url(), {
        "client_id": settings.strava_client_id,
        "client_secret": settings.strava_client_secret,
        "code": code,
        "grant_type": "authorization_code",
    })


def refresh_access_token(refresh_token: str) -> dict:
    return _post_form(_token_url(), {
        "client_id": settings.strava_client_id,
        "client_secret": settings.strava_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    })


def _get(url: str, access_token: str) -> dict:
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except URLError as e:
        raise StravaAPIError(f"Strava API GET failed: {e}") from e


def fetch_activities(
    access_token: str,
    after: int | None = None,
    per_page: int = 100,
    max_pages: int = 5,
) -> list[dict]:
    all_activities: list[dict] = []
    for page in range(1, max_pages + 1):
        params = {"page": page, "per_page": per_page}
        if after is not None:
            params["after"] = after
        qs = urllib.parse.urlencode(params)
        url = f"{_api_base()}/athlete/activities?{qs}"
        result = _get(url, access_token)
        if not isinstance(result, list):
            raise StravaAPIError(
                f"Expected list from Strava activities API, got {type(result).__name__}"
            )
        all_activities.extend(result)
        if len(result) < per_page:
            break
    return all_activities


def fetch_athlete_activities(access_token: str, page: int = 1, per_page: int = 100) -> list[dict]:
    return fetch_activities(access_token, after=None, per_page=per_page, max_pages=1)
