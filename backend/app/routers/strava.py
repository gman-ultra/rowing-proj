import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.integration import OAuthState, StravaConnection
from app.models.user import User
from app.schemas.strava import (
    StravaConnectResponse,
    StravaStatusResponse,
    StravaSyncResponse,
)
from app.services import strava as strava_service
from app.services import strava_importer
from app.services.auth import get_current_user
from app.services.token_crypto import decrypt_with_key, encrypt_with_key

REQUIRED_SCOPE = "activity:read_all"

router = APIRouter(prefix="/api/integrations/strava", tags=["strava"])


def _get_encryption_key() -> str:
    key = settings.strava_token_encryption_key
    if not key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Strava token encryption is not configured",
        )
    return key


@router.get("/status", response_model=StravaStatusResponse)
def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(StravaConnection)
        .filter(StravaConnection.user_id == current_user.id)
        .first()
    )
    if not conn:
        return StravaStatusResponse(connected=False)
    return StravaStatusResponse(
        connected=True,
        strava_athlete_id=conn.strava_athlete_id,
        last_sync_at=conn.last_sync_at,
        token_expires_at=conn.token_expires_at,
    )


@router.post("/connect", response_model=StravaConnectResponse)
def connect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.strava_client_id or not settings.strava_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Strava OAuth is not configured",
        )
    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        user_id=current_user.id,
        provider="strava",
        state=state,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(oauth_state)
    db.commit()

    authorization_url = strava_service.build_authorization_url(state)
    return StravaConnectResponse(authorization_url=authorization_url)


@router.get("/callback")
def callback(
    state: str = Query(...),
    code: str | None = Query(None),
    error: str | None = Query(None),
    scope: str | None = Query(None),
    db: Session = Depends(get_db),
):
    if error:
        return _error_html(f"Strava denied authorization: {error}")

    if not code:
        return _error_html("Missing authorization code from Strava.")

    oauth_state = (
        db.query(OAuthState)
        .filter(
            OAuthState.state == state,
            OAuthState.provider == "strava",
        )
        .first()
    )
    if not oauth_state:
        return _error_html("Invalid state parameter.")
    if oauth_state.consumed_at is not None:
        return _error_html("State has already been used.")
    if oauth_state.expires_at < datetime.utcnow():
        return _error_html("State has expired.")

    if not scope:
        return _error_html(
            f"Required scope '{REQUIRED_SCOPE}' was not granted. "
            f"Granted scope: none"
        )
    granted_scopes = {s.strip() for s in scope.split(",")}
    if REQUIRED_SCOPE not in granted_scopes:
        return _error_html(
            f"Required scope '{REQUIRED_SCOPE}' was not granted. "
            f"Granted scope: {scope}"
        )

    try:
        token_data = strava_service.exchange_code_for_token(code)
    except Exception as e:
        return _error_html(f"Token exchange failed: {e}")

    encryption_key = _get_encryption_key()
    access_token_enc = encrypt_with_key(token_data["access_token"], encryption_key)
    refresh_token_enc = (
        encrypt_with_key(token_data.get("refresh_token", ""), encryption_key)
        if token_data.get("refresh_token")
        else None
    )

    raw_expires_at = token_data.get("expires_at")
    if raw_expires_at:
        token_expires_at = datetime.utcfromtimestamp(raw_expires_at)
    else:
        expires_in = token_data.get("expires_in")
        token_expires_at = (
            datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
        )

    athlete = token_data.get("athlete") or {}
    strava_athlete_id = str(athlete.get("id", "")) or None

    existing = (
        db.query(StravaConnection)
        .filter(StravaConnection.user_id == oauth_state.user_id)
        .first()
    )
    if existing:
        existing.access_token_encrypted = access_token_enc
        existing.refresh_token_encrypted = refresh_token_enc
        existing.token_expires_at = token_expires_at
        existing.scope = scope
        existing.strava_athlete_id = strava_athlete_id
    else:
        conn = StravaConnection(
            user_id=oauth_state.user_id,
            strava_athlete_id=strava_athlete_id,
            access_token_encrypted=access_token_enc,
            refresh_token_encrypted=refresh_token_enc,
            token_expires_at=token_expires_at,
            scope=scope,
        )
        db.add(conn)

    oauth_state.consumed_at = datetime.utcnow()
    db.commit()

    html = f"""<!DOCTYPE html>
<html>
<head><title>Connected to Strava</title></head>
<body>
<h1>Strava Connected</h1>
<p>Your RowApp account is now linked to Strava athlete {strava_athlete_id}. You can close this window and return to the app.</p>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)


@router.post("/sync", response_model=StravaSyncResponse)
def sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(StravaConnection)
        .filter(StravaConnection.user_id == current_user.id)
        .first()
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Strava connection found. Connect first.",
        )

    encryption_key = _get_encryption_key()
    access_token = decrypt_with_key(conn.access_token_encrypted, encryption_key)

    if conn.token_expires_at and conn.token_expires_at < datetime.utcnow() + timedelta(minutes=5):
        if conn.refresh_token_encrypted:
            refresh_token = decrypt_with_key(conn.refresh_token_encrypted, encryption_key)
            try:
                token_data = strava_service.refresh_access_token(refresh_token)
                conn.access_token_encrypted = encrypt_with_key(
                    token_data["access_token"], encryption_key
                )
                if token_data.get("refresh_token"):
                    conn.refresh_token_encrypted = encrypt_with_key(
                        token_data["refresh_token"], encryption_key
                    )
                raw_expires_at = token_data.get("expires_at")
                if raw_expires_at:
                    conn.token_expires_at = datetime.utcfromtimestamp(raw_expires_at)
                else:
                    expires_in = token_data.get("expires_in")
                    conn.token_expires_at = (
                        datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
                    )
                db.flush()
                access_token = token_data["access_token"]
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Token refresh failed: {e}",
                )

    try:
        after_timestamp = int(conn.last_sync_at.timestamp()) if conn.last_sync_at else None
        activities = strava_service.fetch_activities(access_token, after=after_timestamp)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch Strava activities: {e}",
        )

    sync_result = strava_importer.sync_strava_activities(db, current_user.id, activities)

    conn.last_sync_at = datetime.utcnow()
    db.commit()

    return StravaSyncResponse(**sync_result)


@router.post("/disconnect", status_code=status.HTTP_200_OK)
def disconnect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(StravaConnection)
        .filter(StravaConnection.user_id == current_user.id)
        .first()
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Strava connection found.",
        )
    db.delete(conn)
    db.commit()
    return {"message": "Strava connection removed. Imported workouts were kept."}


def _error_html(message: str):
    html = f"""<!DOCTYPE html>
<html>
<head><title>Strava Connection Error</title></head>
<body>
<h1>Error</h1>
<p>{message}</p>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=400)
