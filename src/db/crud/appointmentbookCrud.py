


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, time
from src.db.models.models import Appointment, AppointmentSlot, Doctor, Call


class AppointmentBookCrud:

    @staticmethod
    async def create_appointment(db: AsyncSession, call: Call):

        doctor_id = call.doctor_id
        patient_phone = call.from_number
        slot_date = call.proposed_date
        start_time = call.llm_start_time
        end_time = call.llm_end_time
        print(doctor_id, patient_phone, slot_date, start_time, end_time)

        # ---- 1. Convert input time strings to Python time ----
        try:
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()
            end_time = datetime.strptime(end_time, "%H:%M:%S").time()
            slot_date_obj = datetime.strptime(slot_date, "%Y-%m-%d").date()
        except:
            print("here")
            return None

        # ---- 2. Find matching appointment slot ----
        stmt = select(AppointmentSlot).where(
            AppointmentSlot.doctor_id == doctor_id,
            AppointmentSlot.slot_date == slot_date_obj,
            AppointmentSlot.start_time == start_time,
            AppointmentSlot.end_time == end_time,
        )

        result = await db.execute(stmt)
        slot = result.scalar_one_or_none()

        if not slot:
            print("slot not found")
            return None

        # ---- 3. Check if already booked ----
        stmt = select(Appointment).where(
            Appointment.slot_id == slot.id,
            Appointment.status == "booked"
        )
        r = await db.execute(stmt)
        existing = r.scalar_one_or_none()

        if existing:
            print("slot booked")
            return None

        # ---- 4. Create Appointment ----
        appointment = Appointment(
            doctor_id=doctor_id,
            slot_id=slot.id,
            patient_phone=patient_phone,
            start_time = slot.start_time,
            end_time = slot.end_time,
            slot_date = slot_date_obj,
            status="booked"
        )

        db.add(appointment)
        await db.commit()
        await db.refresh(appointment)
        print("appointment create")
        return appointment
