from pydantic import BaseModel, BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Setting(BaseSettings):
    authjwt_secret_key: str = "747a5d9ad0836d6f7b4d39afe34063bf87b4f7586d79a7b72541a4a78b88870e"


class SignUpModel(BaseModel):
    id: Optional[int]
    username: str
    password: str

    class Config:
        orm_mode = True
        schema_extra = {
            'example': {
                "username": "MM10",
                "password": "12345678",
            }
        }


class LoginModel(BaseModel):
    username: str
    password: str
