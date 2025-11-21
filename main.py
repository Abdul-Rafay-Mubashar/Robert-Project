from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather

app = FastAPI()

response_first = VoiceResponse()

gather_first = Gather(
    input="speech",
    action="/appointment",
    method="POST",
    timeout=30,        
    speech_timeout="auto"
)

# ---------------------------
# 1️⃣ START CALL — ASK NAME
# ---------------------------
@app.post("/voice")
async def voice(request: Request):


    gather_first.say("Hello! Do you want to make a appintment?", voice="alice")
    response_first.append(gather_first)
    return Response(content=str(response_first), media_type="application/xml")


# ---------------------------
# 2️⃣ RECEIVE NAME — ASK AGE
# ---------------------------
@app.post("/appointment")
async def ask_age(request: Request):
    form = await request.form()
    appointment = form.get("SpeechResult")

    

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=f"/ask-date",
        method="POST",
        timeout=30
    )
    gather.say(f"Thanks for response please tell which date is sutable for you?", voice="alice")

    response.append(gather)

    return Response(content=str(response), media_type="application/xml")


# ---------------------------
# 3️⃣ RECEIVE AGE — RESPOND
# ---------------------------
@app.post("/ask-date")
async def final_response(request: Request):
    form = await request.form()
    date = form.get("SpeechResult")

    print("date:", date)

    response = VoiceResponse()
    response.say(f"Thank you for giving date. Your appointment is booked", voice="alice")
    response.say("Your data has been saved you will recive message about your appointment. Have a great day!", voice="alice")

    return Response(content=str(response), media_type="application/xml")
