"""개발용 시드 데이터.

`docker compose up` 시 entrypoint 에서 자동 실행된다.
멱등(idempotent)하므로 여러 번 실행/재시작해도 중복 생성되지 않는다.

주의: 여기 값은 전부 **테스트용 더미 데이터**다. 운영 환경에서는 실행하지 말 것.
"""
from __future__ import annotations

import asyncio
import os

from sqlalchemy import select

from app.core.db.databases import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import Department, Gender, Role
from app.models.patient import Patient
from app.models.user import User

# --- 시드 정의 (테스트용) ---------------------------------------------------
# 공개 배포 시에는 SEED_ADMIN_EMAIL / SEED_ADMIN_PASSWORD 환경변수로
# 강한 자격증명을 지정할 수 있다 (미지정 시 로컬 테스트용 기본값).
ADMIN = {
    "email": os.getenv("SEED_ADMIN_EMAIL", "admin@example.com"),
    "password": os.getenv("SEED_ADMIN_PASSWORD", "Passw0rd!!"),
    "name": "테스트관리자",
    "phone_number": "01000000000",
    "gender": Gender.M,
    "department": Department.MEDICAL,
    "role": Role.ADMIN,
}

PATIENTS = [
    {"name": "김환자", "age": 45, "gender": Gender.M, "phone": "01011112222"},
    {"name": "이환자", "age": 32, "gender": Gender.F, "phone": "01033334444"},
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # 1) 테스트 어드민 계정 (이메일로 중복 방지)
        admin = await db.scalar(select(User).where(User.email == ADMIN["email"]))
        if admin is None:
            db.add(
                User(
                    email=ADMIN["email"],
                    hashed_password=hash_password(ADMIN["password"]),
                    name=ADMIN["name"],
                    phone_number=ADMIN["phone_number"],
                    gender=ADMIN["gender"],
                    department=ADMIN["department"],
                    role=ADMIN["role"],
                    is_active=True,
                )
            )
            await db.commit()
            print(f"[seed] admin 생성: {ADMIN['email']} / {ADMIN['password']}")
        else:
            print(f"[seed] admin 이미 존재 → 건너뜀: {ADMIN['email']}")

        # 2) 테스트 환자 2명 (전화번호로 중복 방지)
        for p in PATIENTS:
            found = await db.scalar(
                select(Patient).where(
                    Patient.phone == p["phone"],
                    Patient.is_deleted.is_(False),
                )
            )
            if found is None:
                db.add(
                    Patient(
                        name=p["name"],
                        age=p["age"],
                        gender=p["gender"],
                        phone=p["phone"],
                    )
                )
                print(f"[seed] 환자 생성: {p['name']} ({p['phone']})")
            else:
                print(f"[seed] 환자 이미 존재 → 건너뜀: {p['name']}")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
