from fastapi import FastAPI, Request
from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from fastapi.background import BackgroundTasks
import os

app = FastAPI()

pending_results = {}

response_first = VoiceResponse()

gather_first = Gather(
    input="speech",
    action="/appointment",
    method="POST",
    timeout=30,        
    speech_timeout="auto"
)

from openai import OpenAI  # official SDK

API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=API_KEY)

def classify_text(text: str, model: str = "gpt-4-turbo"):
    """
    Classify the text as: 'irrelevant', 'Yes', or 'No'.
    Returns: {"label": "...", "raw": "..."}
    """

    prompt = (
        "You are a strict classifier. My question to the user is: "
        "\"Do you want to book an appointment?\"\n\n"
        "\"If it is question type sentence also classify it irelevent"
        "Return EXACTLY ONE WORD:\n"
        "irrelevant\n"
        "Yes\n"
        "No\n\n"
        "Rules:\n"
        "• No sentences\n"
        "• No explanation\n"
        "• No JSON\n"
        "• Only ONE of the exact words above.\n\n"
        f"User text:\n\"\"\"\n{text}\n\"\"\"\n\n"
        "Reply with only the one word."
    )

    resp = client.responses.create(
        model=model,
        input=prompt,
        temperature=0.0,
        max_output_tokens=16,
    )

    # Extract model output text
    raw_output = resp.output_text.strip()
    return raw_output

def process_llm(call_sid: str, text: str):
    result = classify_text(text)   # your function
    pending_results[call_sid] = result


# ---------------------------
# 1️⃣ START CALL — ASK NAME
# ---------------------------
@app.post("/voice")
async def voice(request: Request):

    print("Call recived ")
    gather_first.say("Hello! Do you want to make a appintment?", voice="alice")
    response_first.append(gather_first)
    return Response(content=str(response_first), media_type="application/xml")


# ---------------------------
# 2️⃣ RECEIVE NAME — ASK AGE
# ---------------------------
@app.post("/appointment")
async def appointment(request: Request, background: BackgroundTasks):
    form = await request.form()
    speech_text = form.get("SpeechResult", "")
    call_sid = form.get("CallSid")

    # --- Store text for processing ---
    pending_results[call_sid] = None

    # --- Run LLM in background ---
    background.add_task(process_llm, call_sid, speech_text)

    # --- Respond quickly to Twilio ---
    response = VoiceResponse()

    # Keep call alive (30 seconds)
    gather = Gather(
        input="speech",
        action=f"/wait-result?call_sid={call_sid}",
        timeout=10
    )
    gather.say("Please wait while we process your request.", voice="alice")
    response.append(gather)

    return Response(str(response), media_type="application/xml")



@app.post("/wait-result")
async def wait_result(request: Request):
    call_sid = request.query_params.get("call_sid")

    result = pending_results.get(call_sid)

    response = VoiceResponse()

    # LLM still processing
    if result is None:
        gather = Gather(
            input="speech",
            action=f"/wait-result?call_sid={call_sid}",
            timeout=30
        )
        gather.say("Still processing, please wait a moment.", voice="alice")
        response.append(gather)
        return Response(str(response), media_type="application/xml")

    # LLM processed — route next step
    result = result.lower()

    # YES
    if result == "yes":
        gather = Gather(
            input="speech",
            action="/ask-date",
            method="POST",
            timeout=30
        )
        gather.say("Great! Which date works for you?", voice="alice")
        response.append(gather)
        pending_results.pop(call_sid, None)
        return Response(str(response), media_type="application/xml")

    # NO
    if result == "no":
        response.say("Alright, no problem. Have a nice day!", voice="alice")
        response.hangup()
        pending_results.pop(call_sid, None)
        return Response(str(response), media_type="application/xml")

    # IRRELEVANT
    gather = Gather(
        input="speech",
        action="/appointment",
        method="POST",
        timeout=10
    )
    gather.say("I am soory i cannot assist you by any answer i only can book an appointment", voice="alice")
    response.append(gather)
    pending_results.pop(call_sid, None)
    return Response(str(response), media_type="application/xml")



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
