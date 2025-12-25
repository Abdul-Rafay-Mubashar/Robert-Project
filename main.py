from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from fastapi.background import BackgroundTasks
from src.db.config import engine, Base
from src.db.models.models import Doctor, Call
from src.db.crud.doctorsCrud import DoctorCrud
from src.db.crud.callsCrud import CallCrud
from src.db.crud.appointmentCrud import AppointmentSlotCrud
from src.db.crud.appointmentbookCrud import AppointmentBookCrud


from fastapi import APIRouter, Depends, HTTPException, status as http_status
from urllib.parse import quote, unquote

from datetime import datetime
from src.routers import calls, doctors
from src.db.config import get_db
from src.module import openai_api, twilio_agent



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)


app.include_router(calls.router, prefix="/api")
app.include_router(doctors.router, prefix="/api")



@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)




pending_results = []


from fastapi import Request, Depends
from fastapi.responses import Response
from urllib.parse import quote
from twilio.twiml.voice_response import VoiceResponse
from sqlalchemy.ext.asyncio import AsyncSession

@app.post("/voice/{id}")
async def voice(id: int, request: Request, db: AsyncSession = Depends(get_db)):
    try:

        form = await request.form()
        call_sid = form.get("CallSid")
        from_number = form.get("From")
        to_number = form.get("To")
        print(call_sid, from_number, to_number, id)

        doctor = await DoctorCrud.get_doctor_by_id(db, id)
        print(doctor.id, doctor.name)

        if not doctor:
            response = VoiceResponse()
            response.say("Sorry, your doctor is not in our records.", voice="alice")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        if doctor.forward_number != to_number:
            response = VoiceResponse()
            response.say("Sorry, your doctor is using someone's credentials.", voice="alice")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")


        call = await CallCrud.create_call(
            db, call_sid, from_number, to_number, "APPOINTMENT", 0
        )

        response = VoiceResponse()
        response.say(
            "Hello, connecting you to Doctor. Please wait.",
            voice="alice"
        )

        encoded_name = quote(doctor.name)
        response.redirect(f"/appointment/{encoded_name}")

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        print("ERROR IN /voice:", e)

        response = VoiceResponse()
        response.say("Sorry, something went wrong on our server.", voice="alice")
        response.hangup()

        return Response(content=str(response), media_type="application/xml")

    


