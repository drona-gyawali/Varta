from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreation(BaseModel):
    email:EmailStr
    password:str

class ProfileDetails(BaseModel):
    success:int
    id:str
    email:EmailStr
    profileUrl:str
    createdAt: datetime