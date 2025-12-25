import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from openai import OpenAI, OpenAIError
from src.db.config import get_db
from fastapi import Depends
import json
from src.db.crud.callsCrud import CallCrud
from src.db.config import async_session

class OpenAIHelper:
    def __init__(self, api_key: str, reference_date: str = "2025-11-23"):
        self.client = OpenAI(api_key=api_key)
        self.reference_date = reference_date
        self.reference_day = datetime.strptime(reference_date, "%Y-%m-%d").strftime("%A")

    async def extract_date_from_sentence(self, sentence: str, call_id: str):
        prompt = f"""
            You are an assistant that extracts exact dates and weekdays from a given sentence. 
            Assume today is {self.reference_date} ({self.reference_day}).

            Instructions:
            1. Look for any day, date, or relative time in the sentence (e.g., tomorrow, next Friday, the day after next, 11 November, 1/12/2025).
            2. Convert it into an exact date (YYYY-MM-DD) and day of the week.
            3. Output in JSON format as:
            {{ "date": "YYYY-MM-DD", "day": "DayName", "raw": "text snippet mentioning the date" }}
            4. If no date or day is mentioned or date before today is given, return: {{ "date": "Irrelevant", "day": "Irrelevant", "raw": "Irrelevant" }}

            Sentence: "{sentence}"
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            output = response.choices[0].message.content.strip()
            date = json.loads(output)
            print(f"Date is {date}")
            async with async_session() as db:
                await CallCrud.update_date_text(db, call_id, date['date'], date['day'])

        except json.JSONDecodeError:
            date = {"date": "error", "day": "error", "raw": "Invalid JSON from API response"}
            async with async_session() as db:
                await CallCrud.update_date_text(db, call_id, date['date'], date['day'])

        except OpenAIError as e:
            date = {"date": "error", "day": "error", "raw": f"OpenAI error: {str(e)}"}
            async with async_session() as db:
                await CallCrud.update_date_text(db, call_id, date['date'], date['day'])

        except Exception as e:
            date =  {"date": "error", "day": "error", "raw": f"Unexpected error: {str(e)}"}
            async with async_session() as db:
                await CallCrud.update_date_text(db, call_id, date['date'], date['day'])


    async def classify_text(self, call_id: str, text: str, model: str = "gpt-4-turbo"):
        prompt = (
            "You are a strict classifier. My question to the user is: "
            "\"Do you want to book an appointment?\"\n\n"
            "If it is a question-type sentence, classify it as irrelevant.\n"
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
        try:
            resp = self.client.responses.create(
                model=model,
                input=prompt,
                temperature=0.0,
                max_output_tokens=16
            )
            response =  resp.output_text.strip()
            print(f"response i recive from you is {response}")
            async with async_session() as db:
                await CallCrud.update_appointment_text(db, call_id, response)

        except OpenAIError as e:
            async with async_session() as db:
                await CallCrud.update_appointment_text(db, call_id, "error")
            return f"OpenAI error: {str(e)}"
        
        except Exception as e:
            async with async_session() as db:
                await CallCrud.update_appointment_text(db, call_id, "error")
            return f"Unexpected error: {str(e)}"


    async def extract_time_or_date_from_sentence(self, sentence: str, slots: list, call_id: str):



        prompt = f"""
            You are an assistant that reads user speech and determines if they are mentioning:
            1. A time slot from the given list.
            2. A new date.
            3. Or irrelevant.

            TODAY is {self.reference_date} ({self.reference_day}).

            AVAILABLE SLOTS:
            {slots}

            RULES:
            - If user mentions a time (e.g., "4 pm", "16:30", "4:15 to 4:30"), match it with closest slot.start_time and slot.end_time.
            - If user mentions a new date (tomorrow, next Friday, 11 December), convert into YYYY-MM-DD.
            - If both date and time are present → return both.
            - If nothing useful → return type = "irrelevant".

            OUTPUT STRICT JSON FORMAT ONLY:

            {{
                "type": "time" | "date" | "irrelevant",
                "start_time": "HH:MM:SS" | null,
                "end_time": "HH:MM:SS" | null,
                "date": "YYYY-MM-DD" | null,
                "raw": "text snippet"
            }}

            Sentence: "{sentence}"
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            output = response.choices[0].message.content.strip()
            result = json.loads(output)

            print("Parsed result:", result)
            async with async_session() as db:
                await CallCrud.update_time_text(db, call_id, result['type'], result['start_time'], result['end_time'])

            return result

        except json.JSONDecodeError:
            result = {"type": "error", "raw": "Invalid JSON returned by OpenAI"}
            async with async_session() as db:

                await CallCrud.update_time_text(db, call_id, result['type'])

        except OpenAIError as e:
            result = {"type": "error", "raw": f"OpenAI error: {str(e)}"}
            async with async_session() as db:
                await CallCrud.update_time_text(db, call_id, result['type'])

        except Exception as e:
            result = {"type": "error", "raw": f"Unexpected error: {str(e)}"}
            async with async_session() as db:
                await CallCrud.update_time_text(db, call_id, result['type'])
