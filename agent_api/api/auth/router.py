from fastapi import APIRouter, Depends, HTTPException, Request, Response

from api.auth.schemas import LoginRequest, UserInfo
from api.auth.service import create_token, decode_token, verify_credentials
from api.dependencies import require_auth
from api.schemas import OkResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

_COOKIE_NAME = "session"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="strict",
        secure=True,
        path="/",
    )


@router.post("/login")
async def login(body: LoginRequest, response: Response) -> UserInfo:
    if not verify_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(body.username.lower())
    _set_session_cookie(response, token)
    return UserInfo(username=body.username.lower())


@router.post("/logout", response_model=OkResponse)
async def logout(response: Response) -> OkResponse:
    response.delete_cookie(key=_COOKIE_NAME, path="/")
    return OkResponse()


@router.post("/refresh-token")
async def refresh_token(request: Request, response: Response) -> UserInfo:
    token = request.cookies.get(_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=401, detail="No session cookie")
    username = decode_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Session expired")
    new_token = create_token(username)
    _set_session_cookie(response, new_token)
    return UserInfo(username=username)


@router.get("/me")
async def me(username: str = Depends(require_auth)) -> UserInfo:
    return UserInfo(username=username)
