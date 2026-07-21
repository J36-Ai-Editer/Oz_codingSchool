from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Gender
from app.models.patient import Patient


async def create(db: AsyncSession, patient: Patient) -> Patient:
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    return patient


async def list_patients(
    db: AsyncSession,
    *,
    name: str | None = None,
    gender: Gender | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
) -> list[Patient]:
    statement: Select[tuple[Patient]] = select(Patient).order_by(Patient.id)
    if name is not None:
        statement = statement.where(Patient.name.ilike(f"%{name}%"))
    if gender is not None:
        statement = statement.where(Patient.gender == gender)
    if min_age is not None:
        statement = statement.where(Patient.age >= min_age)
    if max_age is not None:
        statement = statement.where(Patient.age <= max_age)

    result = await db.scalars(statement)
    return list(result.all())
