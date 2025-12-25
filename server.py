import asyncio, os
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from openai import OpenAI, OpenAIError
from src.db.config import get_db
from fastapi import Depends
import json
from src.db.crud.callsCrud import CallCrud
from src.db.config import async_session
from src.db.config import Base


class OpenAIHelper:
    def __init__(self, api_key: str, reference_date: str = "2025-11-23"):
        self.client = OpenAI(api_key=api_key)
        self.reference_date = reference_date
        self.reference_day = datetime.strptime(reference_date, "%Y-%m-%d").strftime("%A")

    async def extract_date_from_sentence(self, sentence: str):
        prompt = f"""
            You are an assistant that extracts exact dates and weekdays from a given sentence. 
            Assume today is {self.reference_date} ({self.reference_day}).

            Instructions:
            1. Look for any day, date, or relative time in the sentence (e.g., tomorrow, next Friday, the day after next, 11 November, 1/12/2025).
            2. Convert it into an exact date (YYYY-MM-DD) and day of the week.
            3. Output in JSON format as:
            {{ "date": "YYYY-MM-DD", "day": "DayName", "raw": "text snippet mentioning the date" }}
            4. If no date or day is mentioned, or date before today is mentioned return: {{ "date": "Irrelevant", "day": "Irrelevant", "raw": "Irrelevant" }}

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

        except json.JSONDecodeError:
            return {"date": "Error", "day": "Error", "raw": "Invalid JSON from API response"}
        except OpenAIError as e:
            return {"date": "Error", "day": "Error", "raw": f"OpenAI error: {str(e)}"}
        except Exception as e:
            return {"date": "Error", "day": "Error", "raw": f"Unexpected error: {str(e)}"}

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
            return f"OpenAI error: {str(e)}"
        
        except Exception as e:
            await CallCrud.update_appointment_text(db, call_id, "error")
            return f"Unexpected error: {str(e)}"


    async def extract_time_or_date_from_sentence(self, sentence: str, slots: list):


        # Convert slot list to JSON string for prompt
        slots_json = json.dumps(slots, indent=2)

        prompt = f"""
            You are an assistant that reads user speech and determines if they are mentioning:
            1. A time slot from the given list.
            2. A new date.
            3. Or irrelevant.

            TODAY is {self.reference_date} ({self.reference_day}).

            AVAILABLE SLOTS:
            {slots_json}

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


            return result

        except json.JSONDecodeError:
            return {"type": "error", "raw": "Invalid JSON returned by OpenAI"}
        
        except OpenAIError as e:
            return {"type": "error", "raw": f"OpenAI error: {str(e)}"}

        except Exception as e:
            return {"type": "error", "raw": f"Unexpected error: {str(e)}"}
        

async def main():
    openai_api = OpenAIHelper(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Example call
    sentence = "3:30 PM"
    slots =  [{
        "doctor_id": 1,
        "slot_date": "2025-12-02",
        "start_time": "15:30:00",
        "end_time": "15:45:00",
        "is_day_available": True,
        "id": 27,
        "is_available": True
    },
    {
        "doctor_id": 1,
        "slot_date": "2025-12-02",
        "start_time": "15:45:00",
        "end_time": "16:00:00",
        "is_day_available": True,
        "id": 28,
        "is_available": True
    },
    {
        "doctor_id": 1,
        "slot_date": "2025-12-02",
        "start_time": "16:00:00",
        "end_time": "16:15:00",
        "is_day_available": True,
        "id": 29,
        "is_available": True
    },
    {
        "doctor_id": 1,
        "slot_date": "2025-12-02",
        "start_time": "16:15:00",
        "end_time": "16:30:00",
        "is_day_available": True,
        "id": 30,
        "is_available": True
    },
    {
        "doctor_id": 1,
        "slot_date": "2025-12-02",
        "start_time": "16:30:00",
        "end_time": "16:45:00",
        "is_day_available": True,
        "id": 31,
        "is_available": True
    },
    {
        "doctor_id": 1,
        "slot_date": "2025-12-02",
        "start_time": "16:45:00",
        "end_time": "17:00:00",
        "is_day_available": True,
        "id": 32,
        "is_available": True
    }
]
    
    # await openai_api.extract_time_or_date_from_sentence(sentence, slots)
    # await openai_api.extract_date_from_sentence("in nextweek tuesday")
    # target_metadata = Base.metadata
    # for table_name, table in target_metadata.tables.items():
    #     print(f"\nTable: {table_name}")
    #     for col in table.columns:
    #         print(f" - {col.name} ({col.type})")

# Run the async function
asyncio.run(main())