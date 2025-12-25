from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.db.models.models import DoctorWorkingDay
from src.db.models.schemas import DoctorWorkingDayCreate


class DoctorWorkingDayCrud:

    @staticmethod
    async def create(db: AsyncSession, data: DoctorWorkingDayCreate):
        working_day = DoctorWorkingDay(
            doctor_id=data.doctor_id,
            weekday=data.weekday,
            start_time=data.start_time,
            end_time=data.end_time
        )
        db.add(working_day)
        await db.commit()
        await db.refresh(working_day)
        return working_day

    @staticmethod
    async def get_by_doctor(db: AsyncSession, doctor_id: int):
        result = await db.execute(
            select(DoctorWorkingDay).where(DoctorWorkingDay.doctor_id == doctor_id)
        )
        return result.scalars().all()
