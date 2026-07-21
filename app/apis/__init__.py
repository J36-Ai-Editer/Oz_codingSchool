from app.apis.admin_users import router as admin_users_router
from app.apis.patients import router as patients_router
from app.apis.users import router as users_router

__all__ = [
    "admin_users_router",
    "patients_router",
    "users_router",
]
