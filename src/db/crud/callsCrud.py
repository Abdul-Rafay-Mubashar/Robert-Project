from datetime import datetime
from sqlalchemy import select, delete
from src.db.models.models import Call
from sqlalchemy.ext.asyncio import AsyncSession


class CallCrud:

    async def create_call(db: AsyncSession, id: str, from_number: str, to_number: str, stage: str, retry_count: int = 0):
        db_call = Call(
            id = id,
            doctor_id=1,
            from_number=from_number,
            to_number=to_number,
            stage=stage,
            retry_count=retry_count
        )
        
        db.add(db_call)
        await db.commit()
        await db.refresh(db_call)
        return db_call
    

    async def update_appointment_text(
        db: AsyncSession,
        call_id: str,
        appointment_text: str
    ):
        print(f"call id is this: {call_id}")
        result = await db.execute(
            select(Call).where(Call.id == call_id)
        )
        print("call is found")

        db_call = result.scalar_one_or_none()
        print("call is found")
        if not db_call:
            print("no call present with such id")
            return None
        
        db_call.appointment = appointment_text
        await db.commit()
        await db.refresh(db_call)
        print("call is updated")
        return db_call
    

    async def update_date_text(
        db: AsyncSession,
        call_id: str,
        date_text: str,
        day: str,
    ):
        print(f"call id is this: {call_id}")
        result = await db.execute(
            select(Call).where(Call.id == call_id)
        )
        print("date is found")

        db_call = result.scalar_one_or_none()
        print("date is found")
        if not db_call:
            print("no call present with such id")
            return None
        
        db_call.proposed_date = date_text
        db_call.day = day
        await db.commit()
        await db.refresh(db_call)
        print("date is updated")
        return db_call


    async def get_call_by_id(
        db: AsyncSession,
        call_id: str,
    ):
        result = await db.execute(
            select(Call).where(Call.id == call_id)
        )
        db_call = result.scalar_one_or_none()
        
        return db_call
    
    async def update_call_appintment_retry(
        db: AsyncSession,
        call_id: str,
    ):
        result = await db.execute(
            select(Call).where(Call.id == call_id)
        )
        db_call = result.scalar_one_or_none()
        if not db_call:
            return None
        retry = db_call.retry_count
        db_call.retry_count = retry + 1
        await db.commit()
        await db.refresh(db_call)
        return db_call
    
    async def update_date_appintment_retry(
        db: AsyncSession,
        call_id: str,
    ):
        result = await db.execute(
            select(Call).where(Call.id == call_id)
        )
        db_call = result.scalar_one_or_none()
        if not db_call:
            return None
        retry = db_call.date_retry
        db_call.date_retry = retry + 1
        await db.commit()
        await db.refresh(db_call)
        return db_call
    
    async def update_time_text(
        db: AsyncSession,
        call_id: str,
        response_type: str,
        start_time = None,
        end_time = None
    ):
        result = await db.execute(
            select(Call).where(Call.id == call_id)
        )
        db_call = result.scalar_one_or_none()
        if not db_call:
            return None
        db_call.llm_start_time = start_time
        db_call.llm_end_time = end_time
        db_call.time_type = response_type
        await db.commit()
        await db.refresh(db_call)
        return db_call
    
    async def update_time_retry(
        db: AsyncSession,
        call_id: str,
    ):
        result = await db.execute(
            select(Call).where(Call.id == call_id)
        )
        db_call = result.scalar_one_or_none()
        if not db_call:
            return None
        retry = db_call.time_retry
        db_call.time_retry = retry + 1
        await db.commit()
        await db.refresh(db_call)
        return db_call
    
    async def delete_call_by_id(db: AsyncSession, call_id: str):

        stmt = delete(Call).where(Call.id == call_id)
        result = await db.execute(stmt)
        await db.commit()
        return True