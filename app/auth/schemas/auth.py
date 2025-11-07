from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreation(BaseModel):
    email: EmailStr
    password: str


class ProfileDetails(BaseModel):
    id: str
    email: EmailStr
    profileUrl: str
    createdAt: datetime


class UpdateProfileurl(BaseModel):
    profileUrl: str
