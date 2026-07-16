from typing import Annotated

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentAdmin, DbSession
from app.schemas.user import UserListQuery, UserResponse, UserRoleUpdateRequest
from app.services import user_service


router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin User"])


@router.get("", response_model=list[UserResponse], summary="전체 사용자 목록 조회")
async def get_users(
    admin: CurrentAdmin,
    db: DbSession,
    filters: Annotated[UserListQuery, Query()],
) -> list[UserResponse]:
    del admin
    return await user_service.list_users(
        db,
        query=filters.query,
        department=filters.department,
    )


@router.patch("/role", response_model=UserResponse, summary="사용자 권한 수정")
async def update_user_role(
    request: UserRoleUpdateRequest,
    admin: CurrentAdmin,
    db: DbSession,
) -> UserResponse:
    return await user_service.update_role(db, admin, request)
