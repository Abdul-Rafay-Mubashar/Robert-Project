from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.db.models.models import Doctor


class DoctorCrud:
    
    async def get_doctor_by_id(db: AsyncSession, id: int):
        query = select(Doctor).where(Doctor.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_doctor(db: AsyncSession, name, phone, forword_no, sid, token):
        new_doctor = Doctor(
            name=name,
            phone_number=phone,
            forward_number=forword_no,
            twilio_auth_token=token,
            twilio_account_sid = sid
        )
        db.add(new_doctor)

        await db.commit()
        await db.refresh(new_doctor)
        return new_doctor
