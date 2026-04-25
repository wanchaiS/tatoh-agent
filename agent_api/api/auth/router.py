from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.auth.schemas import LoginRequest, UserInfo
from api.auth.service import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_credentials,
)
from api.dependencies import require_auth
from api.schemas import OkResponse
from core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

_ACCESS_COOKIE = "session"
_REFRESH_COOKIE = "refresh_token"


def _set_access_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_ACCESS_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        path="/",
        max_age=settings.jwt_expire_minutes * 60,
    )


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        samesite="strict",
        secure=settings.cookie_secure,
        path="/",
        max_age=30 * 24 * 60 * 60,
    )


@router.post("/login")
async def login(body: LoginRequest, response: Response) -> UserInfo:
    if not verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    username = body.username.lower()
    _set_access_cookie(response, create_access_token(username))
    _set_refresh_cookie(response, create_refresh_token(username))
    return UserInfo(username=username)


@router.post("/logout", response_model=OkResponse)
async def logout(response: Response) -> OkResponse:
    response.delete_cookie(key=_ACCESS_COOKIE, path="/")
    response.delete_cookie(key=_REFRESH_COOKIE, path="/")
    response.delete_cookie(key=_REFRESH_COOKIE, path="/api/auth")  # clear legacy path
    return OkResponse()


@router.post("/refresh-token")
async def refresh_token(request: Request, response: Response) -> UserInfo:
    token = request.cookies.get(_REFRESH_COOKIE)
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token cookie")
    username = decode_token(token, expected_type="refresh")
    if not username:
        raise HTTPException(status_code=401, detail="Refresh token expired or invalid")
    _set_access_cookie(response, create_access_token(username))
    return UserInfo(username=username)


@router.get("/me")
async def me(username: str = Depends(require_auth)) -> UserInfo:
    return UserInfo(username=username)
