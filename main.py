# from fastapi import FastAPI, Request, Response
# from twilio.twiml.voice_response import VoiceResponse

# app = FastAPI()

# @app.get("/app")
# def read_root():
#     return {"message": "Hello, FastAP!"}

# @app.post("/voice")
# async def voice(request: Request):
#     form = await request.form()
    
#     call_sid = form.get("CallSid")
#     from_number = form.get("From")
#     to_number = form.get("To")
#     call_status = form.get("CallStatus")
    
#     print(f"Call SID: {call_sid}, From: {from_number}, To: {to_number}, Status: {call_status}")
    
#     response = VoiceResponse()
#     speech_text = form.get("SpeechResult")
    
#     if speech_text:
#         print(f"Caller said: {speech_text}")
#         response.say("Hi! You said: " + speech_text, voice="alice")
#         # Optional: end the call or continue
#         response.say("Thank you! Goodbye.")
#         response.hangup()
#     else:
#         gather = response.gather(
#             input="speech",
#             action="/voice",
#             timeout=5
#         )
#         gather.say("Hello! Please ask your question after the beep.", voice="alice")
    
#     return Response(content=str(response), media_type="application/xml")



from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse

app = FastAPI()
response = VoiceResponse()
# form = await request.form()
# print("Webhook hit! Form data:", dict(form))


@app.get("/")
async def read_root():
    return{"Message":"Welcome"}
  

@app.post("/voice")
async def voice(request: Request):

    response.say("Hello! This is a test.", voice="alice")
    return Response(content=str(response), media_type="application/xml")
    