import re
import secrets
from typing import Annotated

from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import FacebookAuth, GoogleAuth, Users
from schemas import OAuthCodeExchange, TokenResponse
from utils.auth import (
    create_access_token,
    hash_password,
)
from utils.redis import redis

router = APIRouter()
db_dependency = Annotated[Session, Depends(get_db)]

oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)
oauth.register(
    name="facebook",
    client_id=settings.facebook_client_id,
    client_secret=settings.facebook_client_secret,
    authorize_url="https://www.facebook.com/dialog/oauth",
    access_token_url="https://graph.facebook.com/oauth/access_token",
    api_base_url="https://graph.facebook.com/",
    client_kwargs={"scope": "email public_profile"},
)


def _oauth_redirect_uri(provider: str) -> str:
    return f"{settings.backend_url.rstrip('/')}/api/v1/auth/{provider}/callback"


def _oauth_error_redirect() -> RedirectResponse:
    return RedirectResponse(
        f"{settings.frontend_url.rstrip('/')}/oauth/callback?error=oauth_failed",
        status_code=status.HTTP_303_SEE_OTHER,
    )


def _get_or_create_social_user(
    db: Session,
    identity_model: type[GoogleAuth] | type[FacebookAuth],
    provider_id: str,
    email: str | None,
    full_name: str,
) -> Users:
    with db.begin():
        identity_query = db.query(identity_model)
        if identity_model is GoogleAuth:
            identity = identity_query.filter(GoogleAuth.google_id == provider_id).first()
        else:
            identity = identity_query.filter(FacebookAuth.facebook_id == provider_id).first()

        if identity:
            user = db.query(Users).filter(Users.id == identity.user_id).first()
            if not user or not user.is_active:
                raise HTTPException(status_code=403, detail="Account is inactive")
            return user

        normalized_email = email.strip().lower() if email else None
        user = (
            db.query(Users).filter(Users.email == normalized_email).first()
            if normalized_email
            else None
        )
        if user:
            if not user.is_active:
                raise HTTPException(status_code=403, detail="Account is inactive")
        else:
            name_parts = full_name.strip().split(maxsplit=1)
            username_seed = (
                normalized_email.split("@", 1)[0]
                if normalized_email
                else f"social_{provider_id}"
            )
            username_base = re.sub(r"[^a-zA-Z0-9_.-]", "", username_seed)[:90]
            username_base = username_base or "social_user"
            username = username_base
            while db.query(Users).filter(Users.username == username).first():
                username = f"{username_base[:88]}-{secrets.token_hex(4)}"

            user = Users(
                username=username,
                email=normalized_email,
                firstname=name_parts[0] if name_parts else username_base,
                lastname=name_parts[1] if len(name_parts) > 1 else "",
                password=None,
            )
            db.add(user)
            db.flush()

        if identity_model is GoogleAuth:
            db.add(GoogleAuth(google_id=provider_id, user_id=user.id))
        else:
            db.add(FacebookAuth(facebook_id=provider_id, user_id=user.id))
    return user


def _finish_oauth_login(user: Users) -> RedirectResponse:
    code = secrets.token_urlsafe(32)
    redis.setex(f"oauth_login_code:{code}", 60, str(user.id))
    return RedirectResponse(
        f"{settings.frontend_url.rstrip('/')}/oauth/callback?code={code}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/google")
async def google_login(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=503, detail="Google login is not configured")
    return await oauth.google.authorize_redirect(
        request, _oauth_redirect_uri("google")
    )


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, db: db_dependency):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return _oauth_error_redirect()

    user_info = token.get("userinfo") or await oauth.google.userinfo(token=token)
    if (
        not user_info
        or not user_info.get("sub")
        or not user_info.get("email")
        or not user_info.get("email_verified")
    ):
        return _oauth_error_redirect()

    user = _get_or_create_social_user(
        db,
        GoogleAuth,
        user_info["sub"],
        user_info["email"],
        user_info.get("name", ""),
    )
    return _finish_oauth_login(user)


@router.get("/facebook")
async def facebook_login(request: Request):
    if not settings.facebook_client_id or not settings.facebook_client_secret:
        raise HTTPException(status_code=503, detail="Facebook login is not configured")
    return await oauth.facebook.authorize_redirect(
        request, _oauth_redirect_uri("facebook")
    )


@router.get("/facebook/callback", name="facebook_callback")
async def facebook_callback(request: Request, db: db_dependency):
    try:
        token = await oauth.facebook.authorize_access_token(request)
        response = await oauth.facebook.get("me?fields=id,name,email", token=token)
        user_info = response.json()
    except OAuthError:
        return _oauth_error_redirect()

    if not user_info.get("id"):
        return _oauth_error_redirect()

    user = _get_or_create_social_user(
        db,
        FacebookAuth,
        str(user_info["id"]),
        user_info.get("email"),
        user_info.get("name", ""),
    )
    return _finish_oauth_login(user)


@router.post("/oauth/exchange", response_model=TokenResponse)
def exchange_oauth_code(data: OAuthCodeExchange, db: db_dependency):
    user_id = redis.getdel(f"oauth_login_code:{data.code}")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth login code is invalid or expired",
        )

    user = db.query(Users).filter(Users.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is unavailable"
        )

    return {
        "access_token": create_access_token(user.username, user.id, user.role),
        "token_type": "bearer",
    }