from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.security import decode_token
from app.models.enums import Department, Role
from app.models.user import User
from app.repositories import user_repository


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")
DbSession = Annotated[AsyncSession, Depends(async_get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보가 유효하지 않습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_token(token, expected_type="access")
    except ValueError as exc:
        raise credentials_error from exc

    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise credentials_error
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용할 수 없는 계정입니다.",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(current_user: CurrentUser) -> User:
    # 토큰 검증·활성 계정 확인(401)은 get_current_user 단계에서 이미 끝났다.
    # 여기서는 "관리자냐"만 판단한다 → 인증은 됐지만 권한이 부족하면 403.
    if current_user.role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,  # 인증 O, 권한 X → Forbidden
            detail="관리자 권한이 필요합니다.",
        )
    return current_user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]


async def get_current_approved_user(current_user: CurrentUser) -> User:
    if current_user.role not in {Role.STAFF, Role.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다.",
        )
    return current_user


CurrentApprovedUser = Annotated[User, Depends(get_current_approved_user)]


async def get_current_medical_staff(
    current_user: CurrentApprovedUser,
) -> User:
    is_admin = current_user.role == Role.ADMIN
    is_medical_staff = (
        current_user.department == Department.MEDICAL
        and current_user.role in {Role.STAFF, Role.ADMIN}
    )
    if not is_admin and not is_medical_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다.",
        )
    return current_user


CurrentMedicalStaff = Annotated[User, Depends(get_current_medical_staff)]
