from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fastapi.background import BackgroundTasks
from src.db.config import engine, Base
from ..db.models.models import Doctor, Call
from ..db.crud.doctorsCrud import DoctorCrud
from ..db.crud.doctordaysCrud import DoctorWorkingDayCrud
from ..db.crud.appointmentCrud import AppointmentSlotCrud

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from ..db.config import get_db
from src.db.models.schemas import (
    DoctorWorkingDayCreate,
    DoctorWorkingDayResponse
)



router = APIRouter(prefix="/doctor", tags=["Doctor"])


@router.get("/add", status_code=http_status.HTTP_201_CREATED)
async def create_doctor(db: AsyncSession = Depends(get_db)):
    try:

        db_doctor = await DoctorCrud.create_doctor(db, "Abdul Rafay", "+923334755884", "+19523337393", "1","1")

        print(f"Doctor {db_doctor}is created")
        return {
            "message": "Doctor created successfully.",
            "doctor_id": db_doctor.id
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        print(f"DoctorRouter -->create_doctor: Internal server error {str(e)}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    

@router.post("/add-working-days", response_model=DoctorWorkingDayResponse)
async def add_working_day(payload: DoctorWorkingDayCreate, db: AsyncSession = Depends(get_db)):
    working_day = await DoctorWorkingDayCrud.create(db, payload)
    return working_day


@router.get("/test")
async def add_working_day(db: AsyncSession = Depends(get_db)):
    slot_date_str = "2025-12-02"
    slot_date = datetime.strptime(slot_date_str, "%Y-%m-%d").date()
    working_day = await AppointmentSlotCrud.get_available_slots(db, 1, slot_date)
    return working_day