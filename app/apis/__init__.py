from app.apis.admin_users import router as admin_users_router
from app.apis.medical_records import router as medical_records_router
from app.apis.users import router as users_router

__all__ = ["admin_users_router", "medical_records_router", "users_router"]
