from sqlalchemy import Column, Integer, String, ForeignKey, Time, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..config import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    phone_number = Column(String(20))
    forward_number = Column(String(20))
    twilio_auth_token = Column(String(100))
    twilio_account_sid = Column(String(100))
    # forward = Column(String(20), nullable= True)


    calls = relationship("Call", back_populates="doctor")
    working_days = relationship("DoctorWorkingDay", back_populates="doctor")
    appointment_slots = relationship("AppointmentSlot", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")



class Call(Base):
    __tablename__ = "calls"

    id = Column(String(50), primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    from_number = Column(String(20))
    to_number = Column(String(20))
    stage = Column(String(50))
    appointment = Column(String(50), nullable=True)
    appointment_date =  Column(String(50), nullable=True)
    retry_count = Column(Integer, default=0)
    proposed_date = Column(String(50), nullable= True)
    date_retry = Column(Integer, default=0)
    day = Column(String(50), nullable=True)
    time_type = Column(String(50), nullable=True)
    llm_start_time = Column(String(50), nullable= True)
    llm_end_time= Column(String(50), nullable= True)
    time_retry = Column(Integer, default=0)


    doctor = relationship("Doctor", back_populates="calls")



class DoctorWorkingDay(Base):
    __tablename__ = "doctor_working_days"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    weekday = Column(String(50))
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    doctor = relationship("Doctor", back_populates="working_days")


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    slot_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # NEW FIELDS YOU REQUESTED
    is_available = Column(Boolean, default=True)      # individual slot availability
    is_day_available = Column(Boolean, default=True)  # whole day availability

    doctor = relationship("Doctor", back_populates="appointment_slots")
    appointments = relationship("Appointment", back_populates="slot")



class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id"))
    slot_id = Column(Integer, ForeignKey("appointment_slots.id"))
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_date = Column(Date, nullable=False)

    patient_phone = Column(String(20))
    status = Column(String(20), default="booked")  # booked / canceled / completed

    doctor = relationship("Doctor", back_populates="appointments")
    slot = relationship("AppointmentSlot", back_populates="appointments")