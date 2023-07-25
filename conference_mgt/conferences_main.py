import inspect
import re

from fastapi import FastAPI

from database.database import Base, engine
from services.conference_routes import conference_router


Base.metadata.create_all(bind=engine)

conferences_app = FastAPI()

conferences_app.include_router(conference_router)
