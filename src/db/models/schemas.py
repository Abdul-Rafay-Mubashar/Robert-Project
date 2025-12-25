from pydantic import BaseModel
from datetime import time

class DoctorWorkingDayCreate(BaseModel):
    doctor_id: int
    weekday: str          # example: "Monday"
    start_time: time
    end_time: time

class DoctorWorkingDayResponse(BaseModel):
    id: int
    doctor_id: int
    weekday: str
    start_time: time
    end_time: time

    class Config:
        from_attributes = True
