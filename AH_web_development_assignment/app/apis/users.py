from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.dependencies import CurrentUser, DbSession
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.repositories import user_repository
from app.schemas.user import (
    MessageResponse,
    PasswordUpdateRequest,
    TokenResponse,
    UserResponse,
    UserSignupRequest,
    UserUpdateRequest,
)
from app.services import user_service


router = APIRouter(prefix="/api/v1/users", tags=["User"])
REFRESH_COOKIE_NAME = "refresh_token"


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/users",
    )


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
)
async def signup(request: UserSignupRequest, db: DbSession) -> UserResponse:
    return await user_service.signup(db, request)


@router.post("/login", response_model=TokenResponse, summary="로그인")
async def login(
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    user = await user_service.authenticate(db, form.username, form.password)
    set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/refresh", response_model=TokenResponse, summary="토큰 재발급")
async def refresh(
    response: Response,
    db: DbSession,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> TokenResponse:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
    )
    if refresh_token is None:
        raise credentials_error
    try:
        user_id = decode_token(refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise credentials_error from exc
    user = await user_repository.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise credentials_error
    set_refresh_cookie(response, create_refresh_token(user.id))
    return TokenResponse(access_token=create_access_token(user.id))


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="로그아웃",
)
async def logout(response: Response, current_user: CurrentUser) -> None:
    del current_user
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/users")


@router.get("/me", response_model=UserResponse, summary="내 정보 조회")
async def get_me(current_user: CurrentUser) -> UserResponse:
    return current_user


@router.patch("/me", response_model=UserResponse, summary="내 정보 수정")
async def update_me(
    request: UserUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> UserResponse:
    return await user_service.update_profile(db, current_user, request)


@router.patch(
    "/me/password",
    response_model=MessageResponse,
    summary="내 비밀번호 변경",
)
async def update_my_password(
    request: PasswordUpdateRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> MessageResponse:
    await user_service.update_password(db, current_user, request)
    return MessageResponse(message="비밀번호가 변경되었습니다.")


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원 탈퇴",
)
async def delete_me(
    response: Response,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    await user_service.deactivate(db, current_user)
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/v1/users")
