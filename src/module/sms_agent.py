from twilio.rest import Client
import os
from dotenv import load_dotenv
from src.db.config import async_session
from src.db.crud.callsCrud import CallCrud
from src.db.models.models import Doctor

load_dotenv()


class TwilioHelper:

    async def send_sms(self, call_id: str, to_number: str, doctor: Doctor, start_time, end_time, date):
        """
        Sends an SMS using Twilio.
        Automatically generates message text using all parameters including to_number.
        """
        # client = Client(doctor.twilio_account_sid, doctor.twilio_auth_token)
        #     # --- Generate SMS content ---
        # message = (
        #     f"Dear Patient ({to_number}), your appointment has been scheduled.\n"
        #     f"Doctor: Dr. {doctor.name}\n"
        #     f"📅 Date: {date}\n"
        #     f"⏰ Time: {start_time} to {end_time}\n"
        #     "Thank you for using our service!"
        # )

        try:
        #     msg = client.messages.create(
        #         body=message,
        #         from_=doctor.forward_number,
        #         to=to_number
        #     )

        #     print("SMS sent!", msg.sid)
            async with async_session() as db:
                call = await CallCrud.delete_call_by_id(db, call_id)
            print(f"Call id {call_id} is deleted")
        except Exception as e:
            retry = retry + 1
            print("SMS ERROR:", e)
            return False

