import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.integration import Concept2Connection, OAuthState
from app.models.user import User
from app.schemas.concept2 import (
    Concept2ConnectResponse,
    Concept2StatusResponse,
    Concept2SyncResponse,
)
from app.services import concept2 as concept2_service
from app.services import concept2_importer
from app.services import token_crypto as token_crypto_service
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/integrations/concept2", tags=["concept2"])


@router.get("/status", response_model=Concept2StatusResponse)
def get_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(Concept2Connection)
        .filter(Concept2Connection.user_id == current_user.id)
        .first()
    )
    if not conn:
        return Concept2StatusResponse(connected=False)
    return Concept2StatusResponse(
        connected=True,
        concept2_user_id=conn.concept2_user_id,
        last_sync_at=conn.last_sync_at,
        token_expires_at=conn.token_expires_at,
    )


@router.post("/connect", response_model=Concept2ConnectResponse)
def connect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not settings.concept2_client_id or not settings.concept2_client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Concept2 OAuth is not configured",
        )
    state = secrets.token_urlsafe(32)
    oauth_state = OAuthState(
        user_id=current_user.id,
        provider="concept2",
        state=state,
        expires_at=datetime.utcnow() + timedelta(minutes=10),
    )
    db.add(oauth_state)
    db.commit()

    authorization_url = concept2_service.build_authorization_url(state)
    return Concept2ConnectResponse(authorization_url=authorization_url)


@router.get("/callback")
def callback(
    state: str = Query(...),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    oauth_state = (
        db.query(OAuthState)
        .filter(
            OAuthState.state == state,
            OAuthState.provider == "concept2",
        )
        .first()
    )
    if not oauth_state:
        return _error_html("Invalid state parameter.")
    if oauth_state.consumed_at is not None:
        return _error_html("State has already been used.")
    if oauth_state.expires_at < datetime.utcnow():
        return _error_html("State has expired.")

    try:
        token_data = concept2_service.exchange_code_for_token(code)
    except Exception as e:
        return _error_html(f"Token exchange failed: {e}")

    access_token_enc = token_crypto_service.encrypt_token(token_data["access_token"])
    refresh_token_enc = token_crypto_service.encrypt_token(token_data.get("refresh_token", "")) if token_data.get("refresh_token") else None

    expires_in = token_data.get("expires_in")
    token_expires_at = (
        datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
    )

    concept2_user_id = str(token_data.get("concept2_user_id", "")) or None

    existing = (
        db.query(Concept2Connection)
        .filter(Concept2Connection.user_id == oauth_state.user_id)
        .first()
    )
    if existing:
        existing.access_token_encrypted = access_token_enc
        existing.refresh_token_encrypted = refresh_token_enc
        existing.token_expires_at = token_expires_at
        existing.scope = token_data.get("scope", "results:read")
        existing.concept2_user_id = concept2_user_id
    else:
        conn = Concept2Connection(
            user_id=oauth_state.user_id,
            concept2_user_id=concept2_user_id,
            access_token_encrypted=access_token_enc,
            refresh_token_encrypted=refresh_token_enc,
            token_expires_at=token_expires_at,
            scope=token_data.get("scope", "results:read"),
        )
        db.add(conn)

    oauth_state.consumed_at = datetime.utcnow()
    db.commit()

    html = f"""<!DOCTYPE html>
<html>
<head><title>Connected to Concept2</title></head>
<body>
<h1>Concept2 Connected</h1>
<p>Your RowApp account is now linked to Concept2 Logbook (user {concept2_user_id}). You can close this window and return to the app.</p>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)


@router.post("/sync", response_model=Concept2SyncResponse)
def sync(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(Concept2Connection)
        .filter(Concept2Connection.user_id == current_user.id)
        .first()
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Concept2 connection found. Connect first.",
        )

    access_token = token_crypto_service.decrypt_token(conn.access_token_encrypted)
    if conn.token_expires_at and conn.token_expires_at < datetime.utcnow() + timedelta(minutes=5):
        if conn.refresh_token_encrypted:
            refresh_token = token_crypto_service.decrypt_token(conn.refresh_token_encrypted)
            try:
                token_data = concept2_service.refresh_access_token(refresh_token)
                conn.access_token_encrypted = token_crypto_service.encrypt_token(token_data["access_token"])
                if token_data.get("refresh_token"):
                    conn.refresh_token_encrypted = token_crypto_service.encrypt_token(token_data["refresh_token"])
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
        results = concept2_service.fetch_results(access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch Concept2 results: {e}",
        )

    if not isinstance(results, list):
        results = results.get("data", results) if isinstance(results, dict) else results

    sync_result = concept2_importer.sync_concept2_results(db, current_user.id, results)

    conn.last_sync_at = datetime.utcnow()
    db.commit()

    return Concept2SyncResponse(**sync_result)


@router.post("/disconnect", status_code=status.HTTP_200_OK)
def disconnect(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conn = (
        db.query(Concept2Connection)
        .filter(Concept2Connection.user_id == current_user.id)
        .first()
    )
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No Concept2 connection found.",
        )
    db.delete(conn)
    db.commit()
    return {"message": "Concept2 connection removed. Imported workouts were kept."}


def _error_html(message: str):
    html = f"""<!DOCTYPE html>
<html>
<head><title>Concept2 Connection Error</title></head>
<body>
<h1>Error</h1>
<p>{message}</p>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=400)
