from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from fastapi.background import BackgroundTasks
from src.db.config import engine, Base
from ..db.models.models import Doctor, Call
from ..db.crud.doctorsCrud import DoctorCrud
from fastapi import APIRouter, Depends, HTTPException, status as http_status
from ..db.config import get_db



router = APIRouter(prefix="/call", tags=["call"])