from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    DUMMY_PASSWORD_HASH,
    hash_password,
    verify_password,
)
from app.models.enums import Department, Role
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import (
    PasswordUpdateRequest,
    UserRoleUpdateRequest,
    UserSignupRequest,
    UserUpdateRequest,
)


async def _commit(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일 또는 전화번호입니다.",
        ) from exc


async def signup(db: AsyncSession, request: UserSignupRequest) -> User:
    if await user_repository.get_by_email(db, str(request.email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다.",
        )
    if await user_repository.get_by_phone_number(db, request.phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 전화번호입니다.",
        )

    user = User(
        email=str(request.email),
        hashed_password=hash_password(request.password),
        name=request.name,
        department=request.department,
        gender=request.gender,
        phone_number=request.phone_number,
        role=Role.PENDING,
        is_active=True,
    )
    await user_repository.create(db, user)
    await _commit(db)
    return user


async def authenticate(db: AsyncSession, email: str, password: str) -> User:
    user = await user_repository.get_by_email(db, email)
    if user is None:
        verify_password(password, DUMMY_PASSWORD_HASH)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용할 수 없는 계정입니다.",
        )
    return user


async def update_profile(
    db: AsyncSession,
    user: User,
    request: UserUpdateRequest,
) -> User:
    updates = request.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목을 하나 이상 입력해주세요.",
        )
    phone_number = updates.get("phone_number")
    if phone_number is not None:
        owner = await user_repository.get_by_phone_number(db, phone_number)
        if owner is not None and owner.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 전화번호입니다.",
            )
    for field, value in updates.items():
        setattr(user, field, value)
    await user_repository.save(db, user)
    await _commit(db)
    return user


async def update_password(
    db: AsyncSession,
    user: User,
    request: PasswordUpdateRequest,
) -> None:
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다.",
        )
    if verify_password(request.new_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호는 현재 비밀번호와 달라야 합니다.",
        )
    user.hashed_password = hash_password(request.new_password)
    await user_repository.save(db, user)
    await _commit(db)


async def deactivate(db: AsyncSession, user: User) -> None:
    user.is_active = False
    await user_repository.save(db, user)
    await _commit(db)


async def list_users(
    db: AsyncSession,
    *,
    query: str | None,
    department: Department | None,
) -> list[User]:
    return await user_repository.list_users(
        db,
        query=query,
        department=department,
    )


async def update_role(
    db: AsyncSession,
    admin: User,
    request: UserRoleUpdateRequest,
) -> User:
    if request.user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 권한은 변경할 수 없습니다.",
        )
    user = await user_repository.get_by_id(db, request.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )
    user.role = request.new_role
    await user_repository.save(db, user)
    await _commit(db)
    return user