@app.post("/appointment/{name}")
async def appointments(
    name: str,
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    try:
        form = await request.form()
        call_sid = form.get("CallSid")
        doctor_name = unquote(name)
        print(doctor_name)
        call = await CallCrud.get_call_by_id(db, call_sid)
        if call.retry_count < 3:
            await CallCrud.update_call_appintment_retry(db, call_sid)
            response = VoiceResponse()
            gather = Gather(
                input="speech dtmf",    
                timeout=5,               
                action=f"/wait-result?call_sid={call_sid}",
                method="POST"
            )
            gather.say(f"Hello, I am the assistant of Dr {doctor_name}. Would you like to book an appointment?", voice="alice")
            response.append(gather)
            response.say("We did not receive any input. Please call again.", voice="alice")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
        
        response = VoiceResponse()
        response.say("Sorry you had try alot of time good bye", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    
    except Exception as e:
        print("ERROR IN /appointment:", e)
        response = VoiceResponse()
        response.say("Sorry, something went wrong on our server.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")


@app.post("/wait-result")
async def wait_result(
    request: Request,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    call_sid: str = Query(None),
):
    try:
        form = await request.form()
        speech = form.get("SpeechResult")

        response = VoiceResponse()
        
        if speech:
            background.add_task(openai_api.classify_text, call_sid, speech)

            response.say("Thanks, processing your request. please wait", voice="alice")
            response.pause(length=5)
            response.redirect(f"/check-response?call_sid={call_sid}")
            return Response(str(response), media_type="application/xml")
    
    except Exception as e:
        print("ERROR IN /wait_result:", e)
        response = VoiceResponse()
        response.say("Sorry, something went wrong on our server.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")



@app.post("/check-response")
async def check_response(call_sid: str = Query(...), db: AsyncSession = Depends(get_db),):
    try:
        call = await CallCrud.get_call_by_id(db, call_sid)
        print("Call come")
        llm_response = call.appointment
        print(llm_response)
        if not llm_response:
            print("not response")
            response = VoiceResponse()
            response.say("Still processing your request please wait a bit more", voice="alice")
            response.pause(length=7)
            response.redirect(f"/check-response?call_sid={call_sid}")
            return Response(str(response), media_type="application/xml")


        elif llm_response.lower() == "yes":
            print("yes response")
            response = VoiceResponse()

            gather = Gather(
                input="speech dtmf",          
                timeout=5,                  
                action=f"/ask-date?call_sid={call_sid}",
            )
            gather.say("Ok good! Now kindly tell me which day is good for you?", voice="alice")
            response.append(gather)
            response.say("We did not receive any input. Please try again.", voice="alice")
            return Response(str(response), media_type="application/xml")
        
        elif llm_response.lower() == "no":
            print("no response")
            response = VoiceResponse()
            response.say("ok thanks for you response, Have a nice day bye", voice="alice")
            response.hangup()
            return Response(str(response), media_type="application/xml")
        
        elif llm_response.lower() == "irrelevant":
            print("irrelevent")
            doctor = await DoctorCrud.get_doctor_by_id(db, call.doctor_id)
            encoded_name = quote(doctor.name)
            response = VoiceResponse()
            response.say("I am sorry i can not assist you with any query i a only here to book apointment", voice="alice")
            response.redirect(f"/appointment/{encoded_name}")
            return Response(str(response), media_type="application/xml")

        elif llm_response.lower() == "error":
            print("error")
            response = VoiceResponse()
            response.say("Sorry unexpected error in our AI", voice="alice")
            response.hangup()
            return Response(str(response), media_type="application/xml")
    
    except Exception as e:
        print("ERROR IN /check_response:", e)
        response = VoiceResponse()
        response.say("Sorry, something went wrong on our server.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    



@app.post("/ask-date")
async def ask_date(
        request: Request,
        background: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        call_sid: str = Query(None)
    ):

    form = await request.form()
    speech = form.get("SpeechResult")
    if speech:
        background.add_task(openai_api.extract_date_from_sentence, speech, call_sid)
    response = VoiceResponse()
    response.say(f"Thank you for giving date. please wait we are processing your request", voice="alice")
    response.pause(length=8)
    response.redirect(f"/confirm-date?call_sid={call_sid}")

    return Response(content=str(response), media_type="application/xml")



@app.post("/confirm-date")
async def confirm_date(call_sid: str = Query(...), db: AsyncSession = Depends(get_db),):
    try:
        call = await CallCrud.get_call_by_id(db, call_sid)
        llm_response = call.proposed_date
        
        print(llm_response)
        if not llm_response:
            print("not response")
            response = VoiceResponse()
            response.say("Still processing your request please wait a bit more", voice="alice")
            response.pause(length=7)
            response.redirect(f"/confirm-date?call_sid={call_sid}")
            return Response(str(response), media_type="application/xml")

        elif llm_response.lower() == "irrelevant":
            if call.date_retry < 2:
                await CallCrud.update_date_appintment_retry(db, call_sid)
                print("irrelevent")
                response = VoiceResponse()
                response.say("I am sorry i can not assist you with any query", voice="alice")
                response.redirect(f"/check-response?call_sid={call_sid}")
                return Response(str(response), media_type="application/xml")
            
            response = VoiceResponse()
            response.say("Sorry you had try alot of time good bye", voice="alice")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        elif llm_response.lower() == "error":
            print("error")
            response = VoiceResponse()
            response.say("Sorry unexpected error in our AI", voice="alice")
            response.hangup()
            return Response(str(response), media_type="application/xml")
        
        else:
            doctor = await DoctorCrud.get_doctor_by_id(db, call.doctor_id)
            print(call.proposed_date, call.day)
            slot_date = datetime.strptime(call.proposed_date, "%Y-%m-%d").date()

            slots = await AppointmentSlotCrud.get_available_slots(db, doctor.id, slot_date)

            if slots == None:
                response = VoiceResponse()
                response.say("Doctor is on leave on that day", voice="alice")
                response.hangup()
                return Response(str(response), media_type="application/xml")
            
            if len(slots)  == 0:
                response = VoiceResponse()
                response.say("No available slots for that day", voice="alice")
                response.hangup()
                return Response(str(response), media_type="application/xml")
            response = VoiceResponse()
            response.say("Available times for appointent are", voice="alice")
            count = 0
            for slot in slots:
                response.say(f"{slot.start_time} to {slot.end_time}", voice="alice")
                count = count + 1
                if count == 5:
                    break

            gather = Gather(
                input="speech dtmf",    
                timeout=5,               
                action=f"/wait-time?call_sid={call_sid}",
                method="POST"
            )
            gather.say(f"Which Time would you like to choose amoung them?", voice="alice")
            response.append(gather)
            response.say("We did not receive any input. Please call again.", voice="alice")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
                
    
    except Exception as e:
        print("ERROR IN /check_response:", e)
        response = VoiceResponse()
        response.say("Sorry, something went wrong on our server.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")
    


@app.post("/wait-time")
async def wait_time(       
        request: Request,
        background: BackgroundTasks,
        db: AsyncSession = Depends(get_db),
        call_sid: str = Query(None)
    ):

    form = await request.form()
    speech = form.get("SpeechResult")
    call = await CallCrud.get_call_by_id(db, call_sid)
    doctor = await DoctorCrud.get_doctor_by_id(db, call.doctor_id)
    slot_date = datetime.strptime(call.proposed_date, "%Y-%m-%d").date()
    slots = await AppointmentSlotCrud.get_available_slots(db, doctor.id, slot_date)
    available_slots = slots
    if len(slots) < 5:
        available_slots = slots[:5]
    
    if speech:
        background.add_task(openai_api.extract_time_or_date_from_sentence, speech, available_slots ,call_sid)
    response = VoiceResponse()
    response.say(f"Thank you for giving time. please wait we are processing your request", voice="alice")
    response.pause(length=8)
    response.redirect(f"/confirm-time?call_sid={call_sid}")

    return Response(content=str(response), media_type="application/xml")


@app.post("/confirm-time")
async def confirm_time( background: BackgroundTasks, call_sid: str = Query(...), db: AsyncSession = Depends(get_db)):
    try:
        call = await CallCrud.get_call_by_id(db, call_sid)
        llm_response = call.time_type
        
        print(llm_response)
        if not llm_response:
            print("not response")
            response = VoiceResponse()
            response.say("Still processing your request please wait a bit more", voice="alice")
            response.pause(length=7)
            response.redirect(f"/confirm-time?call_sid={call_sid}")
            return Response(str(response), media_type="application/xml")

        elif llm_response.lower() == "irrelevant":
            if call.time_retry < 2:
                await CallCrud.update_time_retry(db, call_sid)
                print("irrelevent")
                response = VoiceResponse()
                response.say("I am sorry i can not assist you with any query", voice="alice")
                response.redirect(f"/confirm-date?call_sid={call_sid}")
                return Response(str(response), media_type="application/xml")
            
            response = VoiceResponse()
            response.say("Sorry you had try alot of time good bye", voice="alice")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

        elif llm_response.lower() == "error":
            print("error")
            response = VoiceResponse()
            response.say("Sorry unexpected error in our AI", voice="alice")
            response.hangup()
            return Response(str(response), media_type="application/xml")
        
        elif llm_response.lower() == "time":
            doctor = await DoctorCrud.get_doctor_by_id(db, call.doctor_id)
            appointment = await AppointmentBookCrud.create_appointment(db, call)   
            response = VoiceResponse()

            if appointment:
                background.add_task(twilio_agent.send_sms, call.id, call.from_number, doctor, appointment.start_time, appointment.end_time, appointment.slot_date)
                response.say(f"Your appointment is book with Dr {doctor.name} from {appointment.start_time} to {appointment.end_time}", voice="alice")
                count = 0
                while count < 3:
                    response.say(f"please note Your appointment number is {appointment.id}")
                    response.pause(length=1)
                    count = count + 1
                
                response.say(f"Have a nice day, good bye")
                response.hangup()
                return Response(content=str(response), media_type="application/xml")
            response.say("Sorry facing problem while processing appointment", voice="alice")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")
                
    
    except Exception as e:
        print("ERROR IN /check_response:", e)
        response = VoiceResponse()
        response.say("Sorry, something went wrong on our server.", voice="alice")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")