from pydantic import BaseModel
from typing import List

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str

class DiaryEntry(BaseModel):
    text: str

class SearchQuery(BaseModel):
    query: str