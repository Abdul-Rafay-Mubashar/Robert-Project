from datetime import datetime, timedelta, time
from sqlalchemy import select
from src.db.models.models import AppointmentSlot, Appointment, DoctorWorkingDay
from sqlalchemy.ext.asyncio import AsyncSession

class AppointmentSlotCrud:

    @staticmethod
    async def get_available_slots(db: AsyncSession, doctor_id: int, slot_date):

        # 1. Fetch existing slots
        stmt = (
            select(AppointmentSlot)
            .outerjoin(Appointment, Appointment.slot_id == AppointmentSlot.id)
            .where(
                AppointmentSlot.doctor_id == doctor_id,
                AppointmentSlot.slot_date == slot_date,
                AppointmentSlot.is_day_available == True,
                Appointment.id == None
            )
            .order_by(AppointmentSlot.start_time)
        )

        result = await db.execute(stmt)
        slots = result.scalars().all()

        # 2. If slots already exist → return
        if slots:
            if slots[0].is_day_available == False:
                print("Doctor is not available in that day due to some reason")
                return None
            return slots

        # 3. No slots → auto-generate based on weekday template
        weekday_name = slot_date.strftime("%A")  # "Monday", "Tuesday"

        stmt = select(DoctorWorkingDay).where(
            DoctorWorkingDay.doctor_id == doctor_id,
            DoctorWorkingDay.weekday == weekday_name
        )
        res = await db.execute(stmt)
        working_day = res.scalar_one_or_none()

        if not working_day:
            print("Not working day")
            return []  

        # 4. Generate 15-min slots
        start = datetime.combine(slot_date, working_day.start_time)
        end = datetime.combine(slot_date, working_day.end_time)

        created_slots = []

        while start < end:
            new_slot = AppointmentSlot(
                doctor_id=doctor_id,
                slot_date=slot_date,
                start_time=start.time(),
                end_time=(start + timedelta(minutes=15)).time(),
                is_day_available=True
            )
            db.add(new_slot)
            created_slots.append(new_slot)

            start += timedelta(minutes=15)

        await db.commit()
        await db.refresh(created_slots[0])
        print("Slots Made")
        return created_slots
